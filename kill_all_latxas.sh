#!/bin/bash

#Euskaraz
eu_max=9
for i in `seq 1 $eu_max`
do
    screen -S latxa-$i-eu -X quit
done


es_max=7
for i in `seq 1 $es_max`
do
    screen -S latxa-$i-es -X quit
done
