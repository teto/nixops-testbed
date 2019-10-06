#!/usr/bin/env nix-shell
#!nix-shell shell-mininet.nix -i python --show-trace

# TODO load config via configparser
# TODO test https://stackoverflow.com/questions/46537736/mininet-cant-ping-across-2-routers
# Upon start, nix will try to fetch source it doesn't have
# => on the host you need to start nix-serve -p 8080
# in order to build up

# To clean everything run 'mn -c'

# python needs to read this
# -*- coding: utf-8 -*-
# but it will check just the first 2 lines:
# https://www.python.org/dev/peps/pep-0263/#defining-the-encoding

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
import copy
from typing import Sequence, List, Dict

# python > 3.7
from dataclasses import dataclass, field

import mininet

# from asym_link import AsymTCLink
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.util import pmonitor
from mininet.clean import cleanup as net_cleanup
from mininet.util import (quietRun, errRun, errFail, moveIntf, isShellBuiltin,
                          numCores, retry, mountCgroups)

import ipaddress as ip
from builtins import super
import functools
import logging
import configparser


log = logging.getLogger(__name__)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)


# todo make it so that we just have to unpack the parameter
# -n, --bytes n[KM]
# TODO remove
net = None

PATH_MANAGER_FILENAME = "mptcp-pm.log"
# https://stackoverflow.com/questions/46537736/mininet-cant-ping-across-2-routers

SERVER_NAME = 'server'
CLIENT_NAME = 'client'
GW_NAME = 'gateway'

dataAmount = "1M"

# set to none for a random stream
FILE_TO_TRANSFER = "test_file"
EBPF_DROPPER_BYTECODE = "ebpf_dropper.o"

# is there a way to autodiscover ?
SCHEDULERS = ["default", "redundant", "roundrobin", "prevenant", "ecf"]
# can get parameters from

# @dataclass
# class LinkSetting:
#     bw: int
#     delay: str
#     loss: str


topoWireLessHetero = [
    # parameters taken from "how hard can it be"
    {'bw': 1, 'delay': "150ms", "loss": 1},
    # fast wifi
    {'bw': 4, 'delay': "20ms", "loss": 20},
]

forward = {'delay': "10ms", "loss": 10}
backward = {'delay': "50ms"}

topoAsymetric = [
    # loss is in percoutage 'delay': "20ms",
    # {'bw': 2, "max_queue_size": 1000, "use_htb": True,
    #     'params1': forward, 'params2': backward
    #  },
    {'bw': 2, 'delay': "20ms", "loss": 1},
]

topoSymetric = [
    {'bw': 1, 'delay': "20ms", "loss": 0},
    {'bw': 1, 'delay': "20ms", "loss": 0},
]

# jitter is for example " '5ms"
# update returns None which is BAD
# topoSymetricJitter = list(map(lambda x : x.update(jitter='5ms'), topoSymetric))
topoSymetricJitter = [
    {'bw': 1, 'delay': "20ms", "loss": 0, "jitter": '5ms'},
    {'bw': 1, 'delay': "20ms", "loss": 0, "jitter": '5ms'},
]


topoDack = [
    {'bw': 1, 'delay': "10ms", "loss": 10},
    {'bw': 1, 'delay': "20ms", "loss": 0},
]


topoSinglePath = [
    {'bw': 2, "loss": 0,
        'params1': forward, 'params2': backward,
     },
]


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
    "asymetric": topoAsymetric,
    "dack": topoDack,
    "3paths_symetric_jitter": topoSymetricJitter,
}


# we don't have their RBS scheduler
# os.system('sysctl -w net.mptcp.mptcp_scheduler=rbs')
def run_sysctl(key, value, **popenargs):
    '''
    you can use -e to ignore errors
    sysctl: setting key "net.mptcp.mptcp_path_manager": No such file or directory
    '''
    # todo parse output of check_output instead
    # subprocess.check_call(["sysctl","-w","%s=%s" % (key, value)], shell=True)
    # -q removes stdout content so that we keep only stderr to check
    # for invalid modules
    cmd = [f"sysctl -wq {key}='{value}'"]
    log.debug("Running command:\n%s", cmd)
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    if out != b'':
        # defined in https://kite.com/python/docs/subprocess.CalledProcessError
        # raise subprocess.CalledProcessError(0, cmd, out.decode())
        raise Exception("Error happened %s" % out.decode())


