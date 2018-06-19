#!/usr/bin/env nix-shell 
#!nix-shell shell-mininet.nix -i python --show-trace

# To clean everything run 'mn -c'

# python needs to read this 
# -*- coding: utf-8 -*-
# but it will check just the first 2 lines :/ https://www.python.org/dev/peps/pep-0263/#defining-the-encoding

# todo add python ?
"""
derived from mininet_progmp_helper.py

"""

import os
import sys
from time import sleep
import argparse
import signal
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

topoWireLessHetero = [
    # parameters taken from "how hard can it be"
    { 'bw': 1, 'delay': "150ms", "loss": 1},
    # fast wifi
    { 'bw': 4, 'delay': "20ms", "loss": 20},
]

forward={ 'delay': "10ms"}
backward={ 'delay': "50ms"}

topo = [
    # loss is in percoutage
    # 'delay': "20ms",
    { 'bw': 2,  "loss": 1, "max_queue_size":1000, "use_htb": True, 
        'params1': forward, 'params2': backward
    },
    { 'bw': 2, 'delay': "20ms", "loss": 20},
]

# So with AsymTCLink one can use
# Link.__init__(self, node1, node2, port1=port1, port2=port2,
#               intfName1=intfName1, intfName2=intfName2,
#               cls1=TCIntf,
#               cls2=TCIntf,
#               addr1=addr1, addr2=addr2,
#               params1=par1,
#               params2=par2)

net = None

# clean sthg
def sigint_handler(signum, frame):
    print('Stop pressing the CTRL+C!')
    global net
    net.stop()
    sys.exit(3)

signal.signal(signal.SIGINT, sigint_handler)

class StaticTopo(Topo):
    "Simple topo with 2 hosts and 'number_of_paths' paths"
    def build(self, number_of_paths = 2, loss = 0):
        # If you need per-host private directories, you can specify them as options to Host, for example:
        # h = Host( 'h1', privateDirs=[ '/some/directory' ] )
        client = self.addHost('client')
        server = self.addHost('server')
        
        for i, params in enumerate(topo):
            s = self.addSwitch('s' + str(i))

            # one good fast path
            self.addLink(client, s, **params)
            link2 = self.addLink(server, s, **params)
            # self.addLink(server, s, bw=100, delay="120ms", loss=float(loss))
            print("just for testing, link type = ", type(link2))

# tests - {
# };

