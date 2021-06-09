
"""
The majority of the code for this command line entry point is borrowed from the eralchemy codebase found here:
    https://github.com/Alexis-benoist/eralchemy

"""

from __future__ import print_function
import argparse
import sys

__version__ = 0,0,1

# from https://github.com/mitsuhiko/flask/blob/master/scripts/make-release.py L92
def fail(message, *args):
    print('Error:', message % args, file=sys.stderr)
    sys.exit(1)


def check_args(args):
    """Checks that the args are coherent."""
    check_args_has_attributes(args)
    if args.v:
        non_version_attrs = [v for k, v in args.__dict__.items() if k != 'v']
        print('non_version_attrs', non_version_attrs)
        if len([v for v in non_version_attrs if v is not None]) != 0:
            fail('Cannot show the version number with another command.')
        return
    if args.i is None:
        fail('Cannot draw ER diagram of no database.')
    if args.o is None:
        fail('Cannot draw ER diagram with no output file.')


def check_args_has_attributes(args):
    check_args_has_attribute(args, 'i')
    check_args_has_attribute(args, 'o')
    check_args_has_attribute(args, 'include_tables')
    check_args_has_attribute(args, 'include_columns')
    check_args_has_attribute(args, 'exclude_tables')
    check_args_has_attribute(args, 'exclude_columns')
    check_args_has_attribute(args, 's')


def check_args_has_attribute(args, name):
    if not hasattr(args, name):
        raise Exception('{} should be set'.format(name))


def cli():
    """Entry point for the application script"""
    parser = get_argparser()

    args = parser.parse_args()
    check_args(args)
    if args.v:
        print(f'ACME version {".".join(str(v) for v in __version__)}.')
        exit(0)


def get_argparser():
    parser = argparse.ArgumentParser(prog='ERAlchemy')
    parser.add_argument('-i', nargs='?', help='Database URI to process.')
    parser.add_argument('-o', nargs='?', help='Name of the file to write.')
    parser.add_argument('-s', nargs='?', help='Name of the schema.')
    parser.add_argument('--exclude-tables', '-x', nargs='+', help='Name of tables not to be displayed.')
    parser.add_argument('--exclude-columns', nargs='+', help='Name of columns not to be displayed (for all tables).')
    parser.add_argument('--include-tables', nargs='+', help='Name of tables to be displayed alone.')
    parser.add_argument('--include-columns', nargs='+', help='Name of columns to be displayed alone (for all tables).')
    parser.add_argument('-v', help='Prints version number.', action='store_true')
    return parser