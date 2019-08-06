#!/usr/bin/env nix-shell
#!nix-shell shell-mininet.nix -i python --show-trace

# Upon start, nix will try to fetch source it doesn't have
# => on the host you need to start nix-serve -p 8080
# in order to build up

# To clean everything run 'mn -c'

# python needs to read this
# -*- coding: utf-8 -*-
# but it will check just the first 2 lines :/ https://www.python.org/dev/peps/pep-0263/#defining-the-encoding

# https://gist.github.com/tovask/316f0dc855f2459042af403688590a7f
# https://github.com/SoonyangZhang/mininet-mptcp/tree/master/topology
# TODO add CAP_SYS_ADMIN to be able to run sysctl without


"""
derived from mininet_progmp_helper.py

"""

import os
import sys
import abc
# from time import sleep
import argparse
import signal
import subprocess
import tempfile
import shutil
import time  # for sleep
# from progmp import ProgMP

# python > 3.7
from dataclasses import dataclass, field

# from asym_link import AsymTCLink
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.util import pmonitor
from mininet.clean import cleanup as net_cleanup
from mininet.util import (quietRun, errRun, errFail, moveIntf, isShellBuiltin,
                           numCores, retry, mountCgroups )

import ipaddress as ip
# ipaddress.IPv4Network
# list(ip_network('192.0.2.0/29').hosts())
#
from builtins import super
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
# TODO remove
net  = None


SERVER_NAME = 'server'
CLIENT_NAME = 'client'
GW_NAME = 'gateway'

dataAmount = "1M"

# set to none for a random stream
FILE_TO_TRANSFER="test_file"
EBPF_DROPPER_BYTECODE="ebpf_dropper.o"

# is there a way to autodiscover ?
SCHEDULERS = ["default", "redundant", "roundrobin", "prevenant", "ecf" ]
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



# Problem we wanna solve here:
# class MPTCPIntf(Intf):
#     def setIP(self, *args, **kwargs):
#         pass
#     def runHook()
#         pass 
    # updateIP
    # updateAddr

def runHookOnInterface (intf, gateway, hook_filename="/home/teto/testbed/mptcp_up.sh"):
    """
    call a script to setup mptcp on a specific interface
    """
    # or pexec ?
    # seems like we can't pass a custom environment with 
    log.info("building MPTCP routing table for intf %s" % intf.name)

    #
    # gw = intf.link.node1 if intf.link.node2 == node else intf.link.node1
    env = os.environ
    env.update({
        "DEVICE_IFACE": intf.name,
        # "DHCP4_IP_ADDRESS": intf.IP(),
        "IP4_ADDRESS_0": intf.IP(),
        "DEVICE_IP_IFACE": intf.name,
        # (replace last number)
        "IP4_GATEWAY": gateway
    })
    cmd = "sh {} {action} {status}".format(hook_filename, action="fake", status="up")
    out, err, ret = node.pexec(cmd, env=env)
    assert ret == 0, err
    print(out)


# def runHookOnAllInterfaces (node, gateway=None, hook_filename="/home/teto/testbed/mptcp_up.sh"):
#     # would like to use NetworkManager's hooks to generate the MPTCP routing table
#     # on each host
#     # https://mail.gnome.org/archives/networkmanager-list/2016-April/msg00083.html
#     # https://mail.gnome.org/archives/networkmanager-list/2015-October/msg00020.html
#     for intf in node.intfList():
#         runHookOnInterface( )


