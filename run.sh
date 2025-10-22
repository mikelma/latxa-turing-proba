#!/bin/bash

set -e

cat >izenak.txt <<EOL
Jon
Noa
Unax
Martin
Eneko
Olatz
David
Maialen
Haizea
Oihane
Irene
Leire
Eider
Maite
Iñaki
Idoia
Irati
Jonan
Iñigo
Goizane
Eguzki
Ilargi
Hodei
Iraitz
Ekia
EOL

cat >abizenak.txt <<EOL
Agirre
Etxeberria
Arriola
Goikoetxea
Larrañaga
Mendizabal
Elorza
Arozena
Altuna
Garate
Odriozola
Zabaleta
Aranburu
Irureta
Erdozia
Olabarria
Urkizu
Aristi
Araneta
Lizeaga
Arrieta
Etxegarai
Aiestaran
Zubizarreta
EOL

wget https://github.com/osa1/tiny/releases/download/v0.13.0/tiny-ubuntu-22.04-static.tar.gz -O tiny.tar.xz

wget https://raw.githubusercontent.com/mikelma/latxa-turing-proba/main/config.yaml -O cfg.yaml

tar xvf tiny.tar.xz

room=$1

username="$(shuf -n 1 izenak.txt)-$(shuf -n 1 abizenak.txt)"
echo "username: $username"

# Ander
# Amaia
# Ainhoa
# Alba
# Aitzol
# Alaitz
# Ane
# Aintzane
# Alex
# Andoni

sed -i "s/proba/$username/g" cfg.yaml
sed -i "s/turing/$room/g" cfg.yaml

./tiny -c cfg.yaml

