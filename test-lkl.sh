# gdb --args ping 127.0.0.1
# (gdb) set exec-wrapper env LD_PRELOAD=liblkl-hijack.so LD_LIBRARY_PATH=lib/hijack
# (gdb) run
# set print thread-events off

TAPDEV=lkl_tap
# ip tuntap show |grep $TAPDEV
# if [ $? -ne 0 ]; then

	ip tuntap del dev $TAPDEV mode tap || true
	ip tuntap add dev $TAPDEV mode tap user $USER
	ip link set dev $TAPDEV
	# .11 seems unused
	ip addr add dev $TAPDEV 192.168.0.11/24
# fi

# curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org
lkl-hijack.sh curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org

# As tests  we can run:
# motomu@arch2 > sudo LKL_HIJACK_BOOT_CMDLINE="ip=dhcp" LKL_HIJACK_NET_IFTYPE0=tap LKL_HIJACK_NET_IFPARAMS0=tap0 \
# ./tools/lkl/bin/lkl-hijack.sh curl --resolve multipath-tcp.org:80:130.104.230.45 http://multipath-tcp.org
# Yay, you are MPTCP-capable! You can now rest in peace.
