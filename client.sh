#! /usr/bin/env sh

echo 'extra args'
echo $@

rm client.pcap client.log
pkill -9 tshark
pkill -9 iperf
sleep 2

# todo use timestamp for name
# maybe I should use -H
tshark -n -w client.pcap -q -f "tcp port 5201"  &

sleep 5

# run 5sec session
# -t 5 = lasts 5sec
iperf -d -c server -n 100k --connect-timeout 10000 -J --logfile client.log


# or maybe just don't kill it
sleep 5
pkill tshark

dmesg > kmsg.log
