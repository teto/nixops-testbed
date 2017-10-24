#! /usr/bin/env sh


pkill -9 tshark
pkill -9 iperf
sleep 2

# todo use timestamp for name
tshark -n -w client.pcap -q &

sleep 10

# run 5sec session
# -t 5 = lasts 5sec
iperf -c server -n 10M --connect-timeout 10000

pkill tshark

