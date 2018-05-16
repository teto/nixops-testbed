#!/usr/bin/python

import pandas as pd
import matplotlib.pyplot as plt
import sys
import argparse
import logging
from collections import OrderedDict


# pd.read_csv(

# tcpprobe_dtypes

# [time][src][dst][length][snd_nxt][snd_una][snd_cwnd][ssthresh][snd_wnd][srtt][rcv_wnd]
# 
	# return scnprintf(tbuf, n,
	# 		"%lu.%09lu %pISpc %pISpc %d %#x %#x %u %u %u %u %u %u %u\n",
	# 		(unsigned long)ts.tv_sec,
	# 		(unsigned long)ts.tv_nsec,
	# 		&p->src, &p->dst, p->length, p->snd_nxt, p->snd_una,
	# 		p->snd_cwnd, p->ssthresh, p->snd_wnd, p->srtt,
	# 		p->sowd_out, p->sowd_in, p->rcv_wnd);
# 0.507024701 192.168.122.233:40080 192.168.122.167:5201 28 0x65cef3ca 0x65ce5bea 30 29 1930880 40548 0 0 87616
# modprobe won't work for now see https://github.com/NixOS/nixpkgs/issues/40485
# modprobe tcp_probe port=5201 full=1
fields = OrderedDict ([
    ('time', str),
    ('src',  str),
    ('dst',  str),
    ('length',  int),
    ('snd_nxt',  int),
    ('snd_una',  int),
    ('snd_cwnd',  int),
    ('ssthresh',  int),
    ('snd_wnd',  int),
    ('srtt',  int),
    ('sowd_out',  int),
    ('sowd_in',  int),
    ('rcv_wnd',  int)
])

def plot_owd(filename):

    with open(filename) as fd:
        df = pd.read_csv(
            fd,
            comment='#',
            # we don't need 'header' when metadata is with comment
            header=None,
            names=fields.keys(),
            # skiprows
            # sep=' ',
            delim_whitespace=True, # use whitespace as delimiter
            # having both a converter and a dtype for a field generates warnings
            # so we pop tcp.flags
            dtype=fields,
            
            usecols = [ 'time', 'sowd_out', 'sowd_in'],

            # converters={
            #     "tcp.flags": _convert_flags,
            #     "mptcp.reinjection": functools.partial(_convert_to_list, field="reinjectionOf"),
            # },
            nrows=10, # useful for debugging purpose
            # na_filter=, # might make it able to deal with non-TCP packets
            # memory_map=True, # could speed up processing
        )



        fig = plt.figure()
        axes = fig.gca()
        handles, labels = axes.get_legend_handles_labels()

        axes.set_ylabel("One way delay (OWD)")
        axes.set_xlabel("elapsed time (s)")
        # axes.set_ylim([ymin,ymax])

        # df.lines
        df.set_index('time')
        ax1 = df.plot.line(ax=axes,
                # style=marker,
                # legend=False
        )
        # lines, labels = ax1.get_legend_handles_labels()
        # legend_artists.append(lines[-1])
        # legends.append("dack for sf %d" % tcpstream)
        plt.show()

def main(arguments=None):
    """
    This is the entry point of the program

    Args:
        arguments_to_parse (list parsable by argparse.parse_args.): Made as a parameter since it makes testing easier

    Returns:
        return value will be passed to sys.exit
    """

    if not arguments:
        arguments = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='Plot tcp_probe'
    )

    parser.add_argument(
        "input_file",
        help="Either a pcap or a csv file (in good format)."
    )
    # parser.add_argument('--version', action='version', version="%s" % (__version__))
    parser.add_argument(
        "--debug", "-d", action="count", default=0,
        help="More verbose output, can be repeated to be even more "
        " verbose such as '-dddd'"
    )

    args, unknown_args = parser.parse_known_args(arguments)



    # level = logging.CRITICAL - min(args.debug, 4) * 10
    # log.setLevel(level)
    # print("Log level set to %s " % logging.getLevelName(level))

    # log.debug("Starting in folder %s" % os.getcwd())
    # log.debug("Pandas version: %s" % pd.__version__)
    # log.debug("cmd2 version: %s" % cmd2.__version__)


    plot_owd(args.input_file)


if __name__ == '__main__':
    main()

