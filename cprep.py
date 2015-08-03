#!/usr/bin/env python

from __future__ import absolute_import, division, print_function

import argparse, functools, os, re, sys

COLUMNS = 80
SUFFIXES = '.cpp', '.h', '.inl'

SPLIT = re.compile(r'([]().]|\s)').split

def remove_terminal_whitespace(data, _):
    return '\n'.join(s.rstrip() for s in data.splitlines()) + '\n'

# http://stackoverflow.com/questions/16052862
def tabstop (s, tabnum=4):
    if '\t' not in s:
        return s
    l = s.find('\t')
    return s[0:l]+' '*(tabnum-l)+tabstop(s[l+1:],tabnum)

def remove_tabs(data, _):
    return '\n'.join(tabstop(s) for s in data.splitlines()) + '\n'

def split_line(line, width, indent):
    segment = ['']
    result = []

    def consume(part=''):
        if segment[0] or part:
            result.append(indent + segment[0] + part)
        segment[0] = ''

    def debug(label):
        pass # print(label, '->', result, segment[0], part)

    for part in SPLIT(line):
        if len(part) + len(segment[0]) <= width:
            debug(1)
            segment[0] += part
        else:
            debug(2)
            consume()
            debug(3)
            if len(part) >= width:
                debug(4)
                consume(part)
            else:
                debug(5)
                segment[0] = part
    consume()  # Emit any last short segment.
    return result


def split_by_columns(data, fname):
    result = []
    for line in data.splitlines():
        line = line.rstrip()
        if len(line) <= COLUMNS:
            result.append(line)
            continue

        print('%s:%d:%s' % (fname, len(result) + 1, line))

        body = line.lstrip()
        indent = len(line) - len(body)
        width = COLUMNS - indent
        result += split_line(body, width, indent * ' ')
    return '\n'.join(result) + '\n'

COMMAND_TABLE = {
    'identity': lambda data, _: data,
    'change': lambda data, _: data + '\n',
    'space': remove_terminal_whitespace,
    'split': split_by_columns,
    'tabs': remove_tabs,
}

def get_args():
    parser = argparse.ArgumentParser(
        prog='cprep',
        description='Search and replace in cpp files.',
        )

    # Positional arguments.
    parser.add_argument(
        'commands',
        nargs='*',
        help='Commands to apply to CPP files.'
    )

    # Flag arguments

    parser.add_argument(
        '--root',
        default='.',
        help="Where do we search for files?",
    )
    parser.add_argument(
        '--noexecution', '-n',
        action='store_true',
        help='If set, print the changed files but don\'t change them.',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print the changed files but don\'t change them.',
    )

    return parser.parse_args()

ARGS = get_args()

def validate():
    failures = [c for c in ARGS.commands if c not in COMMAND_TABLE]
    if failures:
        raise ValueError('Don\'t understand: ' + ', '.join(failures))

def run_on_file(function, fname):
    data = open(fname, 'r').read()
    result = function(data, fname)
    if data != result:
        if ARGS.noexecution or ARGS.verbose:
            print(fname)
        if not ARGS.noexecution:
            open(fname, 'w').write(result)


def for_each_file(function, matcher):
    for root, _, files in os.walk(ARGS.root):
        for f in files:
            fname = os.path.join(root, f)
            if matcher(fname):
                run_on_file(function, fname)

def cprep():
    if not ARGS.commands:
        print('Valid commands are:', ', '.join(sorted(COMMAND_TABLE)))
    validate()
    functions = [COMMAND_TABLE[c] for c in ARGS.commands]
    def function(data, fname):
        for f in functions:
            data = f(data, fname)
        return data

    def matcher(fname):
        for s in SUFFIXES:
            if fname.endswith(s):
                return True

    for_each_file(function, matcher)

if __name__ == '__main__':
    cprep()
