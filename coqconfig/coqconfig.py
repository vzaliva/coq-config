#!/usr/bin/env python

import os
import sys
import subprocess
from cerberus import Validator
import click

# Uncomment for debugging
#from icecream import ic

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

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
        'schema': {"anyof":[
            {'type': 'string'},
            {'type': 'dict',
                'schema': {
                    'name': {
                        'required': True,
                        'type': 'string',
                    },
                    'kind': {
                        'required': True,
                        'type': 'string',
                    },
                    'target': {
                        'required': True,
                        'type': 'string',
                    }
                }}
        ]}
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
                'recurse-submodules': {
                    'required': False,
                    'type': 'boolean',
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

OPAMROOT = "~/.opam"

def opam_get_switches(verbose):
    if verbose:
        print("Checking OPAM switches")
    try:
        switches = subprocess.check_output(["opam", "switch", "list", "-s"], text=True)
    except subprocess.CalledProcessError:
        print("Error getting list of OPAM switches")
        sys.exit(2)
    return list(map(str.strip, switches.split('\n')))

def opam_get_repositoris(verbose, switch):
    if verbose:
        print("Checking OPAM repositories")
    try:
        repos = subprocess.check_output(["opam", "repo", "list", "-s", ("--on-switches=%s"%switch)], text=True)
    except subprocess.CalledProcessError:
        print("Error getting list of OPAM repositories")
        sys.exit(2)
    return list(map(str.strip, repos.split('\n')))


def opam_check(verbose):
    # Check if opam initialized
    if verbose:
        print("Checking OPAM presence")
    if not os.path.exists(os.path.expanduser(OPAMROOT)):
        print("OPAM is not initialized. Please set up OPAM with `opam init`.")
        sys.exit(2)

def load_config(verbose, cfgfile):
    if not os.path.exists(cfgfile):
        print("'%s' not found" % cfgfile)
        sys.exit(1)
    if verbose:
        print("Loading '%s'" % cfgfile)
    try:
        with open(cfgfile, "r") as f:
            cfg = load(f, Loader=Loader)
            v = Validator(SCHEMA)
            if not v.validate(cfg, SCHEMA):
                print("Invalid config '%s'" % cfgfile)
                print(v.errors)
                sys.exit(1)
            else:
                return cfg

    except: # pylint: disable=bare-except
        print("Error reading '%s'" % cfgfile)
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
    except subprocess.CalledProcessError:
        print("Error creating OPAM switch")
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
    except subprocess.CalledProcessError:
        print("Error adding OPAM repository")
        sys.exit(3)

def opam_install_packages(verbose, dry_run, jobs, switch, packages):
    pnames = [p if type(p) == str else p['name'] for p in packages]
    pkgs = " ".join(pnames)
    if verbose:
        print("Installing: %s" % pkgs)
    try:
        cmd = ["opam", "install", "--yes", ("--switch=%s"%switch)]
        if dry_run:
            cmd.append("--dry-run")
        if jobs is not None:
            cmd.append("--jobs=%d" % jobs)
        cmd.extend(pnames)
        if verbose and dry_run:
            print("DRY RUN: %s" % " ".join(cmd))
        subprocess.check_call(cmd)
        if verbose:
            print("Installed: %s" % pkgs)
    except subprocess.CalledProcessError:
        print("Error installing pakages")
        sys.exit(3)

def opam_pin_packages(verbose, dry_run, switch, packages):
    for p in packages:
        if type(p) == str:
            p2 = p.split('.',1)
            if len(p2)==2:
                # package has version number
                pn = p2[0]
                pt = p2[1]
                pk = "auto"
            else:
                continue # no pinning required
        else:
            pn = p['name']
            pt = p['target']
            pk = p['kind']
        
        if verbose:
            print("Pinning: %s" % pn)
        cmd = ["opam", "pin", "--yes", "--no-action", ("--switch=%s"%switch), ("--kind=%s"%pk)]
        if dry_run:
            cmd.append("--dry-run")
        cmd.append(pn)
        cmd.append(pt)
        try:
            subprocess.check_call(cmd)
            if verbose:
                print("Pinned: %s" % p)
        except subprocess.CalledProcessError:
            print("Error pinnig pakage")
            sys.exit(3)
        
def git_clone(verbose, dry_run, path, git_url, rs):
    if verbose:
        print("Cloning from git '%s'" % git_url)
    if rs:
        cmd = ["git", "clone", "--recurse-submodules", git_url, path]
    else:
        cmd = ["git", "clone", "-n", git_url, path]
    try:
        if dry_run:
            print("DRY RUN: %s" % " ".join(cmd))
        else:
            subprocess.check_call(cmd)
        if verbose:
            print("Cloned '%s' to '%s'" % (git_url, path))
    except subprocess.CalledProcessError:
        print("Error performing git clone")
        sys.exit(3)

def git_checkout(verbose, dry_run, path, commit, rs):
    if verbose:
        print("Checking out at '%s'" % path)
    cmd = ["git", "checkout"]
    if rs:
        cmd.append("--recurse-submodules")
    if commit is not None:
        cmd.append(commit)
    try:
        if dry_run:
            print("DRY RUN: %s" % " ".join(cmd))
        else:
            subprocess.check_call(cmd, cwd=path)
        if verbose:
            print("Checked out at '%s'" % path)
    except subprocess.CalledProcessError:
        print("Error performing git checkout")
        sys.exit(3)
        
CONFIG = "coq_config.yaml"

@click.command()
@click.version_option("1.0")
@click.option('--verbose', '-v', is_flag=True, help='Enables verbose mode.')
@click.option('--dry-run', '-n', is_flag=True, help='Do not modify anything.')
@click.option('--config', '-f', default=CONFIG, help='File name to use instead of `%s`'%CONFIG)
@click.option('--jobs','-j', type=int, help='Set the maximal number of concurrent jobs to use')
@click.option('--switch', '-s', help='Use existing switch')
def main(verbose, dry_run, config, jobs, switch):
    cfg = load_config(verbose, config)
    opam_check(verbose)
    switches = opam_get_switches(verbose)

    if switch is None:
        switch = cfg['opam']['switch']
        if switch in switches:
            if verbose:
                print("Switch '%s' found" % switch)
        else:
            opam_switch_create(verbose, dry_run, switch, cfg['opam']['compiler'])
    else:
        if switch in switches:
            if verbose:
                print("Using existing switch '%s'" % switch)
        else:
            print("Switch does not exist '%s'" % switch)
            exit(1)

    repos = opam_get_repositoris(verbose, switch)
    for r in cfg.get('repositories',[]):
        rn = r['name']
        if rn in repos:
            if verbose:
                print("Repository '%s' found" % rn)
        else:
            opam_repo_add(verbose, dry_run, switch, rn, r['address'])

    opam_pin_packages(verbose, dry_run, switch, cfg.get('dependencies', []))
    
    opam_install_packages(verbose, dry_run, jobs, switch, cfg.get('dependencies', []))
    
    for d in cfg.get('extra-deps', []):
        p = d['path']
        rs = d.get('recurse-submodules', False)
        if not os.path.exists(p):
            git_clone(verbose, dry_run, p, d['git'], rs)
        git_checkout(verbose, dry_run, p, d.get('commit', None), rs)
            
    sys.exit(0)

if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()
