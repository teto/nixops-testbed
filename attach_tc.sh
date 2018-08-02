sudo tc qdisc add dev eth0 clsact

sudo tc filter add dev  eth0 ingress bpf obj test_ebpf_tc.o section action direct-action

# sudo cat /sys/kernel/debug/tracing/trace_pipe
