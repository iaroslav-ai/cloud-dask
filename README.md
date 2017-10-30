Development of this is postponed untill I will actually need it.

# What is this?

Create, manage and destroy clusters of dask in docker on AWS and other cloud providers. 
Cloud providers currently supported:

* AWS

Python3.5 is supported with base docker image that you extend to your specific use case. You can use other versions of python if you wish, but you will need to create your own docker container for that. 

# How does it work?

1. Create docker container with dask and necessary dependencies

It is suggested that you extend a base image [https://hub.docker.com/r/iaroslavai/daskbase/](https://hub.docker.com/r/iaroslavai/daskbase/).

2. Test locally dask with your container

3. Create and manage cluster with your docker container.