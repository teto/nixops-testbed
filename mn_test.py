#!/usr/bin/env nix-shell 
#!nix-shell shell-mininet.nix -i python --show-trace

# Upon start, nix will try to fetch source it doesn't have
# => on the host you need to start nix-serve -p 8080
# in order to build up 

# when you have a problem with the store
# look at https://github.com/NixOS/nixops/issues/931
# mount -o remount,rw /nix/store
# chown -R root:root /nix/store

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
import abc
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
from mininet.clean import cleanup as net_cleanup
from mininet.util import ( quietRun, errRun, errFail, moveIntf, isShellBuiltin,
                           numCores, retry, mountCgroups )

# 
from builtins import super
# import future
import mininet
import functools
import logging


log = logging.getLogger(__name__)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
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
 # -n, --bytes n[KM]
net  = None

dataAmount = "1M"

# set to none for a random stream
FILE_TO_TRANSFER="test_file"
EBPF_DROPPER_BYTECODE="ebpf_dropper.o"

# can get parameters from 

topoWireLessHetero = [
    # parameters taken from "how hard can it be"
    { 'bw': 1, 'delay': "150ms", "loss": 1},
    # fast wifi
    { 'bw': 4, 'delay': "20ms", "loss": 20},
]

forward={ 'delay': "10ms", "loss": 10}
backward={ 'delay': "50ms"}

topoAsymetric = [
    # loss is in percoutage
    # 'delay': "20ms",
    { 'bw': 2, "max_queue_size":1000, "use_htb": True, 
        'params1': forward, 'params2': backward
    },
    # { 'bw': 2, 'delay': "20ms", "loss": 20},
    { 'bw': 2, 'delay': "20ms", "loss": 0},
]

topoSymetric = [
    { 'bw': 1, 'delay': "20ms", "loss": 0},
    { 'bw': 1, 'delay': "20ms", "loss": 0},
]

# jitter is for example " '5ms"
# update returns None which is BAD
# topoSymetricJitter = list(map(lambda x : x.update(jitter='5ms'), topoSymetric))
topoSymetricJitter = [
    { 'bw': 1, 'delay': "20ms", "loss": 0, "jitter":'5ms'},
    { 'bw': 1, 'delay': "20ms", "loss": 0, "jitter":'5ms'},
]


topoDack = [
    { 'bw': 1, 'delay': "10ms", "loss": 10},
    { 'bw': 1, 'delay': "20ms", "loss": 0},
]



topoSinglePath = [
    { 'bw': 2,  "loss": 0, 
        'params1': forward, 'params2': backward,
    },
]

# topo = topoSinglePath
# topo = topoWireLessHetero
# topo = topoSymetric
topo = topoAsymetric

# So with AsymTCLink one can use
# Link.__init__(self, node1, node2, port1=port1, port2=port2,
#               intfName1=intfName1, intfName2=intfName2,
#               cls1=TCIntf,
#               cls2=TCIntf,
#               addr1=addr1, addr2=addr2,
#               params1=par1,
#               params2=par2)

available_topologies = {
    "singlePath": topoSinglePath,
    "wirelessHetero": topoWireLessHetero,
    "symetric": topoSymetric,
    "asymetric":  topoAsymetric,
    "dack":  topoDack,
    "3paths_symetric_jitter": topoSymetricJitter,
}


# we don't have their RBS scheduler
# os.system('sysctl -w net.mptcp.mptcp_scheduler=rbs')
def run_sysctl(key, value, **popenargs):
    # todo parse output of check_output instead
    # subprocess.check_call(["sysctl","-w","%s=%s" % (key, value)], shell=True)
    subprocess.check_call(["sysctl -w %s='%s'" % (key, value)], shell=True)