# TODO look into
class Test(object):
    description = "default description"
    def __init__(self,
            name,
            # sysctl values
            aggr_dupack=0, aggr_rto=0,
            mptcp_scheduler=None,
            # mptcp_path_manager="fullmesh",
            tcp_timestamps=1,
            net=None,
            **kwargs
        ):
        self.name = name
        assert net
        self.net = net

        # a list of started processes one should check on error ?
        self._popens = []  # type: ignore
        self._out_folder = kwargs.get("out", "out")
        run_sysctl("net.ipv4.tcp_rmem", "{0} {0} {0}".format(4000,))
        run_sysctl("net.ipv4.tcp_no_metrics_save", 1)

        try:
            run_sysctl("net.mptcp.mptcp_aggressive_dupack", aggr_dupack)
            run_sysctl('net.mptcp.mptcp_aggressive_rto', aggr_rto)
        except Exception as e:
            print("WARNING %s" % e)

        # run_sysctl('net.mptcp.mptcp_path_manager', mptcp_path_manager)
        # run_sysctl("net.mptcp.mptcp_scheduler", mptcp_scheduler)
        # os.system('sysctl -w net.mptcp.mptcp_debug=0')
        # os.system('sysctl -w net.mptcp.mptcp_enabled=1')


        assert tcp_timestamps == None or tcp_timestamps < 5
        if tcp_timestamps is not None:
            run_sysctl('net.ipv4.tcp_timestamps', tcp_timestamps)
        # self.init(**kwargs)

    @staticmethod
    def init_subparser(parser):
        return parser

    # https://github.com/mininet/mininet/issues/857
    def start_daemon(self, node, cmd, **kwargs):

        print("starting daemon ?")
        logging.info("starting %s" % cmd)
        proc = node.popen(cmd, **kwargs)
        self._popens.append(proc)
        print("returncode", proc.returncode)

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

        # BACKUP solution
        # self.start_tcpdump(node, **kwargs)

        # The file "XX.pcapng" appears to have been cut short in the middle of a packet
        # https://stackoverflow.com/questions/13563523/the-capture-file-appears-to-have-been-cut-short-in-the-middle-of-a-packet-how
        pcap_filename = self._out("%s" % node, number_of_paths, ".pcapng")
        # pcap_filename = "/tmp/%s_%d_%s" % (node, number_of_paths, ".pcapng")
        cmd = ["tshark", "-g", "-i", "any", "-w", pcap_filename ]
        # cmd = ["dumpcap", "-i", "any", "-w", self._out("%s" % node, number_of_paths, ".pcapng") ]
        # node.cmd(cmd)
        self.start_daemon(node, cmd, shell=True, stderr=subprocess.PIPE)

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
        print("name = %r" % self.name)
        cmd = "iperf3 -s --json --logfile={logfile}".format(
                logfile=self._out("server_iperf", self.name, ".log")
            )

        # just as a security
        node.cmd("pkill -9 iperf")
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
        server = net.get(SERVER_NAME)
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

    def tearDown(self):
        logging.info("Tearing down")

        # restore some sysctl values ? like timestamp
        #
        for proc in self._popens:

            print("retcode ", proc.returncode)
            if proc.returncode is None:
                # proc.terminate()  # SIGTERM
                proc.send_signal(signal.SIGINT)  # C-C

            print("server retcode ", proc.returncode)
            if proc.returncode is None:
                proc.kill()  # SIGKILL
            # os.system('pkill -f \'tshark\'')

    @abc.abstractmethod
    def runExperiments(self, net, **kwargs):
        pass


class IperfTest(Test):
    """
    """

    def __init__(self, *args, **kwargs):
        """
        """
        super().__init__("Iperf", *args, **kwargs)
        self.description = "iperf test"

    def setup(self, net, **kwargs):
        print("iperf setup")
        check_reinject = True
        client = net.get('client')
        server = net.get('server')
        self.start_iperf_server(server)
        # subprocess.check_call("sudo insmod /home/teto/mptcp/build/net/mptcp/mptcp_prevenant.ko")
        # TODO temporary must have been prevenant here
        # run_sysctl("net.mptcp.mptcp_scheduler", "redundant")

        super().setup(net, **kwargs)

    def tearDown(self):
        logging.info("Tearing down")

        # CLI(net)
        super().tearDown()

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

    def runExperiments(self, **kwargs):
        """
        """
        # TODO
        run = 0
        client = self.net.get('client')

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


