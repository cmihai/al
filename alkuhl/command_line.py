from __future__ import print_function
import sys
import os

import click
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.script import ScriptDirectory


config = None
script = None


def mark():
    if sys.stdout.isatty():
        sys.stdout.write('\x1b[32m')


def unmark():
    if sys.stdout.isatty():
        sys.stdout.write('\x1b[0m')


def rev(rev_id): return script.get_revision(rev_id)


def replace(path, before, after):
    with open(path, 'r') as f:
        contents = f.read()
    with open(path, 'w') as f:
        f.write(contents.replace(before, after))


@click.group()
def main():
    global config, script
    config = Config('alembic.ini')
    script = ScriptDirectory.from_config(config)


@main.command()
def history():
    """ Display the revision history """
    def _history(rev, context):
        current = context.get_current_revision()
        rev_id = script.get_current_head()

        while rev_id != script.get_base():
            if current == rev_id:
                mark()
                print('* ', end='')
            else:
                print('  ', end='')

            rev = script.get_revision(rev_id)
            print('{} {}'.format(rev_id, rev.doc))

            if current == rev_id:
                unmark()

            rev_id = rev.down_revision
        return []

    with EnvironmentContext(config, script, fn=_history):
        script.run_env()


@main.command()
@click.argument('from')
@click.argument('to')
def rename(**kwargs):
    """ Change a revision's ID """
    from_, to = kwargs.get('from'), kwargs.get('to')

    def _rename(rev, context):
        from_rev = script.get_revision(from_)
        from_path = from_rev.path
        to_path = from_path.replace(from_, to)

        for rev_id in from_rev.nextrev:
            replace(script.get_revision(rev_id).path, from_, to)
        replace(from_path, from_, to)
        replace(
            script.get_revision(from_rev.down_revision).path, from_, to
        )
        os.rename(from_path, to_path)

        return []

    with EnvironmentContext(config, script, fn=_rename):
        script.run_env()


@main.command()
@click.argument('revision')
@click.argument('after')
def move(revision, after):
    """ Reorder revisions """
    # P(ver) -> ver -> C(ver) ... P(after) -> after -> C(after)
    # becomes
    # P(ver) -> C(ver) ... P(after) -> after -> ver -> C(after)

    if revision == after:
        print(
            "Cannot move revision {0} after itself".format(revision),
            file=sys.stderr
        )
        sys.exit(1)

    def _move(r, ctx):
        what_rev, after_rev = rev(revision), rev(after)
        pwhat_id, cwhat_ids = what_rev.down_revision, list(what_rev.nextrev)
        cafter_ids = list(after_rev.nextrev)

        for rev_id in cwhat_ids:
            replace(rev(rev_id).path, revision, pwhat_id)
        replace(what_rev.path, pwhat_id, after)
        for rev_id in cafter_ids:
            replace(rev(rev_id).path, after, revision)

        return []

    with EnvironmentContext(config, script, fn=_move):
        script.run_env()
