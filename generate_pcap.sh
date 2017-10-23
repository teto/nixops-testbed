#! /usr/bin/env sh

set -x


# use scp to transfer the scripts
TESTBED="$HOME/testbed"

nixops scp --to server $TESTBED/server.sh /tmp
nixops scp --to client $TESTBED/client.sh /tmp
# pkill server

nixops ssh server -f "sh -x /tmp/server.sh" --logfile /tmp/server.log
nixops ssh client "sh -x /tmp/client.sh" --logfile /tmp/client.log


nixops ssh server pkill -9 tshark
# rapatriate the captures

nixops scp --from server server.pcap server.pcap
# nixops scp --from server server.log server.log
nixops scp --from client client.pcap client.pcap
# nixops scp --from client client.log client.log
# $TESTBED/server.sh
