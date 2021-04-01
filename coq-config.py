#!/usr/bin/env python

from icecream import ic

import stackprinter
stackprinter.set_excepthook(style='darkbg2')

import click

@click.command()
@click.version_option("1.0")
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.option("--dry-run", "-n", is_flag=True, help="Do not modify anything.")
def main(verbose, dry_run):
    ic(verbose)
    
if __name__ == '__main__':
    main()

