#!/usr/bin/env nix-shell 
#!nix-shell /home/teto/testbed/shell-check.nix -i python


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
import signal
import sys


# https://github.com/iovisor/bcc/blob/master/tools/ext4slower.py
parser = argparse.ArgumentParser(
    description="trace reinjections",
    # formatter_class=argparse.RawDescriptionHelpFormatter, epilog=examples
    )

parser.add_argument("-j", "--csv", action="store_true", help="just print fields: comma-separated values")
parser.add_argument("-m", "--monitor-reinject-queue", action="store_true", default=True, help="just print fields: comma-separated values")


def sigterm_handler(_signo, _stack_frame):
    # else 
    # print("handler called")
    sys.stdout.flush()
 

# Make sure stdout buffer is flushed on these signals
signal.signal(signal.SIGINT,  sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)





args = parser.parse_args()


# TODO trace args = mptcp_meta_retransmit_timer
# instrument mptcp_sub_send_loss_probe
# just look at __mptcp_reinject_data call

 #  Sets *@reinject to 1 if the returned segment comes from the
 # reinject queue. Sets it to 0 if it is the regular send-head of the meta-sk,
 # and sets it to -1 if it is a meta-level retransmission to optimize the
 # receive-buffer, we should use 2 to distinguish with penatly

# reference API at https://github.com/iovisor/bcc/blob/master/docs/tutorial_bcc_python_developer.md
# look into BPF_PERF_MAP
# use bpf_probe_read to extract values of
# TODO one can use PT_REGS_PARM1 to see 
# TP_DATA_LOC_READ_CONST ? defined https://github.com/iovisor/bcc/blob/c817cfd60ca42e97555c9cb1b076b01e3fa138a8/src/cc/export/helpers.h#L713
prog = """
#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <bcc/proto.h>

BPF_HISTOGRAM(dist);
BPF_PERF_OUTPUT(events);

// define output data structure in C
struct reinjection_event {
	u32 res;    // => successful or not
	u64 ts;
        u64 netns;
	u32 event; // type ?
};

enum EVENT_TYPE {
TLP = 0,
TIMEOUT,
REINJECT_QUEUE, // dunno if it is TLP or TIMEOUT
OPPORTUNISTIC,
OPPORTUNISTIC_WITH_PENALTY 
};


/* if the result is not null then we have an opportunistic reinjection */
static int record_event(struct pt_regs *ctx, int res, int eventType) {
    struct reinjection_event data = {};

    // record snd_una ? subflow it was lost ?
    data.res = res;
    data.event = eventType;
    data.ts = bpf_ktime_get_ns();
    data.netns = 0;

    // Get network namespace id, if kernel supports it
    #ifdef CONFIG_NET_NS
        // data.netns = sk->__sk_common.skc_net.net->ns.inum;
    #endif
    events.perf_submit(ctx, &data, sizeof(data));
    return PT_REGS_RC(ctx);;
}



int check_effective_reinjections(struct pt_regs *ctx) {
    struct reinjection_event data = {};
    int  ret = 0;

    /* we modified mptcp_skb_entail to return different values depending on 
     * return 10 + reinject; if not using fastest path
     * return 3 + reinject; in case of reinjection
     * 1 means a correct transmissions
    */
    int rawret  = PT_REGS_RC(ctx);
    int reinject = (int)PT_REGS_PARM2(ctx);
    int type = 0;


    ret = rawret;

    // la ca merde
    if (reinject < 0) {
        type = OPPORTUNISTIC;
    } else if (reinject > 0) {
        type = REINJECT_QUEUE;
    } else {
        // not a reinjection; skip it
        return rawret;
    }
    
    record_event(ctx, ret, type);
    return rawret;
}



"""



# HINT: The invalid mem access 'inv' error can happen if you try to dereference memory without first using bpf_probe_read() to copy it to the BPF stack. Sometimes the bpf_probe_read is automatic by the bcc rewriter, other times you'll need to be explicit.

# attached to 
# static struct sk_buff *mptcp_rcv_buf_optimization(struct sock *sk, int penal)
check_chosen = """
/* if the result is not null then we have an opportunistic reinjection */
int check_chosen_reinjections(struct pt_regs *ctx) {

    /* ret is struct sk_buff * */
    int rawret  = PT_REGS_RC(ctx);
    int penalty = -42;

    // example from the doc https://github.com/iovisor/bcc/blob/master/docs/reference_guide.md#4-uprobes
    bpf_probe_read(&penalty, sizeof(penalty), (void *)PT_REGS_PARM2(ctx));

    record_event(ctx, rawret != 0, (penalty) ? OPPORTUNISTIC : OPPORTUNISTIC_WITH_PENALTY);
    return rawret;
}
"""

# define output data structure in Python
TASK_COMM_LEN = 16    # linux/sched.h
class Data(ct.Structure):
    _fields_ = [("res", ct.c_uint),
                ("ts", ct.c_ulonglong),
                ("netns", ct.c_ulonglong),
                ("type", ct.c_uint),
                ]


if args.monitor_reinject_queue:
    prog += check_chosen


b = BPF(text=prog)


# that's the one we should hook

# static int mptcp_skb_entail(struct sock *sk, struct sk_buff *skb, int reinject)
ret = b.attach_kretprobe(event="mptcp_skb_entail" , fn_name="check_effective_reinjections")

# mptcp_meta_retransmit_timer
if args.monitor_reinject_queue:
    # has prototype
    # static struct sk_buff *mptcp_rcv_buf_optimization(struct sock *sk, int penal)
    ret = b.attach_kretprobe(event="mptcp_rcv_buf_optimization" , fn_name="check_chosen_reinjections")


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
        print("%u,%u,%u,%u" % (event.type, event.ts, event.netns, event.res, ))
    else:
        print("Reinject ? ts %d => %d" % (event.ts, event.res,))




if args.csv:
    print("EventType,timestamp,namespace,reinject")

# if args.monitor_reinject_queue:
#     ret = b.attach_kretprobe(event="mptcp_retransmit_skb" , fn_name="record_event")
#     ret = b.attach_kretprobe(event="mptcp_sub_send_loss_probe" , fn_name="record_event")

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