class LinuxRouter(Node):
    '''A Node with IP forwarding enabled.'''

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmdPrint('sysctl net.ipv4.ip_forward=1')
        self.cmdPrint('sysctl net.ipv4.conf.all.rp_filter=0')

    def terminate(self):
        # self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


# TODO should go in a custom interface MPTCPIntf
def runMptcpHookOnInterface(intf, gateway, hook_filename="mptcp_up.sh"):
    """
    call a script to setup mptcp on a specific interface
    """
    # or pexec ?
    # seems like we can't pass a custom environment with
    log.debug("Running hook %s" % hook_filename)
    log.info("building MPTCP routing table for intf %s", intf.name)
    # log.debug("running hook on intf"

    env = copy.copy(os.environ)

    # mimic the static path
    extraEnv = {
        "DEVICE_IFACE": intf.name,
        # "DHCP4_IP_ADDRESS": intf.IP(),
        "IP4_GATEWAY": gateway,
        "IP4_ADDRESS_0": intf.IP(),
        "DEVICE_IP_IFACE": intf.name,
    }
    print("Faking variables: %r" % extraEnv)
    env.update(extraEnv)
    # only if needed
    # # (replace last number)
    cmd = "sh {} {action} {status}".format(hook_filename, action="fake", status="up")
    # intf.cmd
    # printCmd instead ?
    out, err, ret = intf.node.pexec(cmd, env=env)
    assert ret == 0, err
    print(out)

