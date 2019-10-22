#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "You must enter exactly 1 command line argument"
    exit 2
fi

docker run -it --rm --init --name $1 --hostname $1 confd-openroadm $1
