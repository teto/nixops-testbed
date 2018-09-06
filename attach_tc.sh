#!/bin/sh
IF="${1:-enp4s0}"
echo "Interface $IF"
sudo tc qdisc add dev "$IF" clsact

# le "Note: 8 bytes struct bpf_elf_map fixup performed due to size mismatch! est normal
sudo tc filter add dev "$IF" ingress bpf obj ebpf_dropper.o section action verbose direct-action

# to remove the filter, one can then do

# sudo cat /sys/kernel/debug/tracing/trace_pipe


#!/usr/bin/nix-shell
#!nix-shell -p ebpfdropper
