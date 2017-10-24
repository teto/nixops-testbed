#! /usr/bin/env sh

# todo use timestamp for name
# tshark counts number of packets so we need to blackhole stdout

pkill tshark
pkill iperf

tshark -n -w server.pcap -q &
iperf -s --one-off

# handle one client connection then exit
# TODO use -J / --logfile /-d

