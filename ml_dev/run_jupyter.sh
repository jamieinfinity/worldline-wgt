#!/bin/bash
# file: run_h2o.sh

dockername=${USER}_JUPYTER

docker run -d -t  \
--shm-size=1g \
--hostname=$(hostname)_H2O \
--name=${dockername} \
-e HOME=$HOME \
-e USER=$USER \
-e PYTHONPATH=~/Projects/WorldLine/worldline-wgt/ml_dev/utils\
:~/Projects/WorldLine/worldline-wgt/server/src \
-u $(id -u):$(id -g) \
-v $HOME:$HOME \
-p 54321:54321 \
-p 8080:8080 \
-p 8888:8888 \
-w $HOME \
continuumio/anaconda3:latest

#docker exec ${dockername} bash -c \
#'pip3 install --user keras'

#docker exec ${dockername} bash -c \
#'pip3 install --user hyperopt'

#docker exec ${dockername} bash -c \
#'pip3 install --user hyperas'

#docker exec ${dockername} bash -c \
#'pip3 install --user sklearn'

#docker exec ${dockername} bash -c \
#'pip3 install --user ggplot'

docker exec -it ${dockername} bash

docker stop ${dockername} && docker rm ${dockername}
