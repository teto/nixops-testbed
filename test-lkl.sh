# gdb --args ping 127.0.0.1
# (gdb) set exec-wrapper env LD_PRELOAD=liblkl-hijack.so LD_LIBRARY_PATH=lib/hijack
# (gdb) run
# set print thread-events off

TAPDEV=lkl_tap
ip show $TAPDEV
if [ $? -ne 0 ]; then
	ip tuntap add dev $TAPDEV
fi


lkl-hijack.man
