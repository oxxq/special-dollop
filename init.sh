#!/bin/bash

sudo apt install -y python2 lighttpd php curl wget;
sudo pip2 install requests pytz;

if ! [ -d "/usr/lib/python2.7/site-packages/tvsp2xmltv" ] || ! [ -e "/usr/lib/python2.7/site-packages/tvspielfilm2xmltv.py" ]; then
    sudo cp -r tvsp2xmltv /usr/lib/python2.7/site-packages/;
    sudo cp tvspielfilm2xmltv.py /usr/lib/python2.7/site-packages/;
fi;

echo "init Done! Now start: ./start.sh ...";