# TODO use a dataclass instead ?
# MPTCP vs TCP tests
# @dataclass
class Test(object):
    # name: str
    description = "default description"

    def __init__(self,
                 name,
                 topo,
                 # sysctl values
                 mptcp=True,
                 aggr_dupack=0, aggr_rto=0,
                 mptcp_scheduler=None,
                 mptcp_path_manager=None,
                 tcp_timestamps=0,

                 **kwargs
                 ):
        self.name = name
        self.topo = topo
        # tempdir = tempfile.mkdtemp()

        # TODO reestablish
        # disabled in order to check for journald logs in /j
        # net_cleanup()

        self.out = tempfile.mkdtemp()
        self.description = "Please set the description"
        print("MATT topo %r" % self.topo)

        if mptcp:
            # run_sysctl("net.mptcp.mptcp_aggressive_dupack", aggr_dupack)
            # run_sysctl('net.mptcp.mptcp_aggressive_rto', aggr_rto)

            if mptcp_path_manager is not None:
                run_sysctl('net.mptcp.mptcp_path_manager', mptcp_path_manager)

            if mptcp_scheduler is not None:
                run_sysctl("net.mptcp.mptcp_scheduler", mptcp_scheduler)

            # os.system('sysctl -w net.mptcp.mptcp_debug=0')
            # os.system('sysctl -w net.mptcp.mptcp_enabled=1')

            run_sysctl("net.mptcp.mptcp_enabled", 1)

        # a list of started processes one should check on error ?
        self._popens = []  # type: ignore

        # TODO set wmem as well
        # in bytes
        # the minimum is SK_MEM_QUANTUM (4096), default 16*1024;
        # limit = 4096     # the min
        limit = 16*1024  # default
        # limit = 64*1024 # max
        run_sysctl("net.ipv4.tcp_wmem", "{min} {default} {max}".format(
            min=limit,
            default=limit,
            max=limit
        ))

        run_sysctl("net.ipv4.tcp_no_metrics_save", 1)

        self.net = Mininet(
            topo=self.topo,
            link=TCLink,
            host=MptcpHost,
            cleanup=True,
            # inNamespace=False,
        )

        self.topo.hook(self.net)
        self.net.start()

        try:
            pass
        except Exception as e:
            print("WARNING %s" % e)

        assert tcp_timestamps is None or tcp_timestamps < 5
        if tcp_timestamps is not None:
            run_sysctl('net.ipv4.tcp_timestamps', tcp_timestamps)

    @staticmethod
    def init_subparser(parser):
        return parser

    # def start_nemphis(self, node, cmd, **kwargs):
    #     '''
    #     start the NEtlink MPtcp HAskell daemon
    #     '''
    #     # daemon $@
    #     # cabal run daemon daemon $@
    #     # cmd = ["mptcp-pm", "-g", "-i", "any", "-w", pcap_filename]
    #     # cmd = ["nix-build", "./default.nix"]
    #     # subprocess.check_call(cmd, cwd="")

    #     # TODO need to remove/insert the module beforehand ?

    #     self.start_daemon(node, cmd, shell=True, stderr=subprocess.PIPE)

    # https://github.com/mininet/mininet/issues/857
    def start_daemon(self, node, cmd, **kwargs):

        print("starting daemon...")
        logging.info("starting: %s", cmd)

        # could use pexec as well ?
        proc = node.popen(cmd, **kwargs)
        self._popens.append(proc)
        print("returncode", proc.returncode)

        if proc.poll():
            print("Failed to run ", cmd)
            print("returned", proc.returncode)
            # print(err)
            sys.exit(1)

        return proc

    def start_tcpdump(self, node, **kwargs):
        cmd = ["tcpdump", "-i", "any", "-w", self._out("%s" % node, self.topo, ".pcapng")]
        self.start_daemon(node, cmd)

    def start_tshark(self, node, **kwargs):
        # nohup tshark -i any -n -w out/server.pcap -f "tcp port 5201" 2>1 &
        # todo use dumpcap instead
        # dumpcap -q -w
        # for tcpdump use -U

        # BACKUP solution
        # self.start_tcpdump(node, **kwargs)

        # The file "XX.pcapng" appears to have been cut short in the middle of a packet
        # https://stackoverflow.com/questions/13563523/the-capture-file-appears-to-have-been-cut-short-in-the-middle-of-a-packet-how
        pcap_filename = self._out("%s" % node, self.topo.topo_name, ".pcapng")
        # pcap_filename = "/tmp/%s_%d_%s" % (node, number_of_paths, ".pcapng")
        cmd = ["tshark", "-g", "-i", "any", "-w", pcap_filename]
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
        print("name = %r" % self.name)
        cmd = ["iperf3", "-s", "--json", "--logfile={logfile}".format(
            logfile=self._out("server_iperf", self.name, ".log")
        )]

        # just as a security
        node.cmdPrint("pkill -9 iperf")
        self.start_daemon(node, cmd)

    def start_webfs(self, node, **kwargs):
        '''
        There is also fileshare now packaged in nixpkgs
        '''
        # -i 7.7.7.7
        # -s => some text in syslog
        # -R <dir> set document root to DIR
        print("startwebfs")
        cmd = "webfsd -s -R /home/teto/testbed -d"
        self.start_daemon(node, cmd)

    # setup as an abstract to implement
    def setup(self, **kwargs):
        net = self.net
        client = net.get('client')
        server = net.get(SERVER_NAME)
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
        return os.path.join(self.out, suffix)

    def tearDown(self):
        logging.info("Tearing down")

        # restore some sysctl values ? like timestamp
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

    def setup(self, **kwargs):
        net = self.net
        server = net.get(SERVER_NAME)
        self.start_iperf_server(server)

        # subprocess.check_call("sudo insmod /home/teto/mptcp/build/net/mptcp/mptcp_prevenant.ko")
        # TODO temporary must have been prevenant here
        # run_sysctl("net.mptcp.mptcp_scheduler", "redundant")

        super().setup(**kwargs)

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
        server = self.net.get(SERVER_NAME)

        # need to generate a situation with frequent retransmissions
        for run in range(kwargs.get("runs", 1)):
            self.run_xp(client=client, server=server, run=run, **kwargs)

    def run_xp(self, client, server, run, **kwargs):
        # in iperf3, the client sends the data so...
        # self.start_iperf_client(client,  )
        # client = dataAmount
        # server = self.net.get('server')
        cmd = [
            "iperf3", "-c", server.IP(),
            "--cport 5500",
            "--json",
            # # dataAmount="-n " + dataAmount if FILE_TO_TRANSFER is not None else "",
            # dataAmount="",
            dataAmount,
            "--logfile={logfile}".format(logfile=self._out(
                "client_iperf", "path", self.topo.topo_name, "run", run, ".log")),
            # {fromFile}".format(
            # # Generated by gen_file
            # # must finish with a string "DROPME" so that ebpfdropper can recognize and
            # # drop it
            "-F %s" % (FILE_TO_TRANSFER) if FILE_TO_TRANSFER else "",
            # # fromFile=args.file "",
        ]
        client.cmdPrint(cmd)


