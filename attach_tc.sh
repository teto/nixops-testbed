IF="enp4s0"
sudo tc qdisc add dev "$IF" clsact

sudo tc filter add dev "$IF" ingress bpf obj test_ebpf_tc.o section action direct-action

# sudo cat /sys/kernel/debug/tracing/trace_pipe
