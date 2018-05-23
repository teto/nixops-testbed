#!/usr/bin/python

"""
mininet_progmp_helper.py: Simple example of MPTCP in Mininet to test ProgMP Scheduler.

Check https://progmp.net for more details.

"""

import os
from time import sleep
import argparse
from progmp import ProgMP

from mininet.cli import CLI
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel

__author__ = "Alexander Froemmgen"

class StaticTopo(Topo):
    "Simple topo with 2 hosts and 'number_of_paths' paths"
    def build(self, number_of_paths = 2, loss = 0):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        
        for i in range(0, number_of_paths): 
            s = self.addSwitch('s' + str(i))

            self.addLink(h1, s, bw=100, delay="20ms", loss=float(loss))
            self.addLink(h2, s, bw=100, delay="20ms", loss=float(loss))

def runExperiment(number_of_paths, with_cli, loss):
    net = Mininet(topo=StaticTopo(number_of_paths, loss), link=TCLink)
    net.start()
    h1 = net.get('h1')
    h2 = net.get('h2')

    # there is probably a better way, but somehow we have to configure
    # the IP adresses
    for i in range(0, number_of_paths):
        h1.cmd('ifconfig h1-eth' + str(i) + ' 1' + str(i) + '.0.0.1')
        h2.cmd('ifconfig h2-eth' + str(i) + ' 1' + str(i) + '.0.0.2')
    
    # heat network to avoid intial packet artefacts
    for i in range(number_of_paths):
        h1.cmd("ping 1" + str(i) + ".0.0.2 -c 4")
    
    if with_cli:
        print "Experiment is ready to start... enter exit to start"
        CLI(net)

    h2.cmd('iperf -s -i 1 -y C > server_' + str(number_of_paths) + '.log &')
    h1.cmd('iperf -c 10.0.0.2 -t 10 -i 1 > client' + str(number_of_paths) + '.log')

    if with_cli:
        print "Experiment finished... enter exit to finish"
        CLI(net)
    
    # lets wait a moment
    sleep(3)
    # and ensure iperf is finished :-)
    os.system('pkill -f \'iperf\'')
    net.stop()
    sleep(1)
  
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="The file which contains the scheduler", required=True)
    parser.add_argument("-n", "--number_of_subflows", help="The number of subflows")
    parser.add_argument("-d", "--debug", help="Running in debug mode", default=False)
    parser.add_argument("-c", "--cli", help="Waiting in command line interface", default=False)
    parser.add_argument("-l", "--loss", help="Loss rate", default=0)
    args = parser.parse_args()
    
    setLogLevel('warning')
    
    if args.debug:
        os.system('sysctl -w net.mptcp.mptcp_debug=1')
    else:
        os.system('sysctl -w net.mptcp.mptcp_debug=0')

    os.system('sysctl -w net.mptcp.mptcp_enabled=1')
    # we don't have their RBS scheduler
    # os.system('sysctl -w net.mptcp.mptcp_scheduler=rbs')
    os.system('sysctl -w net.mptcp.mptcp_path_manager=fullmesh')
    
    schedulerName = ProgMP.getSchedulerName(args.file)
    if schedulerName is None:
        print "Scheduler file makes some trouble..."
        exit()
        
    with open(args.file, "r") as src:
        schedProgStr = src.read()
        
    try:
        ProgMP.loadScheduler(schedProgStr)
    except:
        print "Scheduler loading error."
        exit()
    
    print "now setting sched", schedulerName
    ProgMP.setDefaultScheduler(schedulerName)
   
    if args.number_of_subflows:
        number_of_paths = [int(args.number_of_subflows)]
    else:
        number_of_paths = [1, 2, 3]
    
    for paths in number_of_paths:
        print "Running experiments with ", paths, "subflows"
        runExperiment(paths, args.cli, args.loss)
    
    ProgMP.setDefaultScheduler("simple")
    ProgMP.removeScheduler(schedulerName)
