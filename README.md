# Coq-config

Simple script to set up a Coq project dependencies using *opam*.
Inspired by Haskell's `stack`.

## Documentation

Reads `coq_config.yaml` file and set up am *opam* *switch* and install
required packages.

Optionally checks out some sub-projects from *git* (an alternative
to using sub-modules).

### Notes

-   It is safe to run multiple times.
-   The *opam* packages where the version numer was specified, will be
    pinned, so it is safe to do `opam update` aftewards.
-   You will need to activate opam switch specified in config with
    `opam switch` command. The script does not change current active
    switch for you.
-   Tested with *opam* verson 2.0.5.

## To-Do

-   Run `opam init` if necessary
-   If switch exists, check if the right compiler is used and
    update if necessary.
-   When adding repositories, check their URLs, not just names.
    It they do not match the config - report errror.
-   Run `coq-config` for all `extra-deps`
-   pass-through "-j" command line option
-   When re-running, make sure pinned version removed or updated
    if changed.

## Installation

The easiets way to install is using `pip`:

`pip install coq-config`

### Manual install

To run from local clone of git repository install dependencies (using
`pip`):

-   click
-   pyyaml
-   cerberus


