#!/bin/bash

# bash message colors
red=$'\e[1;31m'
grn=$'\e[1;32m'
yel=$'\e[1;33m'
blu=$'\e[1;34m'
mag=$'\e[1;35m'
cyn=$'\e[1;36m'
end=$'\e[0m'

printf "\n\n ${grn}Installing system libraries...${end} \n\n"
apt-get -y update
apt-get -y install curl

printf "\n\n ${grn}Installing MyStem...${end} \n\n"
rm -rf /tmp/mystem*
curl -sL http://download.cdn.yandex.net/mystem/mystem-3.1-linux-64bit.tar.gz -o /tmp/mystem-3.1-linux-64bit.tar.gz
cd /tmp
tar -xzf mystem-3.1-linux-64bit.tar.gz
mv mystem /usr/local/bin/mystem
cd /tmp
rm -rf /tmp/mystem*