class Test(object):
    def __init__(self, name,
            # sysctl values
            aggr_dupack=0, aggr_rto=0,
            mptcp_scheduler="default",
            mptcp_path_manager="fullmesh",
            tcp_timestamps=3,
            **kwargs
        ):
        self.name = name
        # a list of started processes one should check on error ?
        self._popens = []  # type: ignore
        self._out_folder = kwargs.get("out", "out")
        run_sysctl("net.ipv4.tcp_rmem", "{0} {0} {0}".format(4000,))
        run_sysctl("net.ipv4.tcp_no_metrics_save", 1)
        # 
        try:
            run_sysctl("net.mptcp.mptcp_aggressive_dupack", aggr_dupack)
            run_sysctl('net.mptcp.mptcp_aggressive_rto', aggr_rto)
        except Exception as e:
            print("WARNING %s" % e)

        run_sysctl('net.mptcp.mptcp_path_manager', mptcp_path_manager)
        run_sysctl("net.mptcp.mptcp_scheduler", mptcp_scheduler)
        # os.system('sysctl -w net.mptcp.mptcp_debug=0')
        # os.system('sysctl -w net.mptcp.mptcp_enabled=1')


        assert tcp_timestamps == None or tcp_timestamps < 5
        if tcp_timestamps is not None:
            run_sysctl('net.ipv4.tcp_timestamps', tcp_timestamps)
        # self.init(**kwargs)

    @staticmethod
    def init_subparser(parser):
        return parser


    def start_daemon(self, node, cmd):

        print("starting daemon ?")
        logging.info("starting %s" % cmd)
        proc = node.popen(cmd)

        if proc.poll():
            print("Failed to run ", cmd)
            print("returned", proc.returncode)
            # print(err)
            sys.exit(1)


    def start_tcpdump(self, node, **kwargs):
        cmd = ["tcpdump", "-i", "any", "-w", self._out("%s" % node, number_of_paths, ".pcapng") ]
        self.start_daemon(node, cmd)


    def start_tshark(self, node, **kwargs):
        # nohup tshark -i any -n -w out/server.pcap -f "tcp port 5201" 2>1 &
        # todo use dumpcap instead
        # dumpcap -q -w
        # for tcpdump use -U
        # client.cmd(cmd,)
        self.start_tcpdump(node, **kwargs)

    # def start_iperf_client(self, ):
    #     cmd = "iperf3 -c {serverIP} {dataAmount} --json --logfile={logfile} {fromFile}".format(
    #         serverIP=server.IP(),   # seems to work
    #         # serverIP="10.0.0.2",
    #         # dataAmount="-n " + dataAmount if FILE_TO_TRANSFER is not None else "",
    #         dataAmount="",
    #         # Generated by gen_file
    #         # must finish with a string "DROPME" so that ebpfdropper can recognize and 
    #         # drop it
    #         fromFile="-F %s" % (FILE_TO_TRANSFER) if FILE_TO_TRANSFER else "",
    #         # fromFile=args.file "",
    #         # paths=number_of_paths
    #         logfile=self._out("client_iperf", "path", number_of_paths, "run", run, ".log")
    #     )

    def start_iperf_server(self, node, **kwargs):
        # iperf 3 version
        # "Normally, the test data is sent from the client to the server,"
        # number_of_paths, 
        cmd = "iperf3 -s --json --logfile=%s" % (self._out("server_iperf", self.name, ".log"),)

        self.start_daemon(node, cmd)

    def start_webfs(self, node, **kwargs):
        # -i 7.7.7.7 
        # -s => some text in syslog
        # -R <dir> set document root to DIR
        print("startwebfs")
        cmd = "webfsd -s -R /home/teto/testbed -d"
        self.start_daemon(node, cmd)

    # setup as an abstract to implement
    def setup(self, net, **kwargs):
        client = net.get('client')
        server = net.get('server')
        gateway = net.get('gateway')
        # gateway.cmd('sysctl -w net.ipv4.ip_forward=1')

        if kwargs.get('interactive'):
            print("Experiment is ready to start... enter exit to start")
            print("client ping 10.0.0.2 -c 4")
            res = None
            res = CLI(net)
            if res:
                net.stop()
                sys.exit(1)

            print("RESULT %r" % (res))
        

        if kwargs.get("capture"):
            print("Capturing packets...")
            print('tshark -r out/client_2.pcap -z "conv,mptcp"')

            self.start_tshark(client)
            self.start_tshark(server)

            os.system("sleep 5")

    def _out(self, *args):
        """ Use it to name files"""
        suffix = '_'.join(map(str, args))
        return os.path.join(self._out_folder, suffix )

    # def parser():
        # 
        # argparse.ArgumentParser

    def tearDown(self):
        logging.info("Tearing down")

        # restore some sysctl values ? like timestamp
        # 
        for proc in self._popens:

            print("retcode ", proc.returncode)
            if proc.returncode is None:
                proc.terminate()

            print("server retcode ", proc.returncode)
            # os.system('pkill -f \'tshark\'')

    # def run_xp(self, run):
    #     pass

    # @abc.abstractmethod
    # def run_xp(self, net, run, **kwargs):
    #     """
    #     """
    #     pass


    # out, err, exit = errFail(cmd)
    # print("process output: %s", out)

    @abc.abstractmethod
    def runExperiments(self, net, **kwargs):
        
        pass
        # for run in range(args.get("runs", 1)):
        #     test.run_xp(net, run, **args)




