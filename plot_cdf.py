#!/usr/bin/env nix-shell 
#!nix-shell shell-plot.nix -i python --show-trace 

import json
import sys
import os
import argparse
import logging
from collections import OrderedDict

def load_completion_times(folder):

    cpt = []

    filenames = []
    for (dirpath, dirnames, cur_filenames) in os.walk(folder):
        filenames.extend(cur_filenames)
        break
    
    for f in map(lambda x: os.path.join(folder, x), filenames):
        with open(f) as fd:
            print("loading %s" % f)
            ret = json.load(fd)
            elapsed_time = ret["end"]["sum_received"]["seconds"]
            print(elapsed_time)
            cpt.append(elapsed_time)

    print(cpt)

    return cpt


def plot_completion_times(results):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    # heights = pd.Series(np.random.normal(size=100))
    df = pd.Series(results)
    # df = results

    fig = plt.figure()
    axes = fig.gca()
    # step histtype='step' to remove bars
    df.hist(histtype='step', cumulative=True, density=1)
    # axes.set_ylabel("success")
    # axes.set_xlabel("Time")

    # TODO move afterwards ?
    # df.set_index('time', inplace=True)

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
        "--gen", "-g", action="store_true", default=False,
        help="More verbose output, can be repeated to be even more "
        " verbose such as '-dddd'"
    )


    parser.add_argument(
        "folder",
        help="Either a pcap or a csv file (in good format)."
    )
    # parser.add_argument('--version', action='version', version="%s" % (__version__))
    parser.add_argument(
        "--debug", "-d", action="count", default=0,
        help="More verbose output, can be repeated to be even more "
        " verbose such as '-dddd'"
    )

    args, unknown_args = parser.parse_known_args(arguments)

    # log.setLevel(level)

    cpt = load_completion_times(args.folder)

    # plot_owd(args.input_file)
    plot_completion_times(cpt)


if __name__ == '__main__':
    main()


