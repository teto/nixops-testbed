#!/usr/bin/env sh

# todo use timestamp for name
# tshark counts number of packets so we need to blackhole stdout
# echo 'extra args'
# echo $@

rm -rf  out/ 
# server.pcap server.log
mkdir out

pkill -9 tshark
pkill -9 iperf

echo "starting tshark"
# add -i any to capture from several interfaces
nohup tshark -n -w out/server.pcap -f "tcp port 5201" 2>1 &
sleep 3

# --one-off accepts only one connection at a time
# -s server
# -D daemon
# --one-off
# -d/--debug
nohup iperf -s -D  -d --logfile out/iperf.log

# it is daemonized automatically
# nohup netserver -4 -d

# wait is a bash builtins
# $! is the pid of the last program launched (aka iperf here)
# wait $!
# --logfile server.log

# handle one client connection then exit
# TODO use -J / --logfile /-d

