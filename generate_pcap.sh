#! /usr/bin/env sh

# set -x
if [ -z "$NIXOPS_DEPLOYMENT" ]; then
	# if [ $# -lt 1 ]; then
	# 	echo "Set \$NIXOPS_DEPLOYMENT or pass the domain name"
	# 	exit 1
	# else
		export NIXOPS_DEPLOYMENT="$1"
	# fi
fi

echo "Using deployment=$NIXOPS_DEPLOYMENT"

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
rm -rf server client
# nixops ssh-for-each rm /tmp/*.pcap

# upload scripts to /tmp
nixops scp --to server "$TESTBED/server" .
nixops scp --to client "$TESTBED/client" .
# pkill server

# need the & because the -f is not propagated to nixops ssh
# --logfile server.log
# need to redirect stderr because to let ssh disconnect when with -f ?
echo "Starting server"
nixops ssh server "sh -x server/server.sh 2>1 >stdout.txt"
sleep 2

echo "Starting client"
nixops ssh client "sh client/client.sh "

echo "saving data from server"
nixops ssh server "dmesg > out/kmsg.log"
echo "data saved"

# sleep 5

# nixops ssh-for-each pkill tshark
# rapatriate the captures

# rapatriate folders
nixops scp --from server out server
nixops scp --from client out client