class IperfNetlink(IperfTest):
    def __init__(self, *args, **kwargs):
        """
        """
        Test.__init__(self, "Iperf (netlink)", *args, **kwargs)
        self.description = "iperf test"

    def setup(self, **kwargs):
        client = self.net.get('client')
        server = self.net.get(SERVER_NAME)
        try:
            run_sysctl("net.mptcp.mptcp_path_manager", "netlink")
        except Exception as e:
            print(e)
            print("You probably need to load the netlink module, e.g.:")
            print("insmod /home/teto/mptcp/build/net/mptcp/mptcp_netlink.ko")
            exit(1)

        cmd = [
            "mptcp-pm", "daemon", server.IP(),
            # or just use fake_solver and add it to PATH
            # os.path.join(os.getcwd(), "fake_solver")
            # /home/teto/mptcp-pm/hs
            "--optimizer=./fake_solver",
            "--out=" + self.out,
            # TODO passer le dossier temporaire
            # ""
        ]
        # TODO I want to log its output
        # self.cmdPrint("mptcp-pm")
        fd = open(self._out(PATH_MANAGER_FILENAME), "w+")
        self.start_daemon(client, cmd, shell=True, stdout=fd, stderr=subprocess.STDOUT)
        super().setup(**kwargs)

class IperfWithLostLinks(IperfTest):
    def __init__(self, *args, **kwargs):
        """
        """
        super().__init__("Iperf", *args, **kwargs)
        self.description = "iperf test with intermittent link"

    def run_xp(self, client, server, run, **kwargs):
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
            logfile=self._out("client_iperf", "path", self.topo.topo_name, "run", run, ".log")
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

    def setup(self, **kwargs):
        gateway = net.get('gateway')
        # if kwargs.get("ebpfdrop"):
        print("attach_filter %r" % gateway)
        # TODO pass ifname ?

        attach_filter(gateway)

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
        super().__init__("Dack", **kwargs)
        self.description = "Dataack test"

        # TODO temporary
        # run_sysctl("net.mptcp.mptcp_scheduler", "redundant")

    @staticmethod
    def init_subparser(parser):
        parser.add_argument("fileToDownload", action="store",
                            type=str, default=FILE_TO_TRANSFER, help="filename to download")
        parser.add_argument("--reordering", action="store", type=int, default=3,
                            help="number of dupack to consider a fast retransmit")
        return parser

    def setup(self, **kwargs):
        logging.info("setup network")
        server = net.get('server')
        gateway = net.get('gateway')

        self.start_webfs(server)

        # run_sysctl("net.ipv4.tcp_reordering", 3)

        super().setup(**kwargs)

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

    def run_xp(self, run, client, fileToDownload, **kwargs):
        """
        Start an http server, download a file and saves the transfer time into a csv
        """
        gateway = self.net.get('gateway')
        server = self.net.get('server')
        # cmd = "wget http://%s/%s -O /dev/null"
        cmd = "curl -so /dev/null -w '%%{time_total}\n' http://%s/%s"
        # TODO use
        server.getIP()
        cmd = cmd % ("7.7.7.7:8000", fileToDownload)
        #     import re

        # log.info(cmd)
        # CLI(net)
        print("starting")
        out = client.cmdPrint(cmd)
        print(out)

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
    "iperfNetlink": IperfNetlink,
    # "reinjection": ReinjectionTest,
}


def cleanup():
    net_cleanup()
    # TODO kill tshark/haskell daemons

