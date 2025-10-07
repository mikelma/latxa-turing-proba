#!/bin/bash

set -e

wget https://github.com/osa1/tiny/releases/download/v0.13.0/tiny-ubuntu-22.04-static.tar.gz -O tiny.tar.xz

wget https://raw.githubusercontent.com/mikelma/latxa-turing-proba/main/config.yaml -O cfg.yaml

tar xvf tiny.tar.xz

./tiny -c cfg.yaml