class PrevenantTest(Test):
    """
    """
    def __init__(self, *args, **kwargs):
        """
        """
        super().__init__(self, "Prevenant", *args)

    def setup(self, net, **kwargs ):
        print("prevent setup")
        check_reinject = True
        client = net.get('client')
        server = net.get('server')
        self.start_iperf_server(server)
        # subprocess.check_call("sudo insmod /home/teto/mptcp/build/net/mptcp/mptcp_prevenant.ko")
        # TODO temporary must have been prevenant here
        run_sysctl("net.mptcp.mptcp_scheduler", "redundant")

        super().setup(net, **kwargs)

    def tearDown(self):
        logging.info("Tearing down")

    # def runExperiments(self, net, **kwargs):
    #     """
    #     """
    #     # TODO
    #     run = 0
    #     reinject_out = self._out("check", run, ".csv")
    #     # TODO temporary for testing 
    #     reinject_out = os.devnull;
    #     number_of_paths = kwargs.get('number_of_paths')
    #     # check_reinject = kwargs.get("")
    #     print("reinject_out=", reinject_out)
    #     # check_reinject = True
    #     with open(reinject_out, "w+") as fd:

    #         # print("launch check_reinject")
    #         # cmd =["/home/teto/testbed/check_opportunistic_reinject.py", "-j"], 
    #             # might be a problem
    #             # stdout=fd, universal_newlines=True, bufsize=0

    #         # or server ?
    #         self.start_daemon(client, cmd)
    #         self.start_iperf_server(server, cmd)

    #         # need to generate a situation with frequent retransmissions
    #         for run in range(args.get("runs", 1)):
    #             self.run_xp(net, run, **args)

    def runExperiments(self, net, **kwargs):
        """
        """
        # TODO
        run = 0
        client = net.get('client')

        # need to generate a situation with frequent retransmissions
        for run in range(kwargs.get("runs", 1)):
            self.run_xp(client, run, **kwargs)


    def run_xp(self, client, run, **kwargs):
        # in iperf3, the client sends the data so...
        # self.start_iperf_client(client,  )
        # client = dataAmount
        cmd = "iperf3 -c {serverIP} {dataAmount} --json --logfile={logfile} {fromFile}".format(
            serverIP=server.IP(),   # seems to work "7.7.7.7"
            # dataAmount="-n " + dataAmount if FILE_TO_TRANSFER is not None else "",
            dataAmount="",
            # Generated by gen_file
            # must finish with a string "DROPME" so that ebpfdropper can recognize and 
            # drop it
            fromFile="-F %s" % (FILE_TO_TRANSFER) if FILE_TO_TRANSFER else "",
            # fromFile=args.file "",
            # paths=number_of_paths
            logfile=self._out("client_iperf", "path", number_of_paths, "run", run, ".log")
        )
        client.cmdPrint(cmd)





