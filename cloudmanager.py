"""


Create access keys at https://console.aws.amazon.com/iam , go to users -> create user, enable programmatic access

~/.aws/credentials:
```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

To figure out IamFleetRole, go to IAM -> Roles and find fleet role.
Specify the key that you want to use to access created machines for
maintenance.

IAM images should be based on Ubuntu 16.04 image.

"""

import boto3
import subprocess
from pprint import pprint
import os
import time
from tqdm import tqdm
from joblib import Parallel, delayed
import json
import argparse
import abc


class ClusterInstance:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, name):
        """
        Create an instance of named cluster
        """
        self.name = name

    @abc.abstractmethod
    def start_cluster_instances(self):
        """
        Run the instances in the cluster backend.
        """

    @abc.abstractmethod
    def execute_on(self, ip, cmd):
        """
        Run command on some IP
        """

    @abc.abstractmethod
    def get_worker_ips(self):
        """
        Return list of all available worker machines
        """

    @abc.abstractmethod
    def terminate_cluster(self):
        """
        Terminate cluster instance
        """

    def hwfile(self):
        return self.name + '.hardware.json'

    def notify(self, message):
        print(message)


class EC2(ClusterInstance):

    recommended_worker_num = {
        'c3.large': 2,
        'c4.large': 2,
        'c3.xlarge': 4,
        'm3.medium': 1,
    }

    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')


    def __init__(self, name='default', config="{}"):
        super(EC2, self).__init__(name)
        self.cluster = {}

        # load cluster info
        if os.path.exists(self.hwfile()):
            self.cluster = json.load(open(self.hwfile(), 'r'))
            self.provider = self.cluster[0]["Provider configuration"]
            self.config = self.provider["Settings"]
        else:
            self.config = json.load(open(os.path.join('defaults', 'ec2_defaults.json')))

        userconfig = json.loads(config)

        # set up defaults where not specified
        for k in userconfig:
            self.config[k] = userconfig[k]


    def create(self):
        self.notify("Starting the cluster instances ... ")

        # Print out bucket names
        cluster = EC2.client.request_spot_fleet(
            SpotFleetRequestConfig={
                'AllocationStrategy': 'lowestPrice',
                'IamFleetRole': self.config['iamfleetrole'],
                'LaunchSpecifications': [
                    {
                        'SecurityGroups': [
                            {
                                'GroupId': self.config['security_group'],
                            }
                        ],
                        'InstanceType': self.config['instance_type'],
                        'SpotPrice': '0.3',
                        'ImageId': self.config['ami_image_id'],
                        'KeyName': self.config['aws_key_name'],
                    }
                ],
                'SpotPrice': '0.4',
                'TargetCapacity': self.config['target_capacity'],
            }
        )

        hwjson = {
            "Provider configuration": {
                'SpotFleetRequestId': cluster['SpotFleetRequestId'],
                'Settings': self.config,
            },
        }

        json.dump([hwjson], open(self.hwfile(), 'w'), indent=2, sort_keys=True)
        self.cluster = hwjson[0]
        self.notify("Started the cluster instances. ")

    def configure(self):
        # get ip's
        ips = self.get_worker_ips(self.provider)

        self.notify("Installing access using local identity...")

        # install public key for passwordless access
        commands = []
        for ip in ips:
            command = 'ssh-copy-id -i /home/iaroslav/.ssh/id_rsa.pub -f -o "IdentityFile '+ self.config['aws_access_key']\
                      +'" -o "StrictHostKeyChecking=no" ubuntu@' + ip
            commands.append(command)

        Parallel(n_jobs=len(commands))(
            delayed(subprocess.call)(command, shell=True)
            for command in commands
        )

        self.notify("Creating hardware json...")

        work_num = 1

        if self.config['instance_type'] in self.recommended_worker_num:
            work_num = self.recommended_worker_num[self.config['instance_type']]

        hwjson = {
            "Provider configuration": self.provider,
            "Means of access": "ssh_key_access",
            "Access config": {
                'User': 'ubuntu'
            },
            "IPs": ips,
            "Type": "CPUx86",
            "Workers": work_num
        }

        json.dump([hwjson], open(self.hwfile(), 'w'), indent=2, sort_keys=True)
        self.cluster = hwjson
        self.notify("Created hardware json. ")

    def get_worker_ips(self, info):
        rid = info['SpotFleetRequestId']

        while True:
            response = EC2.client.describe_spot_fleet_instances(
                SpotFleetRequestId=rid
            )

            inst_ids = [inst['InstanceId'] for inst in response['ActiveInstances']]
            ips = [EC2.ec2.Instance(id=id).public_ip_address for id in inst_ids]

            if len(ips) >= self.config['target_capacity']:
                break

            self.notify("Current capcity: %s" % len(ips))
            time.sleep(3)

        return ips

    def kill(self):
        if self.cluster is None:
            raise BaseException("Cluster does not exist!")

        EC2.client.cancel_spot_fleet_requests(
            SpotFleetRequestIds=[
                self.provider['SpotFleetRequestId'],
            ],
            TerminateInstances=True
        )

        os.remove(self.hwfile())

providers = {
    EC2.__name__: EC2
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--create', action='store_true', help="Request cloud instances.")
    parser.add_argument(
        '--config', action='store_true', help="Setup access, and store information to .hardware.json.")
    parser.add_argument(
        '--kill', action='store_true', help="Destroy cluster instance.")
    parser.add_argument(
        '--name', nargs="?", default='cluster', type=str, help="Name of the cluster instance.")
    parser.add_argument(
        '--provider', nargs="?", default='EC2', type=str, help="Name of provider of cloud instances.")
    parser.add_argument(
        '--settings', nargs="?", default='{}', type=str, help="Json describing cluster settings that deviate from defaults.")

    args = parser.parse_args()

    if not args.provider in providers:
        raise ValueError("Unknown provider %s, supported providers: %s"
                         % (args.provider, list(providers.keys())))

    manager = providers[args.provider](args.name, args.settings)

    if args.create:
        manager.create()

    if args.config:
        manager.configure()

    if args.kill:
        manager.kill()
