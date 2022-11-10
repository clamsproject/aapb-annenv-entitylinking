#!/bin/bash

# Script to start a container from an image named link-annotator
#
# Takes an image tag and optionally a port to run the container on
#
# Usage:
#     sh run.sh 0.1.0
#     sh run.sh 0.1.1 8502

version=$1
port=8501

if [[ "$2" ]]; then port=$2; fi

echo "docker run -idt --rm -p ${port}:8501 -v $PWD/data:/data link-annotator:${version}"

docker run -idt --rm -p ${port}:8501 -v $PWD/data:/data link-annotator:${version}
