#! /usr/bin/env sh

# set -x
if [ -z "$NIXOPS_DEPLOYMENT" ]; then
	export NIXOPS_DEPLOYMENT="$1"
fi

# echo "Using deployment=$NIXOPS_DEPLOYMENT"

# exit_trap ()
# {
# 	local lc="$BASH_COMMAND" rc=$?
# 	test $rc -eq 0 || echo "*** error $rc"
# }
# trap exit_trap EXIT
# trap 'echo term or sign catched; exit 1' TERM INT


[ hostname == "jedha" ];
HOST=$?

echo "running on host $HOST" 

# clean local files so that it is easier to catch errors
# rm -rf server client
# nixops ssh-for-each rm /tmp/*.pcap

# upload itself
# skip it, assuming it it
# if [ $HOST ]; then
# 	nixops scp --to main "$0" .
# fi


# run one thing in a shell
nixops ssh main bash -x /home/teto/testbed/run_xp.sh

echo "downloading results..."

# if [ $HOST ]; then
	# rapatriate folders
nixops scp --from main out .
# fi
