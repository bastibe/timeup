# TimeUp

Creates incremental backups, and thins them out the older they get. By default, it will keep all backups you make for 48 hours, then keep daily backups for 14 days, and after that, keep all weekly backups. Each backup is a complete, self-contained clone of the original directories. To save space, unchanged files are hard-linked to the previous backup.

Create your first backup using

```bash
./timeup.py -l /path/to/lockfile.pid /save/backups/here/ /back/this/up/ /and/this/too/
```

Then run the same script hourly with `cron` or `systemd` or `launchd`, and it will create directories like this:

```
/save/backups/here/2018-01-01T00:00:00/back/this/up/
/save/backups/here/2018-01-01T00:00:00/and/this/too/

/save/backups/here/2018-01-01T01:00:00/back/this/up/
/save/backups/here/2018-01-01T01:00:00/and/this/too/

/save/backups/here/2018-01-01T02:00:00/back/this/up/
/save/backups/here/2018-01-01T02:00:00/and/this/too/

/save/backups/here/2018-01-01T03:00:00/back/this/up/
/save/backups/here/2018-01-01T03:00:00/and/this/too/
```

After 48 hours, it will start deleting older backups so that only one backup per day remains. After another 14 days, it will delete some of those, so that only one backup per week remains.

## Configuration

You can customize the number of hours where all backups are kept using the `--hours` switch, the number of days for daily backups with `--days`, the number of weeks for weekly backups with `--weeks`. If any of these is set to `-1`, it will keep all of them. By default, all weekly backups are kept.

You need to specify a lock file to ensure that only one instance of timeup is running at any one time. You can store this file anywhere you want, as long as you have write access to that location. If no lock file is given, timeup will not lock, which might lead to errors if more than one instance is running at the same time.

## Schedule

### systemd (Linux)

create two files in `/etc/systemd/system/`:

timeup.timer:
```
[Unit]
Description=Run hourly backup

[Timer]
OnCalendar=hourly

[Install]
WantedBy=multi-user.target
```

timeup.service:
```
[Unit]
Description=Run hourly backup

[Service]
Type=simple
ExecStart=/path/to/timeup.py -l /path/to/lockfile.pid /save/backups/here/ /back/this/up/ /and/this/too/
```

### launchctl (macOS)

Under Construction...

## FAQ

- Does timeup work on Windows?  
  no
