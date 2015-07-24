#!/usr/bin/env python

from __future__ import absolute_import, division, print_function

# Don't include unicode_literals to improve legacy code.

import argparse
import os
import sys

SUFFIXES = '.cpp', '.h', '.inl'

COMMAND_TABLE = {}

def get_args():
    parser = argparse.ArgumentParser(
        prog='cprep',
        description='Search and replace in cpp files.',
        )

    # Positional arguments.
    parser.add_argument(
        'commands',
        nargs='+',
        help='Commands to apply to CPP files.'
    )

    # Flag arguments

    parser.add_argument(
        '--root',
        default='.',
        help="Where do we search for files?",
    )
    return parser.parse_args()


def validate(commands):
    failures = [c for c in commands if c not in COMMAND_TABLE]
    if failures:
        raise ValueError('Don\'t understand: ' + ', '.join(failures))

def run_on_file(function, fname):
    data = open(fname, 'r').read()
    result = function(data)
    if data != result:
        open(fname, 'w').write(result)


def for_each_file(function, root, matcher):
    for root, _, files in os.walk(root):
        for f in files:
            fname = os.path.join(root, f)
            if matcher(fname):
                run_on_file(function, fname)

def cprep(args):
    validate(args.commands)
    functions = [COMMAND_TABLE[c] for c in args.commands]
    def function(data):
        for f in functions:
            data = f(data)
        return data

    def matcher(fname):
        for s in SUFFIXES:
            if fname.endswith(s):
                return True

    for_each_file(function, args.root, matcher)

if __name__ == '__main__':
    cprep(get_args())
