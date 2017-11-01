"""
"""

from joblib import Parallel, delayed
from pprint import pprint
import os
import time
from tqdm import tqdm
import json
import argparse
import abc
import copy
import subprocess

def ssh_key_access(config, ip, command):
    """
    It is assumed that you have already installed the identity on
    the machine 'ip', so that you can use passwordless ssh.
    You make this happen using

    ```bash
    ssh-copy-id IP_OF_SOME_MACHINE
    ```
    """

    address = ip

    if 'User' in config:
        address = config['User'] + "@" + ip

    # open ssh connection
    sshProcess = subprocess.Popen(
        ('ssh -oStrictHostKeyChecking=no %s' % address),
        shell=True,
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        universal_newlines = True,
        bufsize = 0
    )

    # execute command
    sshProcess.stdin.write(command + " \n")

    # wait for command to finish
    sshProcess.communicate()

access = {
    'ssh_key_access': ssh_key_access
}

class DaskManager():

    def hw_name(self):
        return self.cluster_name + ".hardware.json"

    def dask_name(self):
        return self.cluster_name + ".dask.json"

    def __init__(self, cluster_name):
        self.cluster_name = cluster_name

        hw_config = self.hw_name()
        dask_config = self.dask_name()

        if not os.path.exists(hw_config):
            raise ValueError("File '%s' not found - it seems that the "
                             "cluster %s does not exist. Please check "
                             "that the name of corresponding .hardware.json"
                             "file is correct." % (hw_config, cluster_name))

        self.cluster_file = hw_config
        self.cluster_hardware = json.load(open(hw_config))

        self.cluster_dask = None

        if os.path.exists(dask_config):
            self.cluster_dask = json.load(open(dask_config))

    def notify(self, message):
        print(message)

    def config(self, docker_image):
        # make the json file for dask configuration
        self.notify("Start configuration of dask ...")

        dask_config_seq = []

        if isinstance(docker_image, str):
            image_speification = lambda cfg: docker_image
        else:
            image_speification = docker_image

        if not callable(image_speification):
            raise ValueError(
                'docker_image should either be a string '
                'or callable that takes hardware config as input,'
                'got %s' % image_speification
            )

        first_ip = None

        for machine_class in self.cluster_hardware:
            image = image_speification(machine_class)
            access_mode = machine_class['Means of access']
            access_config = machine_class['Access config']
            workers = machine_class['Workers']
            type = machine_class['Type']

            for ip in machine_class['IPs']:
                if first_ip is None:
                    first_ip = ip

                dask_config_seq.append(
                    {
                        'Docker image': image,
                        "Means of access": access_mode,
                        "Access config": access_config,
                        "Workers": workers,
                        "Type": type,
                        "Role": 'worker',
                        "IP": ip,
                        "Scheduler": first_ip
                    }
                )

        # set the first machine as a scheduler also
        first = copy.deepcopy(dask_config_seq[0])
        first['Role'] = 'scheduler'
        dask_config_seq = [first] + dask_config_seq

        # save configuration sequence
        config_file = self.dask_name()

        json.dump(dask_config_seq, open(config_file, 'w'), indent=2, sort_keys=True)

        self.notify("Created configuration.")

    def check_configured(self):
        dask_config = self.dask_name()

        if os.path.exists(dask_config):
            self.cluster_dask = json.load(open(dask_config))
        else:
            raise ValueError("Please configure the dask cluster first (use --config for that)")

    def run_command_on_machines(self, machines, command, n_jobs=None):
        commands = []
        for machine in machines:
            acc_mode = machine['Means of access']
            acc_config = machine['Access config']
            ip = machine['IP']
            acc_func = access[acc_mode]

            commands.append(
                (acc_func, acc_config, ip, command(machine))
            )

        if n_jobs is None:
            n_jobs = len(commands)

        # run docker pull in parallel
        Parallel(n_jobs=len(commands))(
            delayed(acc_func)(acc_config, ip, command)
            for acc_func, acc_config, ip, command in commands
        )

    def start_dask(self):
        self.check_configured()
        self.notify("Run update for docker containers ...")

        # update docker on all machines
        self.run_command_on_machines(
            self.cluster_dask, lambda m: 'docker pull ' + m['Docker image']
        )

        self.notify("Start scheduler ...")
        # first start the scheduler
        sch = [v for v in self.cluster_dask if v['Role'] == 'scheduler']

        self.run_command_on_machines(
            sch, lambda m: "docker run --net='host' -d " + m['Docker image'] + " /bin/bash -c 'export LC_ALL=C.UTF-8 && dask-scheduler'"
        )

        self.notify("Start workers ...")
        # point all workers to scheduler
        scheduler_ip = sch[0]['IP']

        # first start the scheduler
        workers = [v for v in self.cluster_dask if v['Role'] == 'worker']

        self.run_command_on_machines(
            workers, lambda m: "docker run --net='host' -d " + m['Docker image'] +
                               " /bin/bash -c 'export LC_ALL=C.UTF-8 && dask-worker " +
                               scheduler_ip + ":8786 --nprocs " + str(m['Workers']) + "'"
        )

        self.notify("Started docker cluster. Scheduler is %s:8786" % scheduler_ip)

    def remove_dask(self):
        self.check_configured()
        self.notify("Removing all containers...")

        # Destroy all containers
        self.run_command_on_machines(
            self.cluster_dask, lambda m: 'docker rm -f $(docker ps -a -q)'
        )

        self.notify("Removed the docker cluster infrastrucutre.")

    def clear_dask(self):
        self.remove_dask()
        os.remove(self.hw_name())

    def reset_dask(self):
        self.remove_dask()
        self.start_dask()

    def show_ip(self):
        self.check_configured()
        ip = self.cluster_dask[0]['IP']
        self.notify("Scheduler ip: %s" % ip)
        return ip


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--config', action='store_true', help="Creates dask configuration file.")
    parser.add_argument(
        '--start', action='store_true', help="Start the dask connections on cluster.")
    parser.add_argument(
        '--remove', action='store_true', help="Stop and remove all containers on the cluster, including dask.")
    parser.add_argument(
        '--clear', action='store_true', help="Same as --remove, except dask.json is also removed.")
    parser.add_argument(
        '--reset', action='store_true', help="Remove all containers, start dask anew.")
    parser.add_argument(
        '--mainip', action='store_true', help="Show the IP of a Dask scheduler for the cluster.")
    parser.add_argument(
        '--image', nargs="?", default=None, type=str, help="Command to execute on every node of cluster.")
    parser.add_argument(
        '--name', nargs="?", default='cluster', type=str, help="Name of the cluster instance.")

    args = parser.parse_args()

    manager = DaskManager(args.name)

    if args.config:
        manager.config(args.image)

    if args.start:
        manager.start_dask()

    if args.remove:
        manager.remove_dask()

    if args.clear:
        manager.clear_dask()

    if args.reset:
        manager.reset_dask()

    if args.mainip:
        manager.show_ip()
