#! /usr/bin/env sh

set -x

exit_trap ()
{
	local lc="$BASH_COMMAND" rc=$?
	test $rc -eq 0 || echo "*** error $rc"
}
trap exit_trap EXIT

# use scp to transfer the scripts
TESTBED="$HOME/testbed"

nixops scp --to server $TESTBED/server.sh /tmp
nixops scp --to client $TESTBED/client.sh /tmp
# pkill server

# need the & because the -f is not propagated to nixops ssh
nixops ssh server -f "sh -x /tmp/server.sh" --logfile /server.log &
sleep 2
nixops ssh client "sh -x /tmp/client.sh" --logfile client.log


nixops ssh server pkill -9 tshark
# rapatriate the captures

nixops scp --from server server.pcap server.pcap
nixops scp --from server server.log server.log
nixops scp --from client client.pcap client.pcap
nixops scp --from client client.log client.log
# $TESTBED/server.sh