class IperfWithLostLinks(IperfTest):
    def __init__(self, *args, **kwargs):
        """
        """
        super().__init__("Iperf", *args, **kwargs)
        self.description = "iperf test with intermittent link"

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

        # TODO after some time cut some link
        # in seconds
        time.sleep(1)
        client.set_mptcp_behavior("", "off")
        # TODO cut the link off than reput it to on


class TlpTest(Test):
    """ Reproduce tail loss probe test"""

    def __init__(self, *args, **kwargs):
        super().__init__("Tlp", *args, **kwargs)

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

        # TODO temporary
        run_sysctl("net.mptcp.mptcp_scheduler", "redundant")

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

        # run_sysctl("net.ipv4.tcp_reordering", 3)

        super().setup(net, **kwargs)

    def runExperiments(self, net, **kwargs):
        client = net.get('client')

        runs = kwargs.get("runs", 1)
        # logging.info("Starting %d runs" % runs)

        def _runXPs(aggr_dupack):
            # run_sysctl("net.mptcp.mptcp_aggressive_dupack", aggr_dupack)
            print("Starting %d runs" % runs)
            for run in range(runs):
                elapsed_ms = self.run_xp(net, run, client, **kwargs)

                writer.writerow([int(aggr_dupack), elapsed_ms])

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
        server = net.get('server')
        # cmd = "wget http://%s/%s -O /dev/null"
        cmd = "curl -so /dev/null -w '%%{time_total}\n' http://%s/%s"
        # TODO use
        server.getIP()
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
        # elapsed_ms_str = re.sub("tcpdump.*", "", 
        #  client.cmd("curl -so /dev/null -w '%%{time_total}\n' http://%s/%s" % (topo.server_addr, filename)).replace("> ", ""))

        elapsed_ms_str = out[2:].rstrip()   # replace("> ", ""))
        # print("elapsed_ms_str", elapsed_ms_str)
        elapsed_ms = float(elapsed_ms_str)*1000

        print("elapsed_ms", elapsed_ms)

        # write avec ou sans dupack puis la valeur
        return elapsed_ms


# net = None

