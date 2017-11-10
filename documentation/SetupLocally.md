# Checklist for how to set up everything necessary to run computations on your local cluster


1. You have a cluster of machines running on your local network

You can also run only on your own PC / laptop etc.

2. You use machine with OS(s) where you can ssh into (even for sinlge machine!), and run docker from terminal.

This is true if you have a flavour of Linux, such as Ubuntu. 
For Ubuntu you can enable ssh access with 

```bash
apt-get install openssh-server
```

You also need docker. In general, see Docker installation procedure.

For Ubuntu (tested on Ubuntu 16) you can copy paste this into your terminal and execute:

```bash
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates -y
sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

sudo rm /etc/apt/sources.list.d/docker.list
# get version of os
. /etc/lsb-release
echo 'deb https://apt.dockerproject.org/repo ubuntu-'$DISTRIB_CODENAME' main' | sudo tee --append /etc/apt/sources.list.d/docker.list
sudo apt-get update
sudo apt-get purge lxc-docker
apt-cache policy docker-engine

sudo apt-get update
sudo apt-get install linux-image-extra-$(uname -r) -y
sudo apt-get install apparmor -y

sudo apt-get update
sudo apt-get install docker-engine -y
sudo service docker start
sudo docker run hello-world
```

Also, make sure that you can run docker from command line without sudo.
You can do that by adding current user to the 'docker' group:

```bash
sudo usermod -aG docker $USER
```

You might need to restart your terminal session to see changes take 
action.

You might also see warnings

Solve this with
```bash
sudo chown "$USER":"$USER" /home/"$USER"/.docker -R
sudo chmod g+rwx "/home/$USER/.docker" -R
```

3. You know ip's of other machines.

On Ubuntu, you can get ip of a machine using 

```bash
ifconfig
```

4. You can ssh into your machines from your workstations using RSA key.

On Ubuntu, you can set up RSA access in two steps.
First, generate key for your machine if you did not do so already:

```bash
ssh-keygen
``` 

For the software to work properly, please do not use passphrase 
for key generation. PR's are welcome to change this!

Secondly, install your key on other machines using:

```bash
ssh-copy-id IP_OF_SOME_MACHINE
```

Do this for every IP of every machine that you have.

5. Create a hardware json file which lists all your machines. Name of the file should be 

`cluster_name.hardware.json`

In this file, specify parameters of your machine. Here is example specification:

```json
[
  {
    "Means of access": "ssh_key_access",
    "Access config": {
      "Secret key": "/home/iaroslav/.ssh/id_rsa"
    },
    "IPs": ["192.168.0.88"],
    "Type" : "CPUx86",
    "Workers" : 4,
    "Provider configuration": null
  }
]
``` 

See description of fields in `JsonFields.md`.

6. Create your docker image with necessary dependencies. 

You can simply run the `iaroslavai/daskbase`  docker image using

```bash
docker run --net='host' -d  iaroslavai/daskbase  /bin/bash 
```

or create your own image (it needs python3 and dask[complete] 
installed).

Before you do anything, create docker hub account, and login using

```bash
docker login
```

so that you can push your created image.

This will give you the terminal promt of docker container. 
There, you can run installation of all necessary dependencies
similar to how you would do that in normal Ubuntu.

After you installed all the dependencies, exit the terminal using
`Ctrl+C`. Commit your docker container to a new image using

```bash 
docker commit [id of container] username_on_dockerhub/yourimagename
```

and push the image into the repository

```bash 
docker push username_on_dockerhub/yourimagename
```

7. Create your cluster config with this command:

```bash 
python3 daskmanager.py --config --image=username_on_dockerhub/yourimagename
```

8. You are ready to run your cluster! Run it as so:

```bash 
python3 daskmanager.py --reset
```

This will remove all existing docker containers, pull the neweset 
version of your image, create worker and scheduler docker 
containers, and give you the IP of scheduler.

You can test your cluster using `gridsearch.py`.
