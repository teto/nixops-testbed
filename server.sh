#!/usr/bin/env sh

# todo use timestamp for name
# tshark counts number of packets so we need to blackhole stdout
# echo 'extra args'
# echo $@

rm server.pcap server.log
pkill -9 tshark
pkill -9 iperf

echo "starting tshark"
# add -i any to capture from several interfaces
nohup tshark -n -w server.pcap -f "tcp port 5201" 2>1 &
sleep 3

# --one-off
# -s accepts only one connection at a time
# --one-off
nohup iperf -s -D  -d --logfile server.log
# --logfile server.log

# handle one client connection then exit
# TODO use -J / --logfile /-d

dmesg > kmsg.log
