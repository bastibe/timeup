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

You need to specify a lock file with `-l` to ensure that only one instance of timeup is running at any one time. You can store this file anywhere you want, as long as you have write access to that location. If no lock file is given, timeup will not lock, which might lead to errors if more than one instance is running at the same time.

If you want to change the directory names, you can use `--format`, and supply any `strftime`-compatible format string. This is particularly necessary on file systems that don't support `:` in file names.

## Schedule

### systemd (Linux)

create two files in `/etc/systemd/system/`:

timeup.timer:
```ini
[Unit]
Description=Run hourly backup

[Timer]
OnCalendar=hourly

[Install]
WantedBy=multi-user.target
```

timeup.service:
```ini
[Unit]
Description=Run hourly backup

[Service]
Type=simple
ExecStart=/path/to/timeup.py -l /path/to/lockfile.pid /save/backups/here/ /back/this/up/ /and/this/too/
```

Since the first backup will take some time, let's run it manually first:
```
systemctl start timeup.service
```

Then enable the timer with
```
systemctl enable timeup.timer
```

### launchd (macOS)

On macOS, there are a few issues:
- macOS ships only Python 2.7, which lacks a required library
- The file system does not support `:` in file names

Thus, we need to install the missing library:
```
sudo /usr/bin/easy_install pathlib
```

And write a configuration file in `~/Library/LaunchAgents/` that changes the naming pattern:

timeup.plist:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>timeup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/timeup.py</string>
        <string>-l</string>
        <string>/path/to/lockfile.pid</string>
        <string>--format</string>
        <string>%Y-%m-%dT%H.%M.%S</string>
        <string>/save/backups/here/</string>
        <string>/back/this/up/</string>
        <string>/and/this/too/</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

Then load the agent file:
```
launchctl load ~/Library/LaunchAgents/timeup.plist
```

And start the service once:
```
launchctl start timeup
```

If backups are not being created, check in Console.app if there is an error, or add

```xml
<key>StandardErrorPath</key>
<string>/path/to/error-file</string>
```

to the configuration file.

## FAQ

- Does timeup work on Windows?  
  no.  
  Apparently, there are Windows versions of `rsync` available, most
  notably in msys2, cygwin, and WSL. I know that at least
  `os.kill(pid, 0)` does not work on Windows, though. This part could
  simply be disabled without much trouble. Pull Requests are welcome.

- Does timeup work with Python 2?  
  maybe.  
  It seems to work on my Mac, but I haven't tested it thoroughly.