class TlpTest(Test):
    """ Reproduce tail loss probe test"""
    def __init__(self, *args, **kwargs):
        super().__init__("Tlp",  *args, **kwargs)

    # Tail loss probe
    # def init(self, *args):
    #     super().__init__("Tlp", *args)

    def setup(self, net):
        gateway = net.get('gateway')
        # if kwargs.get("ebpfdrop"):
        print("attach_filter %r" % gateway)
        # TODO pass ifname ?

        attach_filter(gateway)


    # def runExperiments(self, net, **kwargs):
    #     for run in range(args.get("runs", 1)):
    #         test.run_xp(net, run, **args)




# class ReinjectionTest(Test):

#     def __init__(self, *args, **kwargs):
#         super(ReinjectionTest, self).__init__("Reinjection", **kwargs)

#     @staticmethod
#     def init_subparser(parser):
#         parser.add_argument("fileToDownload", action="store", 
#             type=str, default=FILE_TO_TRANSFER, help="filename to download")
#         return parser

#     def setup(self, net, **kwargs):
#         logging.info("setup network")
#         server = net.get('server')
#         gateway = net.get('gateway')

#         self.start_webfs(server)

#         super().setup(net, **kwargs)

#     def runExperiments(self, net, **kwargs):
#         client = net.get('client')

#         _runXPs(1)
#         _runXPs(0)

#     def run_xp(self, net, run, client, fileToDownload, **kwargs):
#         """
#         Start an http server, download a file and saves the transfer time into a csv
#         """
#         gateway = net.get('gateway')
#         proc = self.start_tshark(client)
#         # cmd = "wget http://%s/%s -O /dev/null" 
#         cmd = "curl -so /dev/null -w '%%{time_total}\n' http://%s/%s"
#         cmd = cmd % ("7.7.7.7:8000", fileToDownload)
#         print("starting")
#         out = client.cmdPrint(cmd)
#         print(out)
#         proc.terminate()
#         # write avec ou sans dupack puis la valeur
#         return elapsed_ms

class DackTest(Test):

    def __init__(self, *args, **kwargs):
        super(DackTest, self).__init__("Dack", **kwargs)

    @staticmethod
    def init_subparser(parser):
        parser.add_argument("fileToDownload", action="store", 
            type=str, default=FILE_TO_TRANSFER, help="filename to download")
        parser.add_argument("--reordering", action="store", type=int, default=3, 
            help="number of dupack to consider a fast retransmit")
        return parser

    def setup(self, net, **kwargs):
        logging.info("setup network")
        server = net.get('server')
        gateway = net.get('gateway')

        self.start_webfs(server)

        run_sysctl("net.ipv4.tcp_reordering", 3)

        super().setup(net, **kwargs)

    def runExperiments(self, net, **kwargs):
        client = net.get('client')
        
        runs = kwargs.get("runs", 1)
        # logging.info("Starting %d runs" % runs)
        def _runXPs(aggr_dupack):
            run_sysctl("net.mptcp.mptcp_aggressive_dupack", aggr_dupack)
            print("Starting %d runs" % runs)
            for run in range(runs):
                elapsed_ms = self.run_xp(net, run, client, **kwargs)

                writer.writerow([ int(aggr_dupack), elapsed_ms])


        import csv
        with open(self._out('dl_times', '.csv'), 'wb') as csvfile:
            writer = csv.writer(csvfile, 
                    # delimiter=' ',
                    # quotechar='|', quoting=csv.QUOTE_MINIMAL
            )

            writer.writerow(["aggr", "delay"])
            _runXPs(1)
            _runXPs(0)



    def run_xp(self, net, run, client, fileToDownload, **kwargs):
        """
        Start an http server, download a file and saves the transfer time into a csv
        """
        gateway = net.get('gateway')
        # cmd = "wget http://%s/%s -O /dev/null" 
        cmd = "curl -so /dev/null -w '%%{time_total}\n' http://%s/%s"
        cmd = cmd % ("7.7.7.7:8000", fileToDownload)
        #     import re
        # elapsed_ms_str = re.sub("tcpdump.*", "", client.cmd( % (topo.server_addr, filename)).replace("> ", ""))
        # elapsed_ms = float(elapsed_ms_str)*1000

        # out = client.monitor(timeoutms=2000)
        # log.info(cmd)
        # CLI(net)
        print("starting")
        out = client.cmdPrint(cmd)
        print(out)
        # import re
        # elapsed_ms_str = re.sub("tcpdump.*", "", client.cmd("curl -so /dev/null -w '%%{time_total}\n' http://%s/%s" % (topo.server_addr, filename)).replace("> ", ""))

        elapsed_ms_str = out[2:].rstrip()   # replace("> ", ""))
        # print("elapsed_ms_str", elapsed_ms_str)
        elapsed_ms = float(elapsed_ms_str)*1000

        print("elapsed_ms", elapsed_ms)

        # write avec ou sans dupack puis la valeur
        return elapsed_ms




