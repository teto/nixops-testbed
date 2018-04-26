#! /usr/bin/env sh

echo 'extra args'
echo $@

rm ./*.pcap ./*.log
pkill -9 tshark
pkill -9 iperf
sleep 1

# todo use timestamp for name
# maybe I should use -H
# 
# see on how to put limits https://www.thegeekstuff.com/2014/05/wireshark-file-buffer-size/
# duration is in sec
# if you use '-b duration:10' then 0w is used as a template client_XXXX.pcap
tshark -n -q -f "tcp port 5201" -w client.pcap  2>1 &

sleep 3

# run 5sec session
# -t 5 = lasts 5sec
 # -n, --bytes n[KM]
 #              number of bytes to transmit (instead of -t)
iperf -d -c server --bytes 10M --connect-timeout 10 -J --logfile client.log

# TODO
# -l -2 = number of request
# netperf -H server -4 -l -2

# or maybe just don't kill it
# sleep 3
pkill -9 tshark
dmesg > kmsg.log

echo "client finished"
