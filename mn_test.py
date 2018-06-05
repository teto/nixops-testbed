#!/usr/bin/env nix-shell 
#!nix-shell -p 'python.withPackages(ps:[ps.mininet-python])' -i python
# todo add python ?
"""
derived from mininet_progmp_helper.py

"""

import os
from time import sleep
import argparse
# from progmp import ProgMP

from mininet.cli import CLI
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink, AsymTCLink
from mininet.log import setLogLevel, info

# look for __mptcp_reinject_data call
# [   63.813460] acking on fast path, looking for best sock 
# [   63.813461] Looking for fastest path

# todo make it so that we just have to unpack the parameter

dataAmount = "10M"

# can get parameters from 
# Chan, M. C., & Ramjee, R. (2005). TCP/IP performance over 3G wireless links with rate and delay variation. Wireless Networks, 11(1–2), 81–97. https://doi.org/10.1007/s11276-004-4748-7

topoWireLessHetero = [
    # parameters taken from "how hard can it be"
    { 'bw': 2, 'delay': "150ms", "loss": 1},
    # fast wifi
    { 'bw': 8, 'delay': "20ms", "loss": 20},
]

forward={ 'bw': 10, 'delay': "20ms", "loss": 1}
backward={ 'bw': 90, 'delay': "20ms", "loss": 1}

topo = [
    # loss is in percoutage
    { 'bw': 5, 'delay': "20ms", "loss": 1, "max_queue_size":1000, "use_htb": True, 
        'params1': forward, 'params2': backward
    },
    { 'bw': 5, 'delay': "20ms", "loss": 20},
]

# So with AsymTCLink one can use
# Link.__init__(self, node1, node2, port1=port1, port2=port2,
#               intfName1=intfName1, intfName2=intfName2,
#               cls1=TCIntf,
#               cls2=TCIntf,
#               addr1=addr1, addr2=addr2,
#               params1=par1,
#               params2=par2)


class StaticTopo(Topo):
    "Simple topo with 2 hosts and 'number_of_paths' paths"
    def build(self, number_of_paths = 2, loss = 0):
        client = self.addHost('client')
        server = self.addHost('server')
        
        for i, params in enumerate(topo):
            s = self.addSwitch('s' + str(i))

            # one good fast path
            self.addLink(client, s, **params)
            link2 = self.addLink(server, s, **params)
            # self.addLink(server, s, bw=100, delay="120ms", loss=float(loss))
            print("just for testing, link type = ", type(link2))

class AsymetricTopo(Topo):
    "Simple topo with 2 hosts and 'number_of_paths' paths"
    def build(self, number_of_paths = 2, loss = 0):
        client = self.addHost('client')
        server = self.addHost('server')
        
        for i, params in enumerate(topo):
            s = self.addSwitch('s' + str(i))

            # TODO use instead
            # AsymTCLink
            # one good fast path
            link1 = self.addLink(client, s, **params)
            link2 = self.addLink(server, s, **params)
            # self.addLink(server, s, bw=100, delay="120ms", loss=float(loss))


def runExperiment(number_of_paths, with_cli, loss):
    net = Mininet(topo=StaticTopo(number_of_paths, loss), link=AsymTCLink)
    net.start()
    client = net.get('client')
    server = net.get('server')


    # there is probably a better way, but somehow we have to configure
    # the IP adresses
    for i in range(0, number_of_paths):
        client.cmd('ifconfig client-eth' + str(i) + ' 1' + str(i) + '.0.0.1')
        server.cmd('ifconfig server-eth' + str(i) + ' 1' + str(i) + '.0.0.2')
    
    # heat network to avoid intial packet artefacts
    # for now I don't care
    for i in range(number_of_paths):
        client.cmd("ping 1" + str(i) + ".0.0.2 -c 4")

    client.cmd('tshark -i any -w out/client_' + str(number_of_paths) + '.pcap &')
    server.cmd('tshark -i any -w out/server_' + str(number_of_paths) + '.pcap &')
    
    if with_cli:
        print("Experiment is ready to start... enter exit to start")
        CLI(net)

    # iperf2 version
    # server.cmd('iperf -s -i 1 -y C > out/server_' + str(number_of_paths) + '.log &')
    # client.cmd('iperf -c 10.0.0.2  -n ' + dataAmount + ' -i 1 > out/client_' + str(number_of_paths) + '.log')

    # # iperf 3 version
    # server.cmd('iperf -s -i 1 -y C > out/server_' + str(number_of_paths) + '.log &')
    # client.cmd('iperf -c 10.0.0.2  -n ' + dataAmount + ' -i 1 > out/client_' + str(number_of_paths) + '.log')

    # netperf version
    # server.cmd('iperf -s -i 1 -y C > out/server_' + str(number_of_paths) + '.log &')
    # client.cmd('iperf -c 10.0.0.2  -n ' + dataAmount + ' -i 1 > out/client_' + str(number_of_paths) + '.log')

    # flent version
    # flent rrul -p ping_cdf -l 60 -H address-of-netserver -t text-to-be-included-in-plot -o filename.png
    server.cmd('netserver -D > out/server_' + str(number_of_paths) + '.log &')
    client.cmd('flent rrul -p ping_cdf -l 60 -H 10.0.0.2 -t "mon titre" -o filename.png')   

    if with_cli:
        print ("Experiment finished... enter exit to finish")
        CLI(net)
    
    # lets wait a moment
    sleep(3)
    # and ensure iperf is finished :-)
    os.system('pkill -f \'iperf\'')
    os.system('pkill -f \'tshark\'')
    net.stop()
    sleep(1)
  
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser.add_argument("-f", "--file", help="The file which contains the scheduler", required=True)
    parser.add_argument("-n", "--number_of_subflows", help="The number of subflows")
    parser.add_argument("-d", "--debug", choices=['debug', 'info', 'error'], help="Running in debug mode", default='info')
    parser.add_argument("-t", "--capture", help="capture packets", default=False)
    parser.add_argument("-c", "--cli", help="Waiting in command line interface", default=False)
    parser.add_argument("-l", "--loss", help="Loss rate", default=0)
    args = parser.parse_args()
    
    setLogLevel(args.debug)
    
    # if args.debug:
    #     os.system('sysctl -w net.mptcp.mptcp_debug=1')
    # else:
    #     os.system('sysctl -w net.mptcp.mptcp_debug=0')

    os.system('sysctl -w net.mptcp.mptcp_enabled=1')

    # we don't have their RBS scheduler
    # os.system('sysctl -w net.mptcp.mptcp_scheduler=rbs')

    os.system('sysctl -w net.mptcp.mptcp_path_manager=fullmesh')

    # TODO use iperf command instead
    os.system('sysctl -w net.ipv4.tcp_rmem="400000 400000 400000"')
    
    if args.number_of_subflows:
        number_of_paths = [int(args.number_of_subflows)]
    else:
        number_of_paths = [1, 2, 3]
    
    for paths in number_of_paths:
        print("Running experiments with ", paths, "subflows")
        runExperiment(paths, args.cli, args.loss)
    
    # ProgMP.setDefaultScheduler("simple")
    # ProgMP.removeScheduler(schedulerName)
