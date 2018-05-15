#! /usr/bin/env sh

echo 'extra args'
echo $@

KERVER="$(uname -r)"

# rm ./*.pcap ./*.log
rm -rf out

mkdir out

pkill -9 tshark
pkill -9 iperf
pkill -9 cat
sleep 1

rmmod "/run/current-system/kernel-modules/lib/modules/$KERVER/kernel/net/ipv4/tcp_probe.ko"

# todo use timestamp for name
# maybe I should use -H
# 
# see on how to put limits https://www.thegeekstuff.com/2014/05/wireshark-file-buffer-size/
# duration is in sec
# if you use '-b duration:10' then 0w is used as a template client_XXXX.pcap
# tcp port 5201
tshark -n -q -f "tcp" -w out/client.pcap  2>1 &

sleep 3


# start tcpprobe
# insmod doesn't work, use modprobe instead ?
# a priori
# [time][src][dst][length][snd_nxt][snd_una][snd_cwnd][ssthresh][snd_wnd][srtt][rcv_wnd]
# 
	# return scnprintf(tbuf, n,
	# 		"%lu.%09lu %pISpc %pISpc %d %#x %#x %u %u %u %u %u %u %u\n",
	# 		(unsigned long)ts.tv_sec,
	# 		(unsigned long)ts.tv_nsec,
	# 		&p->src, &p->dst, p->length, p->snd_nxt, p->snd_una,
	# 		p->snd_cwnd, p->ssthresh, p->snd_wnd, p->srtt,
	# 		p->sowd_out, p->sowd_in, p->rcv_wnd);
# 0.507024701 192.168.122.233:40080 192.168.122.167:5201 28 0x65cef3ca 0x65ce5bea 30 29 1930880 40548 0 0 87616
# modprobe won't work for now see https://github.com/NixOS/nixpkgs/issues/40485
# modprobe tcp_probe port=5201 full=1
insmod /run/current-system/kernel-modules/lib/modules/$KERVER/kernel/net/ipv4/tcp_probe.ko port=5201 full=1
# chmod 444 /proc/net/tcpprobe

# use nohup instead ?
cat /proc/net/tcpprobe > out/tcpprobe.out &
# not sure what this is (return value ?)
TCPCAP=$!

# run 5sec session
# -t 5 = lasts 5sec
 # -n, --bytes n[KM]
 #              number of bytes to transmit (instead of -t)
iperf -d -c server --bytes 10M --connect-timeout 10 -J --logfile out/client.log

# TODO
# -l -2 = number of request
# netperf -H server -4 -l -2

# or maybe just don't kill it
# sleep 3
pkill -9 tshark
dmesg > out/kmsg.log

echo "client finished"