# net = None

available_tests = {
    "dack":    DackTest,
    "tlp":     TlpTest,
    "prevenant": PrevenantTest,
    # "reinjection": ReinjectionTest,
}

# clean sthg
def sigint_handler(signum, frame):
    print('Stop pressing the CTRL+C!')
    # global net
    # net.stop()

    net_cleanup()
    sys.exit(3)

# signal.signal(signal.SIGINT, sigint_handler)

class StaticTopo(Topo):
    """
    Simple topo with 2 hosts and 'number_of_paths' paths
    
    # server --g----- s1 ----------- client
    #          \________ s2 ____________/

        
                     r1
                  /      \
           client         r3  ---  server
                  \      /
                     r2
        
         we use routers instead of switches to avoid OVS-related problems
        
    """
    def build(self, topo, number_of_paths = 2, loss = 0):

        global args

        # If you need per-host private directories, you can specify them as options to Host, for example:
        # h = Host( 'h1', privateDirs=[ '/some/directory' ] )
        client = self.addHost('client')
        server = self.addHost('server')
        # gateway = self.addHost('gateway')
        gateway = self.addHost('gateway')

        
        # everything should go through this switch
        # since we need to cancel only the first paquet

        # only one link between the 2
        # https://github.com/mininet/mininet/issues/823

        # for r, cmd in [(self.r3, 'tc filter add dev  r3-eth2 ingress bpf obj test_ebpf_tc.o section action direct-action')]:
        for i, params in enumerate(topo):
            name = 'r' + str(i + 1)
            # print("NAME", name)
            s = self.addHost(name)

            # one good fast path
            # params.update({'use_tbf': True,
            #     'max_queue_size': 15000 # 10 paquets
            # })
            self.addLink(client, s, **params)
            link = self.addLink(s, gateway, loss=0, )
            # add route
            # self.r3.cmd("ip route add {dest} via 5.5.5.1 dev %s-eth0".format(
            #     dest=3.3.3.0/24))
            # % self.r3_name)
            # print("link %r" % link)
            # self.addLink(server, s, bw=100, delay="120ms", loss=float(loss))


        # dans frite, il l'ajoute en dernier
        link2 = self.addLink(server, gateway, )
        print("just for testing, link type = ", type(link2))


    def hook(self, network):

        client = network.get("client")
        server = network.get("server")
        r1 = network.get("r1")
        r2 = network.get("r2")
        r3 = network.get("gateway")

        client.setIP('3.3.3.3', 24, '%s-eth0' % client.name)
        client.setIP('4.4.4.4', 24, '%s-eth1' % client.name)
        r1.setIP('3.3.3.1', 24, '%s-eth0' % r1.name)
        r1.setIP('5.5.5.1', 24, '%s-eth1' % r1.name)

        r2.setIP('4.4.4.1', 24, '%s-eth0' % r2.name)
        r2.setIP('6.6.6.1', 24, '%s-eth1' % r2.name)

        r3.setIP('5.5.5.2', 24, '%s-eth0' % r3.name)
        r3.setIP('6.6.6.2', 24, '%s-eth1' % r3.name)
        r3.setIP('7.7.7.1', 24, '%s-eth2' % r3.name)
        server.setIP('7.7.7.7', 24, '%s-eth0' % server.name)

        client.cmd('ip rule add from 3.3.3.3 table 1')
        client.cmd('ip rule add from 4.4.4.4 table 2')
        client.cmd('ip route add 3.3.3.0/24 dev %s-eth0 scope link table 1' % client.name)
        client.cmd('ip route add default from 3.3.3.3 via 3.3.3.1 dev %s-eth0 table 1' % client.name)
        client.cmd('ip route add 4.4.4.0/24 dev %s-eth1 scope link table 2' % client.name)
        client.cmd('ip route add 7.7.7.7 from 4.4.4.4 via 4.4.4.1 dev %s-eth1' % client.name)
        client.cmd('ip route add default scope global nexthop via 3.3.3.1 dev %s-eth0' % client.name)

        server.cmd('ip route add default via 7.7.7.1')

        # should already be shared
        r1.cmd('sysctl -w net.ipv4.ip_forward=1')
        r2.cmd('sysctl -w net.ipv4.ip_forward=1')
        r3.cmd('sysctl -w net.ipv4.ip_forward=1')

        r3.cmd('ip route add 3.3.3.0/24 via 5.5.5.1 dev %s-eth0' % r3.name)
        r3.cmd('ip route add 4.4.4.0/24 via 6.6.6.1 dev %s-eth1' % r3.name)
        r1.cmd('ip route add 7.7.7.0/24 via 5.5.5.2 dev %s-eth1' % r1.name)
        r1.cmd('ip route add 4.4.4.0/24 via 5.5.5.2 dev %s-eth1' % r1.name)
        r1.cmd('ip route add 6.6.6.0/24 via 5.5.5.2 dev %s-eth1' % r1.name)

        r2.cmd('ip route add 7.7.7.0/24 via 6.6.6.2 dev %s-eth1' % r2.name)
        r2.cmd('ip route add 3.3.3.0/24 via 6.6.6.2 dev %s-eth1' % r2.name)
        r2.cmd('ip route add 5.5.5.0/24 via 6.6.6.2 dev %s-eth1' % r2.name)


