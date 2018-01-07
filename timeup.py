# configuration
backup_destination = "/Volumes/BBackup/Backups.timeup/"
lockfile = "/Users/bb/.timeup.pid"

hours_to_keep_all = 48
days_to_keep_dailies = 14
weeks_to_keep_weeklies = -1

backup_directories = ["/Users/bb/Documents/",
                      "/Users/bb/eBooks/",
                      "/Users/bb/Movies/",
                      "/Users/bb/Music/",
                      "/Users/bb/Projects/",
                      "/Users/bb/Projects-Archive"]

# -------------------------------------------------------------------------- #

import os
import datetime
import subprocess
import pathlib
import argparse
import shutil


class LockFile:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        if self.path.exists():
            with open(self.path) as f:
                pid = int(f.read())
            try:
                # will not work on Windows:
                os.kill(pid, 0)
            except OSError:
                # lockfile exists, but no process is running
                pass
            else:
                # lockfile exists, and process is running
                raise RuntimeError("Another instance of timeup is running already")

        with open(self.path, 'w') as f:
            f.write(os.getpid())

    def __exit__(self):
        self.path.unlink()


def create_backup(destination, directories):
    all_backups = {datetime.datetime(str(d)):d for d in destination.iterdir()}
    newest_backup = all_backups[max(all_backups.keys())]

    destination /= datetime.now().isoformat()

    proc = subprocess.run(['rsync',
                           '-a', # preserve as much as possible
                           '-v', # verbose
                           '--link-dest', str(newest_backup),
                           *(str(d) for d in directories),
                           str(destination)])
    try:
        proc.check_returncode()
    except CalledProcessError:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def prune_backups(destination, hours_to_keep_all, days_to_keep_dailies, weeks_to_keep_weeklies):
    all_backups = {datetime.datetime(str(d)):d for d in destination.iterdir()}

    now = datetime.now()
    keep_all = [dt for dt in sorted(all_backups.keys())
                if now - dt < datetime.timedelta(hours=hours_to_keep_all)]
    remaining_backups = set(all_backups.keys()) - keep_all

    keep_daylies = []
    for day in range(days_to_keep_dailies):
        date = (now - datetime.timedelta(days=day)).date()
        backups = [dt for dt in remaining_backups
                   if dt.date() == date]
        keep_daylies.append(max(backups))

    keep_weeklies = []
    for week in range(weeks_to_keep_weeklies):
        date = (now - datetime.timedelta(weeks=week)).date()
        backups = [dt for dt in remaining_backups
                   if dt.year == date.year and
                      # compare week number:
                      dt.isocalendar()[1] == date.isocalendar[1]]
        keep_weeklies.append(max(backups))

    keep = set(keep_all + keep_daylies + keep_weeklies)
    delete = set(all_backups.keys()) - keep

    for d in delete:
        shutil.rmtree(all_backups[d], ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(prog='timeup', description="Create backups, and keep regular copies")
    parser.add_argument('-h', '--hours', action='store', type=int, default=48)
    parser.add_argument('-d', '--days', action='store', type=int, default=14)
    parser.add_argument('-w', '--weeks', action='store', type=int, default=-1)
    parser.add_argument('-l', '--lockfile', action='store', type=pathlib.Path, default='~/.timeup.pid')
    parser.add_argument('destination', type=pathlib.Path, action='store')
    parser.add_argument('directories', type=pathlib.Path, nargs=argparse.REMAINDER)
    args = parser.parse_args()

    with LockFile(args.lockfile):
        create_backup(args.destination, args.directories)
        prune_backups(args.destination, args.hours, args.days, args.weeks)


if __name__ == "__main__":
    main()
