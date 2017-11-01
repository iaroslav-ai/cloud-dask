# Description of fields in hardware and dask configuration json

Here is a description of fields and how to set them. Both files share
same semantics for fields.

Important: the first machine in the hardware list is always used as a scheduler.

* "Means of access": How to access the machine(s). Currently supported is 'ssh_key_access'. 
* "Access config": Access credentials and configurations. For example, 
```json
{
"Access config": {
      "Secret key": "/home/user/.ssh/id_rsa"
    }
}
```
* "IPs": list of all IP's of machines that comply with this configuration.
* "Type": Type of machine. Currently only 'CPUx86'. 
This will be used to run different version of docker, such as
'nvidia-docker' for GPU machines, or even different versions of 
docker image, eg on 'ARM' machines. 
* "Workers": Number of workers to run with dask.
* "Provider configuration": For example spot request ID for AWS.
Is useful when the cluster is hosted in a cloud.
* "Docker image": Docker image used for particular machine(s)
* "Role": What role a particular machine serves. 