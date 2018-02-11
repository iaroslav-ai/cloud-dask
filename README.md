# What is this?

Create, manage and destroy clusters of dask in docker 
locally, on AWS or on other cloud providers [coming soon] using ssh only. 

Currently cluster can be provisioned on:
* AWS
* Your own machines

If you have IP's of and ssh on computing nodes on other cloud providers, 
it is straightforward to use code on these also.

Python3.5 is supported with base docker image that you extend to your specific use case. You can use other versions of python if you wish, but you will need to create your own docker container for that.

Using Docker allows to distribute easily your dependencies.

# Do you have anything that resembles a quickstart?

Yes, look into `documentation` for different setups.

# How does it work?

1. Create docker container with dask and necessary dependencies

It is suggested that you extend a base image [https://hub.docker.com/r/iaroslavai/daskbase/](https://hub.docker.com/r/iaroslavai/daskbase/).

2. Test locally dask with your container

3. Start cluster of machines with docker installed

4. Create a cluster out of these machines and use it.
