"""
```
sudo pip install boto3
```

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
from pprint import pprint
import os
import time
from tqdm import tqdm
import joblib
import json
import argparse
import abc


class ClusterInstance:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, name, config):
        """
        Create an instance of named cluster
        """

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

    @abc.abstractmethod
    def cores_per_ip(self):
        """
        Return number of cores every IP has
        """
        return 1


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
        super(EC2, self).__init__(name, config)
        self.name = name
        self.cluster = {}

        # load cluster info
        if os.path.exists(self._get_cluster_file()):
            self.cluster = json.load(open(self._get_cluster_file(), 'r'))
            self.config = self.cluster['config']
        else:
            self.config = json.load(open('ec_config.json', 'r'))

        userconfig = json.loads(config)

        # set up defaults where not specified
        for k in userconfig:
            self.config[k] = userconfig[k]

    def _get_cluster_file(self):
        return self.name + '.ec2.cluster.json'

    def start_cluster_instances(self):
        pprint("Starting the cluster instances ... ")

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

        cluster = {
            'SpotFleetRequestId': cluster['SpotFleetRequestId'],
            'config': self.config,
        }

        json.dump(
            cluster, open(self._get_cluster_file(), 'w')
        )

        self.cluster = cluster

        return cluster

    def execute_on(self, ip, cmd):
        cmd = "ssh -oStrictHostKeyChecking=no -i '" + \
              self.config['aws_access_key'] + \
              "' ubuntu@" + ip + " '" + cmd + "'"
        os.system(cmd)

    def get_worker_ips(self):
        rid = self.cluster['SpotFleetRequestId']

        while True:
            response = EC2.client.describe_spot_fleet_instances(
                SpotFleetRequestId=rid
            )

            inst_ids = [inst['InstanceId'] for inst in response['ActiveInstances']]
            ips = [EC2.ec2.Instance(id=id).public_ip_address for id in inst_ids]

            if len(ips) >= self.config['target_capacity']:
                break

            pprint("Current capcity: %s" % len(ips))
            time.sleep(3)

        return ips

    def terminate_cluster(self):
        if self.cluster is None:
            raise BaseException("Cluster does not exist!")

        EC2.client.cancel_spot_fleet_requests(
            SpotFleetRequestIds=[
                self.cluster['SpotFleetRequestId'],
            ],
            TerminateInstances=True
        )

        os.remove(self._get_cluster_file())

    def cores_per_ip(self):
        if self.config['instance_type'] in self.recommended_worker_num:
            return self.recommended_worker_num[self.config['instance_type']]
        else:
            return 1

