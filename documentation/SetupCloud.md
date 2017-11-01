# Checklists for how to set up everything necessary to run computations in a cloud

Setting up cloud is necessary to come up with hardware json.
Instructions are tested on Ubuntu, and primarily intended for Linux machines,
using python3.5. 

### AWS

1. Install boto3

```bash
pip install boto3
```

2. Create access keys at AWS IAM management. Go to Users, and create a 
user for yourself if you do not have one. Then go to security credentials,
and create Access Key ID and Secret Access Key pair. Your will need this 
for the next step.

3. Store your keys in ~/.aws/credentials:
```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region=YOUR_PREFERRED_REGION(eg us-east-1)
```

See the regions [here](http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region).

4. Copy a few parameters into the 'defaults' folder, into 'ec2_defaults.json'.
In particular:

* "ami_image_id": ID of ANI image with docker installed in it.
* "aws_access_key": File name of RSA key that you use to log in 
to created AWS instances.
* "aws_key_name": Name of the key as it is in AWS. Normally should be 
the same as the name of the key file without `.pem` extension.
* "security_group" Specify security group id where your instance will run. 
It is easiest to simply allow trafic from all prots to your machine in
security group settings, so that everything works fine.
* "iamfleetrole": To figure out IamFleetRole, go to IAM -> Roles and find 
fleet role (or fleet tagging role - also works). 
