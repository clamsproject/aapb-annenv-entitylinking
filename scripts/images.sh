#!/bin/bash

# List all docker images matching a search term
#
# Usage:
#     sh images.sh <term>

term=$1

echo "docker images | grep ${version}"

docker images | grep ${term}