def attach_filter(node):
    """
    Attach ebpf drop filter to interface
    """
    ifname = node.name + "-eth2"

    logging.info("attaching filter to node %r" % node)

    node.cmd("tc qdisc del dev %s clsact" % ifname)

    node.cmd("tc qdisc add dev %s clsact" % ifname )
    node.cmd("rm bpf_fifo; mkfifo bpf_fifo")
    # this is when
    node.cmd("rm /tmp/bpf")
    node.cmd('tc exec bpf import /tmp/bpf run sh read_map.sh > /tmp/out_bpf &')

    node.cmd('tc qdisc add dev %s clsact' % ifname)
    cmd = "tc filter add dev {ifname} ingress bpf obj {bytecode} section action direct-action".format(
            ifname=ifname,
            bytecode=EBPF_DROPPER_BYTECODE)

    # to see the filters you have to run
    # tc filter show dev gateway-eth2 ingress

    # print cmd
    out = node.cmd(cmd)
    if "File exists" in out:
        cmd = cmd.replace("add", "change")
        print("exists")
        out = node.cmd(cmd)

    if out:
        print(cmd)
        print(out)


class MptcpHost(mininet.net.Host):
    """
    mounts debugfs so that bcc works
    """
    def __init__(self, name, **kwargs):

        super(MptcpHost, self).__init__(name, **kwargs)
        res = self.cmd("mount -t debugfs none /sys/kernel/debug")
        res = self.cmd("mount -t bpf none /sys/fs/bpf/")
        print("HOST: res", res)



  
