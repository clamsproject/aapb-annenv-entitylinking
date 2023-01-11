#!/bin/bash

# Script to start a container from an ELA image. By default it takes the latest
# version of an image named link-annotation and runs it on port 80, while using
# the "data" directory in this repository.
#
# Run this script from the root of this repository (one level up from where
# this script lives):
#
#    sh scripts/run.sh [-h] [-i IMAGE-NAME] [-p PORT] [-v VERSION] [-d DATA-DIR]
#
# Use the -i, -v, -p and -d options to change the image name, image version,
# port and data directory.

echo ${PWD}
image="link-annotation"
version="latest"
port="80"
data="${PWD}/data"

while getopts :i:p:v:d:h option; do
  case ${option} in
  i) image=${OPTARG};;
  p) port=${OPTARG};;
  v) version=${OPTARG};;
  d) data=${OPTARG};;
  h) echo "Usage: run.sh [-h] [-i IMAGE-NAME] [-p PORT] [-v VERSION] [-d DATA-DIR]"; exit;;
  \?) echo "Usage: run.sh [-h] [-i IMAGE-NAME] [-p PORT] [-v VERSION] [-d DATA-DIR]"; exit
  esac
done

echo "docker run -idt --rm -p ${port}:8501 -v ${data}:/data ${image}:${version}"

docker run -idt --rm -p ${port}:8501 -v ${data}:/data ${image}:${version}
