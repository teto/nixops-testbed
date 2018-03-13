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
# -D daemon
# --one-off
# -d/--debug
# --one-off
nohup iperf -s -D  -d --logfile server.log

# it is daemonized automatically
# nohup netserver -4 -d

# wait is a bash builtins
# $! is the pid of the last program launched (aka iperf here)
# wait $!
# --logfile server.log

# handle one client connection then exit
# TODO use -J / --logfile /-d

