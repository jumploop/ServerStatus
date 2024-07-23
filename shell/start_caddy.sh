#!/usr/bin/env sh
/usr/bin/caddy run --config /etc/caddy/Caddyfile && /ServerStatus/server/sergate --config=/ServerStatus/server/config.json --web-dir=/usr/share/caddy
