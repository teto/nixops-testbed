#!/usr/bin/env nix-shell 
#!nix-shell shell-mininet.nix -vv -i python --show-trace

# Upon start, nix will try to fetch source it doesn't have
# => on the host you need to start nix-serve -p 8080
# in order to build up 

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
import subprocess
# from progmp import ProgMP

from mininet.cli import CLI
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.util import pmonitor
import mininet
import functools
import logging

# look for __mptcp_reinject_data call
# [   63.813460] acking on fast path, looking for best sock 
# [   63.813461] Looking for fastest path

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

# try:

# todo make it so that we just have to unpack the parameter

dataAmount = "5M"

# can get parameters from 

topoWireLessHetero = [
    # parameters taken from "how hard can it be"
    { 'bw': 1, 'delay': "150ms", "loss": 1},
    # fast wifi
    { 'bw': 4, 'delay': "20ms", "loss": 20},
]

forward={ 'delay': "10ms"}
backward={ 'delay': "50ms"}

topoAsymetric = [
    # loss is in percoutage
    # 'delay': "20ms",
    { 'bw': 2,  "loss": 1, "max_queue_size":1000, "use_htb": True, 
        'params1': forward, 'params2': backward
    },
    { 'bw': 2, 'delay': "20ms", "loss": 20},
]

topoSinglePath = [
    { 'bw': 2, 'delay': "20ms", "loss": 0},
]

topo = topoSinglePath
# topo = topoWireLessHetero

# So with AsymTCLink one can use
# Link.__init__(self, node1, node2, port1=port1, port2=port2,
#               intfName1=intfName1, intfName2=intfName2,
#               cls1=TCIntf,
#               cls2=TCIntf,
#               addr1=addr1, addr2=addr2,
#               params1=par1,
#               params2=par2)



def _gout(out, *args):
    """ Use it to name files"""
    suffix = '_'.join(map(str, args))
    return os.path.join(out, suffix )

net = None

# clean sthg
def sigint_handler(signum, frame):
    print('Stop pressing the CTRL+C!')
    global net
    # net.stop()
    sys.exit(3)

# signal.signal(signal.SIGINT, sigint_handler)

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


class MptcpHost(mininet.net.Host):
    """
    mounts debugfs so that bcc works
    """
    def __init__(self, name, **kwargs):

        super(MptcpHost, self).__init__(name, **kwargs)
        res = self.cmd("mount -t debugfs none /sys/kernel/debug")
        print("HOST: res", res)


def runSingleExperiment(run, client, server, out, **kwargs):
    # in iperf3, the client sends the data so...

    _out = functools.partial(_gout, out)

    reinject_out = _out("check", run, ".csv")
    number_of_paths = kwargs.get('number_of_paths')
    # check_reinject = kwargs.get("")
    check_reinject = False
    print(reinject_out)

    # sendCmd returns immediately while cmd waits for output
    # res = client.cmd("ls /sys")
    # res = client.cmd("mount -t debugfs none /sys/kernel/debug")
    
    # print("mounting folder res :", res)
    # res = client.cmd("ls /root")
    # TODO problem is exec does not mount /sys/
    # res = client.cmd("ls /sys/kernel/debug/tracing/kprobe_events")
    # print("kprobe_events :", res)
    # res = client.cmd("cat /etc/mtab")
    # print("mtab :", res)
    try: 
        # iperf 3 version
        cmd = "iperf3 -s --json --logfile=%s" % (_out("server_iperf", number_of_paths, ".log"),)
        print("starting", cmd)
        server_iperf = server.popen(cmd)
        # out, err = server_iperf.communicate()
        # if err is not None:
        if server_iperf.returncode:
            print("Failed to run ", cmd)
            print("returned", server_iperf.returncode)
            # print(err)
            sys.exit(1)

        # server.cmd("iperf3 -s --json --logfile '%s' &" % _out("server_iperf", number_of_paths, ".log"))
        # server_iperf.poll()
        # TODO get results else it might get dirty
        with open(reinject_out, "w+") as fd:

            if check_reinject:
                print("launch check_reinject")
                client_check = client.popen(
                # client_check = subprocess.Popen(
                    ["/home/teto/testbed/check_opportunistic_reinject.py", "-j"], 
                    # might be a problem
                    stdout=fd,
                    universal_newlines=True,
                    bufsize=0
                )
                if client_check.returncode is not None:
                    print("failed to start ", client_check.returncode)
                # out, err = client_check.communicate()
                print("launched check_reinject with pid", client_check.pid)

            # if err is not None:
            #     print("Failed running with returncode=", client_check.returncode)
            #     print(err)
            #     break

            # assert err == 0

            cmd = "iperf3 -c {serverIP} -n {dataAmount} --json --logfile={logfile} ".format(
            # client.cmd("iperf3 -c {serverIP} -n {dataAmount} --logfile {logfile} ".format(
                serverIP=server.IP(),   # seems to work
                # serverIP="10.0.0.2",
                dataAmount=dataAmount,
                # paths=number_of_paths
                logfile=_out("client_iperf", "path", number_of_paths, "run", run, ".log")
            )

            # client.cmd(cmd)

            client_iperf = client.popen(cmd) #, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print("communicate for client iperf ")

            # out, err = client_iperf.communicate()
            # # wait for iperf to finish
            print("waiting for client iperf ")
            # print(out)
            # print(err)
            client_iperf.wait()
            # client.waitOutput()

            # if client_check.returncode:
            # print("out/errs=", out, err)
            # print("returncode=", client_iperf.returncode)
            # # client.cmd("kill %d" % (client_check.pid,))
            print("terminating client iperf")

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except Exception as e:
        logging.error("ERROR %s" % e)

    finally:
        print("finally")
        if client_iperf and client_iperf.returncode is None:
            client_iperf.terminate()
        if check_reinject and client_check.returncode is None:
            client_check.terminate()

        server_iperf.terminate()

