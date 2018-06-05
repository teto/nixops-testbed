#!/usr/bin/env sh

# erase previous results
rm -rf out
mkdir -p out

# nix-shell -p python '(linuxPackagesFor mptcp-local-stable).bcc' mptcp-local-stable.dev --command \
# 	'python /home/teto/testbed/check_opportunistic_reinject.py -j > out/reinject.csv' &
# BCC_PID=$!
# jobs -l
# jobs -p
# if [ $? -ne 0 ]; then
# 	echo "failed to launch bcc tracker"
# 	exit 1
# fi


nix-shell -p 'python.withPackages(ps:[ps.mininet-python])' --command \
	'python /home/teto/testbed/mn_test.py -n2'

echo "Finished running iperf test"
# set -x

# kill the check_opportunistic_reinject
# pkill -TERM -P $BCC_PID
# kill -- -$(ps -o pgid= $BCC_PID | grep -o [0-9]*)
# kill -- -PGID
pkill -9 tshark
# set +x
exit 0
