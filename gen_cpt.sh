#!/usr/bin/env nix-shell
#!nix-shell -p iperf3 -i bash


HOST=$1
NB_OF_RUNS=${2:-1}
OUT_FOLDER=${3:-out}

SIZE="1MB"

# IPERF2
# -x, --reportexclude [CDMSV]
#        exclude C(connection) D(data) M(multicast) S(settings) V(server) reports
# -y, --reportstyle C|c
#        if set to C or c report results as CSV (comma separated values)
# perf -c 127.0.0.1 --enhancedreports -n 1MB -y C

# IPERF3
# --json
# perf3 -c 127.0.0.1 --json -n 1MB
# in the json we have which is interested
# "sum_sent":	{
# 	"start":	0,
# 	"end":	0.00032401084899902344,
# 	"seconds":	0.00032401084899902344,
# 	"bytes":	1310720,
# 	"bits_per_second":	32362373150.139809,
# 	"retransmits":	0
# },
# "sum_received":	{


# https://stackoverflow.com/questions/966020/how-to-produce-range-with-step-n-in-bash-generate-a-sequence-of-numbers-with-i
# set -x

# if -
mkdir -p "$OUT_FOLDER"
for (( COUNTER=0; COUNTER<= $NB_OF_RUNS; COUNTER+=1 )); do
    # echo coco $COUNTER
	FILENAME="${OUT_FOLDER}/iperf_${SIZE}_run_${COUNTER}.json"

	set -x
	iperf3 -c $HOST --json -n "$SIZE" --logfile "$FILENAME"
	set +x

	if [ $? -ne 0 ];
	then 
		echo "an error happened"
		exit 1
	fi
done

exit 0
# set +x

