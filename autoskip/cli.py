#!/usr/bin/env python3
from . import autoskipper
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--toggle', '-t', action='store_const', const=True, help='Toggle autoskipper')
    parser.add_argument('--skip', '-s', action='store_const', const=True, help='Skip song')
    parser.add_argument('--whitelist-song', '-wls', action='store_const', const=True, help='Toggle whitelist for current song')
    parser.add_argument('--whitelist-artist', '-wla', action='store_const', const=True, help='Toggle whitelist for current artist')
    parser.add_argument('--blacklist-song', '-bls', action='store_const', const=True, help='Toggle blacklist for current song')
    parser.add_argument('--blacklist-artist', '-bla', action='store_const', const=True, help='Toggle blacklist for current artist')
    parser.add_argument('--notify', '-n', action='store_const', const=True, help='Toggle notifications')
    parser.add_argument('--run', '-r', action='store_const', const=True, help='Run CLI')
    args = parser.parse_args()

    # Could be done with dict, but this is easily read.
    if args.whitelist_artist:
        autoskipper.wla()

    if args.blacklist_artist:
        autoskipper.bla()

    if args.whitelist_song:
        autoskipper.wls()

    if args.blacklist_song:
        autoskipper.bls()

    if args.skip:
        autoskipper.skip()

    if args.toggle:
        autoskipper.toggle()

    if args.notify:
        autoskipper.notify()

    # Makes a dict of all args used. Checked in order to determine if the program should be run.
    fixed_args = {i: args.__dict__[i] for i in args.__dict__ if args.__dict__[i] is not None}
    if not fixed_args or args.run:
        autoskipper.run()
