#!/usr/bin/env nix-shell 
#!nix-shell /home/teto/testbed/check.nix -i python


# Copyright (c) PLUMgrid, Inc.
# Licensed under the Apache License, Version 2.0 (the "License")
# nix-shell -p python '( linuxPackagesFor mptcp-local-stable ).bcc' mptcp-local-stable.dev -i python

# run in project examples directory with:
# sudo ./hello_world.py"
# see trace_fields.py for a longer example

# https://github.com/iovisor/bcc/blob/master/docs/reference_guide.md#1-bpf
from bcc import BPF
from time import sleep, strftime
import ctypes as ct
import argparse


# https://github.com/iovisor/bcc/blob/master/tools/ext4slower.py
parser = argparse.ArgumentParser(
    description="trace reinjections",
    # formatter_class=argparse.RawDescriptionHelpFormatter, epilog=examples
    )

parser.add_argument("-j", "--csv", action="store_true", help="just print fields: comma-separated values")

args = parser.parse_args()


# TODO trace args = mptcp_meta_retransmit_timer
# instrument mptcp_sub_send_loss_probe
# just look at __mptcp_reinject_data call

# reference API at https://github.com/iovisor/bcc/blob/master/docs/tutorial_bcc_python_developer.md
prog = """
#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <bcc/proto.h>

BPF_HISTOGRAM(dist);
BPF_PERF_OUTPUT(events);

// define output data structure in C
struct reinjection_event {
	u32 res;
	u64 ts;
	u32 event; // type ?
};
enum EVENT_TYPE {
TLP = 0,
TIMEOUT,
OPPORTUNISTIC  
};

/* if the result is not null then we have an opportunistic reinjection */
int check_ret(struct pt_regs *ctx) {
    struct reinjection_event data = {};
    int  ret = 0;

    /* ret is struct sk_buff * */
    int rawret  = PT_REGS_RC(ctx);
    // struct sk_buff *skb

    //    bpf_trace_printk("Hello, World!\\n");

    ret = (rawret != 0) + 1;
    dist.increment( ret );

    // int perf_submit((void *)ctx, (void *)data, u32 data_size ) returns 0 on success
    data.event = ret;
    data.res = OPPORTUNISTIC;
    data.ts = bpf_ktime_get_ns();
    events.perf_submit(ctx, &data, sizeof(data));
    return rawret;
}


/* if the result is not null then we have an opportunistic reinjection */
int record_event(struct pt_regs *ctx) {
    struct reinjection_event data = {};

    // record snd_una ? subflow it was lost ?
    data.res = PT_REGS_RC(ctx);
    data.ts = bpf_ktime_get_ns();

    data.event = TLP;
    events.perf_submit(ctx, &data, sizeof(data));
    return PT_REGS_RC(ctx);;
}


"""

# define output data structure in Python
TASK_COMM_LEN = 16    # linux/sched.h
class Data(ct.Structure):
    _fields_ = [("res", ct.c_ulonglong),
                ("ts", ct.c_ulonglong),
                ("type", ct.c_ulonglong),
                ]

b = BPF(text=prog)


ret = b.attach_kretprobe(event="mptcp_rcv_buf_optimization" , fn_name="check_ret")

# mptcp_meta_retransmit_timer
ret = b.attach_kretprobe(event="mptcp_retransmit_skb" , fn_name="record_event")
ret = b.attach_kretprobe(event="mptcp_sub_send_loss_probe" , fn_name="record_event")
# ret = b.attach_kretprobe(event="tcp_v4_connect" , fn_name="check_ret")
# print ("returned value of attach: %r" % ret)
# header
# print("Tracing... Hit Ctrl-C to end.")

#
# dist = b.get_table("dist")

# interval = 300; # seconds ?
def print_event(cpu, data, size):
    event = ct.cast(data, ct.POINTER(Data)).contents
    if args.csv:
        print("%d,%d,%d" % (event.type, event.ts, event.res, ))
    else:
        print("Reinject ? ts %d => %d" % (event.ts, event.res,))




if args.csv:
    print("EventType,Timestamp,reinject")

# loop with callback to print_event
b["events"].open_perf_buffer(print_event)

exiting = 0

while 1:
    try:
        # Read messages from kernel pipe
        # blocking by default
        # b.perf_buffer_poll() # is the new API
        b.kprobe_poll()
        # (task, pid, cpu, flags, ts, msg) = b.trace_fields()
        # (_tag, saddr_hs, daddr_hs, dport_s) = msg.split(" ")
        # print("msg=", msg)

    # except ValueError:
    #     # Ignore messages from other tracers
    #     continue
    except KeyboardInterrupt:
        exiting = 1

    # print("hello world")
    # dist.print_log2_hist("My label", "operation")

    # dist.clear()

    # countdown -= 1
    if exiting:
        exit()

