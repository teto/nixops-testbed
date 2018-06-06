#!/usr/bin/env sh

# erase previous results
rm -rf out
mkdir -p out


# https://unix.stackexchange.com/questions/113530/how-to-find-out-namespace-of-a-particular-process
# ps -h -o pidns -p 19589

# fix in staging for procps, seems hash is wrong ?
# 54c6a9c7104660757a713a8d2795df57b59251c5

# nix-shell --command \
# 	'python /home/teto/testbed/check_opportunistic_reinject.py -j > out/reinject.csv' &

/home/teto/testbed/check_opportunistic_reinject.py -j > out/reinject.csv &

BCC_PID=$!
jobs -l
jobs -p
if [ $? -ne 0 ]; then
	echo "failed to launch bcc tracker"
	exit 1
fi

echo "starting mn_test"


/home/teto/testbed/mn_test.py -n2

echo "Finished running iperf test"
# set -x

# kill the check_opportunistic_reinject
res=$(pkill -c -TERM -P $BCC_PID)

if [ $? -ne 0 ];
then
	echo "failed killing bcc script"
	exit 1
fi

# kill -- -$(ps -o pgid= $BCC_PID | grep -o [0-9]*)
# kill -- -PGID
# set +x
exit 0