def runExperiment(interactive, test, loss, **kwargs):

    _out = functools.partial(_gout, kwargs.get('out'))
    number_of_paths = kwargs.get('number_of_paths', 1)

    # using 
    global net
    net = Mininet(
        topo=StaticTopo(number_of_paths, loss), 
        # link=mininet.link.AsymTCLink,
        link=TCLink,
        host=MptcpHost
    )
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

# nohup tshark -i any -n -w out/server.pcap -f "tcp port 5201" 2>1 &
# todo use dumpcap instead
# dumpcap -q -w
        cmd = ["dumpcap", "-i", "any", "-w", _out("client", number_of_paths, ".pcapng") ]
        print("starting %s" % cmd)

        print("CWD=", os.getcwd())
        client_tshark = client.popen(cmd, universal_newlines=True,)
        # out, err = client_tshark.communicate()
        # print ( out, err)
        # print ( client_tshark.returncode)
        if client_tshark.returncode is not None:
            print("failed")

        cmd = ["dumpcap", "-i", "any", "-w", _out("server", number_of_paths, ".pcapng") ]
        server_tshark = server.popen(cmd, universal_newlines=True,)
        if server_tshark.returncode is not None:
            print("failed")

        # let tshark the time to setup itself
        os.system("sleep 5")
    

            
    # run_tests()
    # TODO move the loop to here
    for run in range(kwargs.get("runs", 1)):
        runSingleExperiment(run, client, server, **kwargs)

    if kwargs.get("capture"):
        print("killing dumpcap")
        print(" retcode ", client_tshark.returncode)
        client_tshark.terminate()
        print(" retcode ", client_tshark.returncode)
        server_tshark.terminate()
        # server_tshark.terminate()
        # os.system('pkill -f \'tshark\'')

        
    if interactive:
        print ("Experiment finished... enter exit to finish")
        CLI(net)
    
    # lets wait a moment
    sleep(3)
    # and ensure iperf is finished :-)
    # server.cmd("kill %d" % (server_iperf.pid,))
    # server_iperf.terminate()
    # os.system('pkill -f \'iperf\'')


    net.stop()
    # sleep(1)
  
if __name__ == '__main__':

    print("To clean run `mn -c`")
    print("You might want to run `nix-serve  -p 8080`")
    parser = argparse.ArgumentParser()
    # parser.add_argument("-f", "--file", help="The file which contains the scheduler", required=True)
    parser.add_argument("-n", "--number-of-paths", type=int, default=2, help="The number of subflows")
    parser.add_argument("-r", "--reinjections", type=bool, default=False, help="Check for reinjections")
    parser.add_argument("-d", "--debug", choices=['debug', 'info', 'error'], help="Running in debug mode", default='info')
    parser.add_argument("-t", "--test", choices=["iperf3-cdf"], help="test to run", default="iperf3-cdf")
    parser.add_argument("-c", "--capture", action="store_true", help="capture packets", default=False)
    parser.add_argument("-i", "--interactive", action="store_true", help="Waiting in command line interface", default=False)
    parser.add_argument("-l", "--loss", help="Loss rate (between 0 and 100", default=0)
    parser.add_argument("-o", "--out", action="store", default="out", help="out folder")
    parser.add_argument("--runs", action="store", type=int, default=1, help="Number of runs")
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
    
    # if args.number_of_subflows:
    #     number_of_paths = [int(args.number_of_subflows)]
    # else:
    #     number_of_paths = [1, 2, 3]
    

    v = vars(args)
    # for paths in number_of_paths:
    #     print("Running experiments with ", paths, "subflows")
    runExperiment(**v)
    
    # ProgMP.setDefaultScheduler("simple")
    # ProgMP.removeScheduler(schedulerName)
