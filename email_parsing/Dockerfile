FROM ubuntu:20.04

# Base
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y \
	git \
	curl \
	apt-utils \
	wget \
	software-properties-common \
	build-essential \
	vim 

WORKDIR /home

# install python and pip
RUN apt-get install -y \
	python3 \
	python3-pip \
	python3-dev
RUN pip3 -q install pip --upgrade
RUN alias python=python3