if __name__ == '__main__':

    # 
    print("To clean run `mn -c`")
    print("You might want to run `nix-serve  -p 8080`")
    print("sudo insmod /home/teto/mptcp/build/net/mptcp/mptcp_prevenant.ko")

    parser = argparse.ArgumentParser()
    # todo move to test
    # parser.add_argument("--file", help="The file to download",)
    parser.add_argument("-n", "--number-of-paths", type=int, default=2, 
        help="The number of subflows")
    parser.add_argument("-r", "--reinjections", type=bool, default=False,
        help="Check for reinjections")
    parser.add_argument("-d", "--debug", choices=['debug', 'info', 'error'],
        help="Running in debug mode", default='info')
    parser.add_argument("-t", "--topo", choices=available_topologies.keys(),
        help="Topology", default="asymetric")
    parser.add_argument("-c", "--capture", action="store_true", 
        help="capture packets", default=False)
    parser.add_argument("-i", "--interactive", action="store_true",
        help="Waiting in command line interface", default=False)
    # parser.add_argument("-l", "--loss", help="Loss rate (between 0 and 100", default=0)
    parser.add_argument("-o", "--out", action="store", default="out", help="out folder")
    parser.add_argument("--runs", action="store", type=int, default=1, help="Number of runs")
    # parser.add_argument("-f", "--ebpfdrop", action="store_true", default=False,
        # help="Wether to attach our filter")
    # parser.add_argument("test", choices=list(map(lambda x: x.__name__, available_tests)), action="store", 
        # help="Test to run")

    subparsers = parser.add_subparsers(dest="test_type", title="Subparsers",
        help='sub-command help')

    for name, test in available_tests.items():
        # 
        subparser = subparsers.add_parser(name,  # parents=[pcap_parser],
            help='Converts pcap to a csv file')

        test.init_subparser(subparser)


    global args
    args, unknown_args = parser.parse_known_args()
    dargs = vars(args)

    setLogLevel(args.debug)
    # args.debug
    logging.getLogger().setLevel(logging.DEBUG)

    print("CWD=", os.getcwd())
    print("creating %s" % args.out)
    subprocess.check_call("mkdir -p %s" % args.out, shell=True)
    
    # _out = functools.partial(_gout, kwargs.get('out'))
    number_of_paths = dargs.get('number_of_paths', 1)

    # using 
    topo = available_topologies[args.topo]

    logging.info("Selected topology %s" % (args.topo))
    my_topo = StaticTopo(topo=topo, number_of_paths=number_of_paths, )
    net = Mininet(
        topo=my_topo,
        link=mininet.link.AsymTCLink,
        host=MptcpHost
    )

    # installs IPs
    my_topo.hook(net)
    net.start()

    test = (available_tests.get(args.test_type))(**dargs)  # type: ignore
    logging.info("Launching test %s" % (args.test_type))

    try:
        client = net.get('client')
        server = net.get('server')

        # print("setup")
        test.setup(net, **dargs)

        # print("running xps")
        test.runExperiments(net, **dargs)

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except Exception as e:
        logging.exception("Exception triggered ")
    finally:
        test.tearDown()
        net_cleanup()

    print("finished")

    # if args.debug:
    #     os.system('sysctl -w net.mptcp.mptcp_debug=1')
    # else:


    # if args.number_of_subflows:
    #     number_of_paths = [int(args.number_of_subflows)]
    # else:
    #     number_of_paths = [1, 2, 3]
    
