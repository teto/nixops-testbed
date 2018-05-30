#!/usr/bin/env python
# Copyright (c) PLUMgrid, Inc.
# Licensed under the Apache License, Version 2.0 (the "License")

# run in project examples directory with:
# sudo ./hello_world.py"
# see trace_fields.py for a longer example

# https://github.com/iovisor/bcc/blob/master/docs/reference_guide.md#1-bpf
from bcc import BPF
from time import sleep, strftime

    # u64 *tsp;
    # u32 pid = bpf_get_current_pid_tgid();
    # // fetch timestamp and calculate delta
    # tsp = start.lookup(&pid);
    # if (tsp == 0) {
    #     return 0;   // missed start or filtered
    # }
    # u64 delta = (bpf_ktime_get_ns() - *tsp) / FACTOR;
    # // store as histogram
    # dist_key_t key = {.slot = bpf_log2l(delta)};
    # __builtin_memcpy(&key.op, op, sizeof(key.op));
    # dist.increment(key);
    # start.delete(&pid);
    # return 0;

prog = """
#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <bcc/proto.h>

BPF_HISTOGRAM(dist);
BPF_PERF_OUTPUT(events);

/* if the result is not null then we have an opportunistic reinjection */
int check_ret(struct pt_regs *ctx) {
    //  BPF_PERF_OUTPUT() is better ?
    // bpf_trace_printk("Hello, World!\\n");
    int  ret = 0;
    // pr_info ("Hello, World!\\n");

    /* ret is struct sk_buff * */
    struct sk_buff *skb = PT_REGS_RC(ctx);
    ret = (skb != 0);
    dist.increment( ret );

    // int perf_submit((void *)ctx, (void *)data, u32 data_size ) returns 0 on success
    events.perf_submit(ctx, ret, sizeof(ret));
    return 0;
}
"""

b = BPF(text=prog)


b.attach_kretprobe(event="mptcp_rcv_buf_optimization" , fn_name="check_ret")

# header
print("Tracing... Hit Ctrl-C to end.")

#
dist = b.get_table("dist")

interval = 300; # seconds ?
while (1):
    try:
        if interval:
            sleep(int(interval))
        else:
            sleep(99999999)
    except KeyboardInterrupt:
        exiting = 1

    print("hello world")

    dist.print_log2_hist("My label", "operation")
    # dist.clear()

    # countdown -= 1
    if exiting:
        exit()