# clean sthg
def sigint_handler(signum, frame):
    print('Stop pressing the CTRL+C!')
    # global net
    # net.stop()

    cleanup()
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

    def __init__(self, topo_name, links: Sequence[Dict], *args, **kwargs):
        self.topo_name = topo_name
        self.diamond_links = links
        super().__init__(*args, **kwargs)

    def build(self, loss=0):
        '''
        TODO
        pass the name of left and right nodes, along with their networks
        '''

        # If you need per-host private directories,
        # you can specify them as options to Host, for example:
        # h = Host( 'h1', privateDirs=[ '/some/directory' ] )
        client = self.addHost('client')
        server = self.addHost('server')
        gateway = self.addHost('gateway', cls=LinuxRouter,)

        # everything should go through this switch
        # since we need to cancel only the first paquet

        # only one link between the 2
        # https://github.com/mininet/mininet/issues/823

        for i, params in enumerate(self.diamond_links):
            routerName = self.getName(i)
            router = self.addHost(routerName, cls=LinuxRouter,)

            # one good fast path
            # params.update({'use_tbf': True,
            #     'max_queue_size': 15000 # 10 paquets
            # })

            self.addLink(client, router, **params)
            link = self.addLink(router, gateway, )

        link2 = self.addLink(server, gateway, )
        print("just for testing, link type = ", type(link2))

    def getName(self, idx):
        '''Router name'''
        return 'r' + str(idx + 1)

    def set_mptcp_behavior(self, intf: str, status):
        """
        for a link, set status
        intf: interface name
        """

        assert status in ["on", "off", "backup"]
        # ip link set dev eth0 multipath backup
        msg = f"ip link set dev {intf} multipath {status}"
        # % (intf, status)
        subprocess.check_call(msg)

    def network_generator(self, network: Mininet, client, server):
        """
        Generates
        TODO extend later with
        rename into left/right
        todo use getinterface ip a la place

        See StaticTopo.build
        """

        gateway = network.get('gateway')

        leftNode = client
        rightNode = gateway

        # gateway to server network
        gw2s = ip.IPv4Network("3.3.3.0/24")
        print("netmask length ", gw2s.prefixlen)
        # host4.network /netmask/numaddresses
        # zip over 2 IPv4Networks
        # TODO not 2 ! should depend on number of paths
        for i, _ in enumerate(self.diamond_links):
            print("Setting up for id %d" % i)

            # router between client and server
            routerName = self.getName(i)
            r = network.get(routerName)

            # todo use g
            left2router = ip.IPv4Network("10.%d.0.0/24" % (i, ))
            # gateway2router in fact
            right2router = ip.IPv4Network("10.%d.1.0/24" % (i, ))

            #
            print("client intf names", client.intfNames())
            print("server intf names", server.intfNames())
            # print("ip %d" % i, str(left2router[i]))
            # print("ip 1", str(left2router[1]))

            print("left2router.prefixlen=%d" % left2router.prefixlen)
            leftNode.setIP(str(left2router[1]), left2router.prefixlen,
                           '%s-eth%d' % (leftNode.name, i))
            r.setIP(str(left2router[2]), left2router.prefixlen, f"{r.name}-eth0")
            r.setIP(str(right2router[2]), right2router.prefixlen, f"{r.name}-eth1")

            # here we use a mask that covers networks from the gateay till the leftNode
            # (including the router ) right2router.prefixlen,
            rightNode.setIP(str(right2router[1]), right2router.prefixlen,
                            '%s-eth%d' % (rightNode.name, i))

            # routes from one side to the side beside the router
            rightNode.cmdPrint("ip route add %s scope global via %s dev %s"
                               % (left2router, right2router[2], f"{rightNode.name}-eth{i}"))
            leftNode.cmdPrint("ip route add %s scope global via %s dev %s"
                              % (right2router, left2router[2], f"{leftNode.name}-eth{i}"))

            # rightNode.cmdPrint("ip route add default scope global nexthop via %s dev %s"
            #                    % (right2router[2], f"{rightNode.name}-eth{i}"))

            # by default route to the rightmost node
            # r.cmdPrint("ip route add default scope global nexthop via %s dev %s"
            # % (right2router[1], f"{r.name}-eth1"))

            # TODO here we assume that the leftNode is the client node
            # so we can run the hooks on it
            # connectionsTo
            leftIntf = leftNode.intf(f"{leftNode.name}-eth{i}")
            print("Intf %r" % leftIntf)
            runMptcpHookOnInterface(
                leftIntf,
                gateway=str(left2router[2])
            )

    #     gw.cmd('ip route add 3.3.3.0/24 via 5.5.5.1 dev %s-eth0' % gw.nameg
            print("DEBUG MAAAATTT")

            # add route from router towards server
            r.cmdPrint("ip route add {net} via {ip} dev {intf}".format(
                # server
                net=gw2s,
                ip=right2router[1],
                intf=f"{r.name}-eth1"
            ))

            # TODO remove
            # r.cmd('sysctl -w net.ipv4.ip_forward=1')

            # not sure right node is of class LinuxRouter
            rightNode.cmd('sysctl -w net.ipv4.ip_forward=1')

        # str(right2router[2])
        gwNbIntfs = len(rightNode.intfs)
        print("Number of gateway interfaces %d" % gwNbIntfs)
        rightNode.setIP(str(gw2s[1]), gw2s.prefixlen, f"{rightNode.name}-eth%d" % (gwNbIntfs-1))
        server.setIP(str(gw2s[2]), gw2s.prefixlen, f"{server.name}-eth0")

        # routerName = self.getName(i)
        # r = network.get(routerName)
        # TODO fix
        # rightNode.cmd(f"ip route add {gw2s} via {gw2s[1]} dev {rightNode.name}-eth0")
        # %s" % str(gw2s[2]))
        # TODO remove
        server.cmdPrint("ip route add default scope global nexthop via %s dev %s" %
                        (str(gw2s[1]), f"{server.name}-eth0"))

        # hook_filename = "mptcp_up_raw"
        # client.runMptcpHookOnEveryInterface(hook_filename=hook_filename)

        # server.run
        runMptcpHookOnInterface(
            intf=server.intf("server-eth0"),
            gateway=str(gw2s[1]),
        )

        # TODO add route towards server
        leftNode.cmdPrint("ip route add default scope global nexthop via %s dev %s" %
                          ("10.0.0.2", f"{leftNode.name}-eth0"))

        # client also needs a route towards the server
        # client.cmd('ip route add default scope global nexthop via 3.3.3.1 dev %s-eth0' % client.name)

    def hook(self, network):
        client = network.get("client")
        server = network.get("server")
        self.network_generator(network, client, server)


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


