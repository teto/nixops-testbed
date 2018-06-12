import sys
import argparse
import logging
from collections import OrderedDict

#!/usr/bin/env nix-shell 
#!nix-shell shell-plot.nix -i python




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


    # plot_owd(args.input_file)
    plot_completion_time(args.input_file)


if __name__ == '__main__':
    main()