def runExperiment(number_of_paths, interactive, test, loss, out, **kwargs):

    def _out(*args):
        """ Use it to name files"""
        suffix = '_'.join(map(str, args))
        return os.path.join(out, suffix )

    # using 
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
    # for i in range(number_of_paths):
    #     client.cmd("ping 1" + str(i) + ".0.0.2 -c 4")

        # client.cmd("owping 1" + str(i) + ".0.0.2 -c 4 2>&1 > owping" + str(i) + ".log ")

    # sys.exit(1)

    # owamp doesn't work through NAT except in authenticated mode
    # create owamp
    # todo I can create it directly
    # created toto/test
    # server.cmd('pfstore -f owamp.pfs -n toto')
    
    # to run via cli
    # client owping 10.0.0.2 -c 4 -A A
    # server owampd -U owamp -R . -d /tmp -v -a A

    if interactive:
        print("Experiment is ready to start... enter exit to start")
        print("client ping 10.0.0.2 -c 4")
        CLI(net)

    if kwargs.get("capture"):
        print("Capturing packets...")
        print('tshark -r out/client_2.pcap -z "conv,mptcp"')
        # TODO use popen instead ?
        client.cmd("tshark -i any -w '%s' &" % _out("client_", number_of_paths, ".pcap"))
        server.cmd("tshark -i any -w '%s' &" % _out("server_", number_of_paths, ".pcap"))
        # let tshark the time to setup itself
        os.system("sleep 5")
    

    # iperf2 version
    # server.cmd('iperf -s -i 1 -y C > out/server_' + str(number_of_paths) + '.log &')
    # client.cmd('iperf -c 10.0.0.2  -n ' + dataAmount + ' -i 1 > out/client_' + str(number_of_paths) + '.log')

    # netperf version
    # server.cmd('iperf -s -i 1 -y C > out/server_' + str(number_of_paths) + '.log &')
    # client.cmd('iperf -c 10.0.0.2  -n ' + dataAmount + ' -i 1 > out/client_' + str(number_of_paths) + '.log')

    # flent version
    # flent rrul -p ping_cdf -l 60 -H address-of-netserver -t text-to-be-included-in-plot -o filename.png
    # server.cmd('netserver -Ddf > out/server_' + str(number_of_paths) + '.log &')
    # TODO test manually first 
    # client.cmd('flent rrul -p ping_cdf -l 60 -H 10.0.0.2 -t "mon titre" -o filename.png')   

    # # iperf 3 version
    cmd = "iperf3 -s --json --logfile=%s" % (_out("server_iperf", number_of_paths, ".log"),)
    print("starting", cmd)
    server_iperf = server.popen(cmd)
    # out, err = server_iperf.communicate()
    # if err is not None:
    if server_iperf.returncode:
        print("Failed to run ", cmd)
        print("returned", server_iperf.returncode)
        print(err)
        sys.exit(1)

    # server.cmd("iperf3 -s --json --logfile '%s' &" % _out("server_iperf", number_of_paths, ".log"))
    # server_iperf.poll()
    # TODO get results else it might get dirty
        
    # run_tests()
    # TODO move the loop to here
    for run in range(4):

        # in iperf3, the client sends the data so...
        reinject_out = _out("check", run, ".csv")
        print(reinject_out)
        with open(reinject_out, "w+") as fd:
            client_check = client.popen(
                ["/home/teto/testbed/check_opportunistic_reinject.py", "-j"], 
                stdout=fd,
                universal_newlines=True
            )
            out, err = client_check.communicate()

            if err is not None:
                print("Failed running with returncode=", client_check.returncode)
                print(err)
                break
            # assert err == 0

            client_iperf = client.popen("iperf3 -c {serverIP} -n {dataAmount} --logfile {logfile} ".format(
            # client.cmd("iperf3 -c {serverIP} -n {dataAmount} --logfile {logfile} ".format(
                serverIP=server.IP(),   # seems to work
                # serverIP="10.0.0.2",
                dataAmount="5M",
                # paths=number_of_paths
                logfile=_out("client_iperf", "path", number_of_paths, "run", run, ".log")
            ))
            # wait for iperf to finish
            client_iperf.wait()
            # client.waitOutput()

            # if client_check.returncode:
            print("out/errs=", out, err)
            print("returncode=", client_iperf.returncode)
            # client.cmd("kill %d" % (client_check.pid,))
            client_check.kill()
        
        # res = client.cmd('/home/teto/testbed/gen_cpt.sh 10.0.0.2')
        # print("RES=%r" % res)


    if interactive:
        print ("Experiment finished... enter exit to finish")
        CLI(net)
    
    # lets wait a moment
    sleep(3)
    # and ensure iperf is finished :-)
    # server.cmd("kill %d" % (server_iperf.pid,))
    server_iperf.terminate()
    # os.system('pkill -f \'iperf\'')

    if kwargs.get("capture"):
        os.system('pkill -f \'tshark\'')

    net.stop()
    sleep(1)
  
if __name__ == '__main__':

    print("To clean run `mn -c`")
    parser = argparse.ArgumentParser()
    # parser.add_argument("-f", "--file", help="The file which contains the scheduler", required=True)
    parser.add_argument("-n", "--number_of_subflows", help="The number of subflows")
    parser.add_argument("-d", "--debug", choices=['debug', 'info', 'error'], help="Running in debug mode", default='info')
    parser.add_argument("-t", "--test", choices=["iperf3-cdf"], help="test to run", default="iperf3-cdf")
    parser.add_argument("-c", "--capture", action="store_true", help="capture packets", default=False)
    parser.add_argument("-i", "--interactive", action="store_true", help="Waiting in command line interface", default=False)
    parser.add_argument("-l", "--loss", help="Loss rate (between 0 and 100", default=0)
    parser.add_argument("-o", "--out", action="store", default="out", help="out folder")
    # parser.add_argument("-b", "--batch", action="store", default="out", help="out folder")
    # parser.add_argument("-r", "--clean", action="store", default="out", help="out folder")
    args, unknown_args = parser.parse_known_args()
    
    setLogLevel(args.debug)

    print("CWD=", os.getcwd())
    print("creating %s" % args.out)
    os.system("mkdir -p %s" % args.out)
    
    # if args.debug:
    #     os.system('sysctl -w net.mptcp.mptcp_debug=1')
    # else:
    #     os.system('sysctl -w net.mptcp.mptcp_debug=0')

    # os.system('sysctl -w net.mptcp.mptcp_enabled=1')

    # we don't have their RBS scheduler
    # os.system('sysctl -w net.mptcp.mptcp_scheduler=rbs')

    os.system('sysctl -w net.mptcp.mptcp_path_manager=fullmesh')

    # TODO use iperf command instead
    os.system('sysctl -w net.ipv4.tcp_rmem="400000 400000 400000"')
    
    if args.number_of_subflows:
        number_of_paths = [int(args.number_of_subflows)]
    else:
        number_of_paths = [1, 2, 3]
    

    v = vars(args)
    for paths in number_of_paths:
        print("Running experiments with ", paths, "subflows")
        runExperiment(paths, **v)
    
    # ProgMP.setDefaultScheduler("simple")
    # ProgMP.removeScheduler(schedulerName)