# TODO difference between Host and Node ?
class MptcpHost(mininet.net.Host):
    """
    mounts debugfs so that bcc works
    """

    def __init__(self, name, **kwargs):
        '''
        '''

        super(MptcpHost, self).__init__(name, **kwargs)
        res = self.cmd("mount -t debugfs none /sys/kernel/debug")
        res = self.cmd("mount -t bpf none /sys/fs/bpf/")

    # def runMptcpHookOnEveryInterface(self, hook_filename, ):
    #     '''
    #     '''
    #     # self.cmd("ip route flush all")
    #     for intf in self.intfList():
    #         runMptcpHookOnInterface(intf, gateway, hook_filename)


if __name__ == '__main__':

    #
    print("To clean run `mn -c`")
    print("You might want to run `nix-serve  -p 8080`")
    print("sudo insmod /home/teto/mptcp/build/net/mptcp/mptcp_prevenant.ko")

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--reinjections", type=bool, default=False,
                        help="Check for reinjections")
    parser.add_argument("-d", "--debug", choices=['debug', 'info', 'error'],
                        help="Running in debug mode", default='info')
    # shouldn't let the user choose it, it's too dependant on the experiment
    parser.add_argument("-t", "--topo", dest="topo_name",
                        choices=available_topologies.keys(),
                        help="Topology", default="symetric")
    parser.add_argument("-c", "--capture", action="store_true",
                        help="capture packets", default=False)
    parser.add_argument("--tcp", action="store_true",
                        help="Wether to disable mptcp", default=False)
    parser.add_argument("-s", "--scheduler", choices=SCHEDULERS,
                        help="Mptcp scheduler", default="default")
    parser.add_argument("-p", "--path-manager", choices=["fullmesh", "ndiffports", "netlink"],
                        help="Mptcp path manager", default="fullmesh")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Waiting in command line interface", default=False)
    # parser.add_argument("-l", "--loss", help="Loss rate (between 0 and 100", default=0)
    parser.add_argument("-o", "--out", action="store",
                        dest="out", default=None, help="out folder")

    # parser.add_argument("--post-process", "-pp", action="store", default=None,
    #                     help="Run a postprocess script")
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

    dargs = vars(args)

    setLogLevel(args.debug)
    # args.debug
    logging.getLogger().setLevel(logging.DEBUG)

    print("CWD=", os.getcwd())

    logging.info("Selected topology %s", args.topo_name)
    my_topo = StaticTopo(
        topo_name=args.topo_name,
        links=available_topologies[args.topo_name])
    # my_topo = StaticTopo(args.topo_name, topo=topo, )
    logging.info("Selected topology %s", my_topo)

    print("args dict")
    print(dargs)

    extraDict = {
        "net": net,
        "topo": my_topo,
    }
    dargs.update(extraDict)
    test = (available_tests.get(args.test_type))(**dargs)  # type: ignore
    logging.info("Launching test %s", args.test_type)

    try:

        test.setup(**dargs)

        test.runExperiments(**dargs)

        final = test.out
        import glob
        pcaps = glob.glob(os.path.join(test.out, "*.pcapng"))
        print(pcaps)
        print("mptcpanalyzer -l " + os.path.join(final, pcaps[0]) + " 'mptcp_summary -H 1'")

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except Exception as e:
        logging.exception("Exception triggered ")
    finally:
        test.tearDown()  # type: ignore

        # TODO reestablish
        # disabled in order to check for journald logs in /j
        # net_cleanup()
        if args.out is not None:
            log.info("creating %s", args.out)
            subprocess.check_call("mkdir -p %s" % args.out, shell=True)
            final = shutil.move(test.out, args.out)

        # log.info("Results in %s", final)
        subprocess.call(["tail", os.path.join(final, PATH_MANAGER_FILENAME)])

        final = os.path.abspath(final)
        log.info("Results in %s", final)

    print("finished")