available_tests = {
    "dack": DackTest,
    "tlp": TlpTest,
    "iperf": IperfTest,
    "iperfAlt": IperfWithLostLinks,
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
    #          \\________ s2 ____________/


                     r1
                  /      \
           client         gateway  ---  server
                 \\      /
                     r2

         we use routers instead of switches to avoid OVS-related problems

    """

    def build(self, topo, number_of_paths=2, loss=0):

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
        # defaults to 0
        for i, params in enumerate(topo):
            name = self.getName(i)
            # print("NAME", name)
            s = self.addHost(name)

            # one good fast path
            # params.update({'use_tbf': True,
            #     'max_queue_size': 15000 # 10 paquets
            # })
            self.addLink(client, s, **params)
            link = self.addLink(s, gateway, loss=0, )
            # self.addLink(server, s, bw=100, delay="120ms", loss=float(loss))

        # dans frite, il l'ajoute en dernier
        link2 = self.addLink(server, gateway, )
        print("just for testing, link type = ", type(link2))

    def getName(self, idx):
        return 'r' + str(idx + 1)

    def set_mptcp_behavior(self, intf: str, status):
        """
        for a link, set status
        intf: interface name
        """

        assert status in ["on", "off", "backup"]
        # ip link set dev eth0 multipath backup
        msg = "ip link set dev %s multipath %s" % (intf, status)
        subprocess.check_call(msg)

    def network_generator(self, client, server):
        """
        Generates
        TODO extend later with
        """

        # gateway to server network
        gw2s = ip.IPv4Network("3.3.3.0/24")
        # host4.network /netmask/numaddresses
        # prefix = 24
        for i in range(2):

            # router between client and server
            r = self.getName(i)

            c2r = ip.IPv4Network("%d.0.0.0/%d" % (i, 24))
            s2r = ip.IPv4Network("%d.1.0.0/%d" % (i, 24))

            client.setIP(c2r[1], c2r.max_prefixlen, '%s-eth%d' % (client.name, i))
            server.setIP(s2r[1], s2r.max_prefixlen, '%s-eth%d' % (server.name, i))

            r.setIP(c2r[2], c2r.max_prefixlen, '%s-eth0' % r.name)
            r.setIP(s2r[2], s2r.max_prefixlen, '%s-eth0' % r.name)
            r.cmd('sysctl -w net.ipv4.ip_forward=1')

    def hook(self, network):
        client = network.get("client")
        server = network.get("server")
        self.network_generator(client, server)
    #     # ideally we could let NetworkManager handle this
    #     runHookOnInterfaces(client)
    #     runHookOnInterfaces(server)
    #     client.cmdPrint('ip route add default via 3.3.3.1 dev %s-eth0' % client.name)
    #     client.cmdPrint('ip route add default scope global nexthop via 3.3.3.1 dev %s-eth0' % client.name)

    # def hook(self, network):
    #     # old hook with a gateway in between: TODO reestablish

    #     client = network.get("client")
    #     server = network.get("server")
    #     r1 = network.get(self.getName(0))
    #     r2 = network.get(self.getName(1))
    #     gw = network.get("gateway")
    #     print("client.name=", client.name)

    #     r1.setIP('3.3.3.1', 24, '%s-eth0' % r1.name)
    #     r1.setIP('5.5.5.1', 24, '%s-eth1' % r1.name)

    #     r2.setIP('4.4.4.1', 24, '%s-eth0' % r2.name)
    #     r2.setIP('6.6.6.1', 24, '%s-eth1' % r2.name)

    #     gw.setIP('5.5.5.2', 24, '%s-eth0' % gw.name)
    #     gw.setIP('6.6.6.2', 24, '%s-eth1' % gw.name)
    #     gw.setIP('7.7.7.1', 24, '%s-eth2' % gw.name)

    #     server.setIP('7.7.7.7', 24, '%s-eth0' % server.name)
    #     server.cmd("ip route add default via %s" % "7.7.7.1")

    #     # Isn't that handled
    #     # client.cmd('ip rule add from 3.3.3.3 table 1')
    #     # client.cmd('ip rule add from 4.4.4.4 table 2')
    #     # client.cmd('ip route add 3.3.3.0/24 dev %s-eth0 scope link table 1' % client.name)
    #     # client.cmd('ip route add default from 3.3.3.3 via 3.3.3.1 dev %s-eth0 table 1' % client.name)
    #     # client.cmd('ip route add 4.4.4.0/24 dev %s-eth1 scope link table 2' % client.name)
    #     # client.cmd('ip route add 7.7.7.7 from 4.4.4.4 via 4.4.4.1 dev %s-eth1' % client.name)
    #     # client.cmd('ip route add default scope global nexthop via 3.3.3.1 dev %s-eth0' % client.name)

    #     # should already be shared
    #     r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    #     r2.cmd('sysctl -w net.ipv4.ip_forward=1')
    #     gw.cmd('sysctl -w net.ipv4.ip_forward=1')

    #     gw.cmd('ip route add 3.3.3.0/24 via 5.5.5.1 dev %s-eth0' % gw.name)
    #     gw.cmd('ip route add 4.4.4.0/24 via 6.6.6.1 dev %s-eth1' % gw.name)

    #     r1.cmd('ip route add 7.7.7.0/24 via 5.5.5.2 dev %s-eth1' % r1.name)
    #     r1.cmd('ip route add 4.4.4.0/24 via 5.5.5.2 dev %s-eth1' % r1.name)
    #     r1.cmd('ip route add 6.6.6.0/24 via 5.5.5.2 dev %s-eth1' % r1.name)

    #     r2.cmd('ip route add 7.7.7.0/24 via 6.6.6.2 dev %s-eth1' % r2.name)
    #     r2.cmd('ip route add 3.3.3.0/24 via 6.6.6.2 dev %s-eth1' % r2.name)
    #     r2.cmd('ip route add 5.5.5.0/24 via 6.6.6.2 dev %s-eth1' % r2.name)

    #     client.setIP('3.3.3.3', 24, '%s-eth0' % client.name)
    #     client.setIP('4.4.4.4', 24, '%s-eth1' % client.name)

    #     # ideally we could let NetworkManager handle this
    #     runHookOnInterfaces(client)
    #     runHookOnInterfaces(server)
    #     client.cmdPrint('ip route add default via 3.3.3.1 dev %s-eth0' % client.name)
    #     client.cmdPrint('ip route add default scope global nexthop via 3.3.3.1 dev %s-eth0' % client.name)
        # gw.cmdPrint('ip route add default scope global via 5.5.5.1 dev %s-eth0' % gw.name)

def attach_filter(node):
    """
    Attach ebpf drop filter to interface
    """
    ifname = node.name + "-eth2"

    logging.info("attaching filter to node %r" % node)

    node.cmd("tc qdisc del dev %s clsact" % ifname)

    node.cmd("tc qdisc add dev %s clsact" % ifname)
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
    # shouldn't let the user choose it, it's too dependant on the experiment
    parser.add_argument("-t", "--topo", choices=available_topologies.keys(),
                        help="Topology", default="asymetric")
    parser.add_argument("-c", "--capture", action="store_true",
                        help="capture packets", default=False)
    parser.add_argument("-s", "--scheduler", choices=SCHEDULERS,
                        help="Mptcp scheduler", default="default")
    parser.add_argument("-p", "--path-manager", choices=["fullmesh", "ndiffports", "netlink"],
                        help="Mptcp path manager", default="fullmesh")
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
    subparsers.required = True  # type: ignore

    for name, test in available_tests.items():
        subparser = subparsers.add_parser(name,  # parents=[pcap_parser],
                                          help=test.description)

        test.init_subparser(subparser)


    global args
    args, unknown_args = parser.parse_known_args()

    run_sysctl("net.mptcp.mptcp_scheduler", args.scheduler)
    run_sysctl('net.mptcp.mptcp_path_manager', args.path_manager)
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
        link=TCLink,
        host=MptcpHost,
        cleanup=True,
        # inNamespace=False,
        # build=
    )

    # installs IPs
    my_topo.hook(net)
    net.start()

    print("args dict")
    print(dargs)

    tempdir = tempfile.mkdtemp()

    # context manager clean up the folder upon exception
    # with tempfile.TemporaryDirectory() as tempdir:
    # tempdir.name
    # dargs["out"] = tempdir
    dargs.update(net=net)
    test = (available_tests.get(args.test_type))(**dargs)  # type: ignore
    # hack
    test._out_folder = tempdir
    logging.info("Launching test %s" % (args.test_type))

    try:
        client = net.get('client')
        server = net.get('server')

        # print("setup")
        test.setup(**dargs)

        # print("running xps")
        test.runExperiments(**dargs)

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except Exception as e:
        logging.exception("Exception triggered ")
    finally:
        test.tearDown()  # type: ignore

        # TODO reestablish
        # disabled in order to check for journald logs in /j
        # net_cleanup()

        print("Moving from %s to %s" % (tempdir, dargs["out"]))
        shutil.move(tempdir, dargs["out"])

    print("finished")

    # if args.debug:
    #     os.system('sysctl -w net.mptcp.mptcp_debug=1')
    # else:

    # if args.number_of_subflows:
    #     number_of_paths = [int(args.number_of_subflows)]
    # else:
    #     number_of_paths = [1, 2, 3]
