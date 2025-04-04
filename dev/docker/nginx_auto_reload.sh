# nginx_auto_reload.sh

#!/bin/sh
while :; do
    sleep 12h
    nginx -t && nginx -s reload
done &