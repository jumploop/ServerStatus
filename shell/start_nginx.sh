#!/usr/bin/env bash
/etc/init.d/nginx start
/ServerStatus/server/sergate --config=/ServerStatus/server/config.json --web-dir=/usr/share/nginx/html
