#!/usr/bin/env python

import os
import sys
import subprocess
from cerberus import Validator
from icecream import ic
import click
import stackprinter

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

stackprinter.set_excepthook(style='darkbg2')

SCHEMA = {
    'opam': {
        'required': True,
        'type': 'dict',
        'schema': {
            'switch': {
                'required': True,
                'type': 'string',
            },
            'compiler': {
                'required': True,
                'type': 'string',
            }
        }
    },
    'dependencies' : {
        'type': 'list',
        'required': False,
        'schema': {'type': 'string'}
    },
    'extra-deps' : {
        'type': 'list',
        'required': False,
        'schema': {
            'type' : 'dict',
            'schema': {
                'git': {
                    'required': True,
                    'type': 'string',
                },
                'commit': {
                    'required': False,
                    'type': 'string',
                },
                'path': {
                    'required': True,
                    'type': 'string',
                }
            }
        }
    },
    'repositories' : {
        'type': 'list',
        'required': False,
        'schema': {
            'type' : 'dict',
            'schema': {
                'name': {
                    'required': True,
                    'type': 'string',
                },
                'address': {
                    'required': True,
                    'type': 'string',
                }
            }
        }
    }
}

CONFIG = "coq_config.yaml"
OPAMROOM = "~/.opam"

def opam_get_switches(verbose):
    if verbose:
        print("Checking OPAM switches")
    try:
        switches = subprocess.check_output(["opam", "switch", "list", "-s"], text=True)
    except:
        print("Error getting list of OPAM switches")
        stackprinter.show()
        sys.exit(2)
    return list(map(str.strip, switches.split('\n')))

def opam_get_repositoris(verbose, switch):
    if verbose:
        print("Checking OPAM repositories")
    try:
        repos = subprocess.check_output(["opam", "repo", "list", "-s", ("--on-switches=%s"%switch)], text=True)
    except:
        print("Error getting list of OPAM repositories")
        stackprinter.show()
        sys.exit(2)
    return list(map(str.strip, repos.split('\n')))


def opam_check(verbose):
    # Check if opam initialized
    if verbose:
        print("Checking OPAM presence")
    if not os.path.exists(os.path.expanduser(OPAMROOM)):
        print("OPAM is not initialized. Please set up OPAM with `opam init`.")
        sys.exit(2)

def load_config(verbose):
    if not os.path.exists(CONFIG):
        print("'%s' not found" % CONFIG)
        sys.exit(1)
    if verbose:
        print("Loading '%s'" % CONFIG)
    try:
        with open(CONFIG, "r") as f:
            cfg = load(f, Loader=Loader)
            v = Validator(SCHEMA)
            if not v.validate(cfg, SCHEMA):
                print("Invalid config '%s'" % CONFIG)
                print(v.errors)
                sys.exit(1)
            else:
                return cfg
    except:
        print("Error reading '%s'" % CONFIG)
        stackprinter.show()
        sys.exit(1)

def opam_switch_create(verbose, dry_run, switch, compiler):
    if verbose:
        print("Creating switch '%s'" % switch)
        cmd = ["opam", "switch", "create", "--no-switch", switch, compiler]
    try:
        if dry_run:
            print("DRY RUN: %s" % " ".join(cmd))
        else:
            subprocess.check_call(cmd)
        if verbose:
            print("Switch '%s' successfully created" % switch)
    except:
        print("Error creating OPAM switch")
        stackprinter.show()
        sys.exit(3)

def opam_repo_add(verbose, dry_run, switch, rn, ra):
    if verbose:
        print("Adding repository '%s'" % rn)
        cmd = ["opam", "repo", "add", rn, ra, ("--on-switches=%s"%switch)]
    try:
        if dry_run:
            print("DRY RUN: %s" % " ".join(cmd))
        else:
            subprocess.check_call(cmd)
        if verbose:
            print("Repository '%s' successfully created" % rn)
    except:
        print("Error adding OPAM repository")
        stackprinter.show()
        sys.exit(3)
        
@click.command()
@click.version_option("1.0")
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.option("--dry-run", "-n", is_flag=True, help="Do not modify anything.")
def main(verbose, dry_run):
    cfg = load_config(verbose)
    opam_check(verbose)
    switches = opam_get_switches(verbose)
    switch = cfg['opam']['switch']
    if switch in switches:
        if verbose:
            print("Switch '%s' found" % switch)
    else:
        opam_switch_create(verbose, dry_run, switch, cfg['opam']['compiler'])

    repos = opam_get_repositoris(verbose, switch)
    ic(repos)
    for r in cfg['repositories']:
        rn = r['name']
        if rn in repos:
            if verbose:
                print("Repository '%s' found" % rn)
        else:
            opam_repo_add(verbose, dry_run, switch, rn, r['address'])

    sys.exit(0)

if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()
