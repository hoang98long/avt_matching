#!/bin/bash

# shellcheck disable=SC2164
cd /home/avt/github/avt_classification
conda activate avt_classify
echo $1
python main.py --config_file $1