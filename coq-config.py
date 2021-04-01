#!/usr/bin/env python

import os, subprocess
from icecream import ic

import stackprinter
stackprinter.set_excepthook(style='darkbg2')

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import click

CONFIG   = "coq_config.yaml"
OPAMROOM = "~/.opam"

@click.command()
@click.version_option("1.0")
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.option("--dry-run", "-n", is_flag=True, help="Do not modify anything.")
def main(verbose, dry_run):
    if not os.path.exists(CONFIG):
        print("%s not found" % CONFIG)
        exit(1)
    if verbose:
        print("%s found" % CONFIG)
    try:
        with open(CONFIG, "r") as f:
            cfg = load(f, Loader=Loader)
    except:
        print("Error reading %s" % CONFIG)
        stackprinter.show()
        exit(1)
        
    ic(cfg)

    # Check if opam initialized
    if verbose:
        print("Checking OPAM")
    if not os.path.exists(os.path.expanduser(OPAMROOM)):
        print("OPAM is not initialized. Please set up OPAM with `opam init`.")
        exit(2)

    # Check if switch exists
    if verbose:
        print("Checking OPAM switches")
    try:
        switches = subprocess.check_output(["opam", "switch", "list", "-s"], text=True)
    except:
        print("Error getting list of OPAM switches")
        stackprinter.show()
        exit(2)
    switchesl = switches.split('\n')
    ic(switchesl)
    
if __name__ == '__main__':
    main()

