#!/usr/bin/env python

import os
from datetime import datetime, timedelta
import subprocess
import pathlib
import argparse
import shutil
import errno

import sys
if sys.version_info < (3, 0):
    str = unicode


class LockFile:
    def __init__(self, path):
        if str(path) == '__donotlock__': # no lock file given
            self.path = None
        else:
            self.path = path

    def __enter__(self):
        if self.path is None:
            return

        if self.path.exists():
            with self.path.open() as f:
                content = f.read()

            if not content:
                # lockfile exists, but is empty
                self.path.unlink()
                return

            pid = int(content)
            try:
                # will not work on Windows:
                os.kill(pid, 0)
            except OSError as err:
                if err.errno == errno.ESRCH:
                    # lockfile exists, but no process is running
                    self.path.unlink()
                else:
                    # lockfile exists, and process is running
                    raise RuntimeError("Another instance of timeup is running already")
            else:
                # lockfile exists, and process is running
                raise RuntimeError("Another instance of timeup is running already")

        with self.path.open('w') as f:
            f.write(str(os.getpid()))

    def __exit__(self, *args):
        if self.path is None:
            return

        self.path.unlink()


def all_backup_dirs(destination, fileformat):
    """Return a list of Paths in `destination` that conform to
    `fileformat` where existing backups are stored.

    """

    dirs = []
    for d in destination.iterdir():
        try:
            datetime.strptime(d.name, fileformat)
            dirs.append(d)
        except ValueError:
            pass
    return dirs


def create_backup(destination, directories, fileformat):
    """Create a new backup of `directories` in `destination`, naming the
    backup according to `fileformat`, and hard-linking to the most
    recent existing backup.

    """

    if not destination.exists():
        destination.mkdir()

    new_backup = destination / datetime.now().strftime(fileformat)
    args = ['rsync', '-a'] # preserve as much as possible

    all_backups = {datetime.strptime(d.name, fileformat):d for d in
                   all_backup_dirs(destination, fileformat)}
    if all_backups:
        newest_backup = all_backups[max(all_backups.keys())]
        args += ['--link-dest', str(newest_backup)]

    try:
        subprocess.check_call(args + [str(d) for d in directories] + [str(new_backup)])
    except Exception:
        # remove partial backup:
        shutil.rmtree(new_backup, ignore_errors=True)
        raise


def prune_backups(destination, hours_to_keep_all, days_to_keep_dailies, weeks_to_keep_weeklies, fileformat):
    """Delete backups called `fileformat` from `destination` such that all
    backups from the last `hours_to_keep_all` hours are preserved, one
    backup per day from the last `days_to_keep_dailies` days are
    preserved, and one backup per week from the last
    `weeks_to_keep_weeklies` weeks are preserved.

    """

    all_backups = {datetime.strptime(d.name, fileformat):d for d in
                   all_backup_dirs(destination, fileformat)}

    now = datetime.now()
    if hours_to_keep_all == -1:
        hours_to_keep_all = (now - min(all_backups.keys())).hours + 1
    if days_to_keep_dailies == -1:
        days_to_keep_dailies = (now - min(all_backups.keys())).days + 1
    if weeks_to_keep_weeklies == -1:
        weeks_to_keep_weeklies = (now - min(all_backups.keys())).days // 7 + 1

    keep_all = {dt for dt in all_backups.keys()
                if now - dt < timedelta(hours=hours_to_keep_all)}

    keep_daylies = set()
    for day in range(days_to_keep_dailies):
        date = (now - timedelta(days=day)).date()
        backups = [dt for dt in all_backups
                   if dt.date() == date]
        if backups:
            keep_daylies.add(min(backups)) # keep the oldest backup of the day

    keep_weeklies = set()
    for week in range(weeks_to_keep_weeklies):
        date = (now - timedelta(weeks=week)).date()
        backups = [dt for dt in all_backups
                   if dt.year == date.year and
                      # compare week number:
                      dt.isocalendar()[1] == date.isocalendar()[1]]
        if backups:
            keep_weeklies.add(min(backups)) # keep the oldest backup of the week

    keep = keep_all | keep_daylies | keep_weeklies
    delete = set(all_backups.keys()) - keep

    for d in delete:
        shutil.rmtree(all_backups[d], ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(prog='timeup', description=
                                     "Create backups, and keep regular copies."
                                     "By default, this keeps "
                                     "all backups from the last 48 hours, "
                                     "one daily backup for the last 14 days, "
                                     "and infinite weekly backups.")
    parser.add_argument('--hours', action='store', type=int, default=48,
                        help="Keep all backup for this many hours. "
                        "Keep all backups if -1. Default is 48.")
    parser.add_argument('--days', action='store', type=int, default=14,
                        help="Keep daily backups for this many days. "
                        "Keep all daily backups if -1. Default is 14.")
    parser.add_argument('--weeks', action='store', type=int, default=-1,
                        help="Keep weekly backups for this many weeks. "
                        "Keep all weekly backups if -1. Default is -1.")
    parser.add_argument('--format', action='store', type=str, default="%Y-%m-%dT%H:%M:%S",
                        help="`strftime` format string for backups. "
                        "Default is ISO 8601: `%%Y-%%m-%%dT%%H:%%M:%%S`.")
    parser.add_argument('-l', '--lockfile', action='store', type=pathlib.Path, default='__donotlock__',
                        help="Makes sure that only one timeup is running at a time.")
    parser.add_argument('destination', type=pathlib.Path, action='store',
                        help="Where backups are stored")
    parser.add_argument('target', type=pathlib.Path, nargs='+',
                        help="What directories are backed up")
    args = parser.parse_args()

    with LockFile(args.lockfile):
        create_backup(args.destination, args.target, args.format)
        prune_backups(args.destination, args.hours, args.days, args.weeks, args.format)


if __name__ == "__main__":
    main()
