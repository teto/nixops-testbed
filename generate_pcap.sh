#! /usr/bin/env sh

# set -x
if [ -z "$NIXOPS_DEPLOYMENT" ]; then
	if [ $# -lt 1 ]; then
		echo "Set \$NIXOPS_DEPLOYMENT or pass the domain name"
		exit 1
	else
		export NIXOPS_DEPLOYMENT="$1"
	fi
fi

echo "Using deployement= $NIXOPS_DEPLOYMENT"

exit_trap ()
{
	local lc="$BASH_COMMAND" rc=$?
	test $rc -eq 0 || echo "*** error $rc"
}
trap exit_trap EXIT
trap 'echo term or sign catched; exit 1' TERM INT



# use scp to transfer the scripts
TESTBED="$HOME/testbed"

# clean local files so that it is easier to catch errors
rm *.pcap *.log
# nixops ssh-for-each rm /tmp/*.pcap

# upload scripts to /tmp
nixops scp --to server $TESTBED/server.sh /tmp
nixops scp --to client $TESTBED/client.sh /tmp
# pkill server

# need the & because the -f is not propagated to nixops ssh
# --logfile server.log
echo "Starting server"
nixops ssh server "sh -x /tmp/server.sh 2>1 >stdout.txt"
sleep 2

echo "Starting client"
nixops ssh client "sh /tmp/client.sh " --logfile client.log

nixops ssh server "dmesg > kmsg.log"

# sleep 5

# nixops ssh-for-each pkill tshark
# rapatriate the captures

nixops scp --from server kmsg.log skmsg.log
nixops scp --from server server.pcap server.pcap
nixops scp --from server server.log server.log
nixops scp --from client kmsg.log ckmsg.log
nixops scp --from client client.pcap client.pcap
nixops scp --from client client.log client.log
# $TESTBED/server.sh
