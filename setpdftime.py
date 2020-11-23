#!/usr/bin/env python3
""" Set PDF file mtime to ModDate from PDF metadata, CC0 license """

import re
import argparse
import datetime
import subprocess
import os

# Set to location of pdftk program
PDFTKPATH = "/usr/bin/pdftk"


def set_file_mtime(filename, mtime):
    """ Set the modification time of a given filename to the given mtime """
    stat = os.stat(filename)
    atime = stat.st_atime
    os.utime(filename, times=(atime, mtime.timestamp()))


def processtimestamp(line, filename):
    """ Extract timestamp from line """
    match = TIMESTAMP.match(line)
    if match:
        date_time = match.group(1)
        time_zone = match.group(2)
        year = int(date_time[0:4])
        month = int(date_time[4:6])
        day = int(date_time[6:8])
        hour = int(date_time[8:10])
        minute = int(date_time[10:12])
        second = int(date_time[12:14])
        tzoff = datetime.timedelta(hours=int(time_zone))
        mtime = datetime.datetime(
            year, month, day, hour, minute, second, tzinfo=datetime.timezone(tzoff))
        if ARGS.verbose:
            print(f"touch -c -d '{mtime.isoformat()}' {filename}")
        if ARGS.doit:
            set_file_mtime(filename, mtime)


def processfile(filename):
    """ Process one file argument """
    with open(filename) as file_handle:
        file_handle.close()
        expecttimestamp = False
        with subprocess.Popen(
            [PDFTKPATH, filename, "dump_data", "output", "-"],
            stdout=subprocess.PIPE, universal_newlines=True) as pdftk:
            for line in pdftk.stdout:
                if line.startswith("InfoKey: ModDate"):
                    expecttimestamp = True
                if expecttimestamp and line.startswith("InfoValue"):
                    processtimestamp(line, filename)
                    return
    print(f"No ModDate metadata found for {filename}")


TIMESTAMP = re.compile(r"InfoValue: D:(\d{14})([-+]\d{2})")
PARSER = argparse.ArgumentParser(
    description='Set PDF file modification time to ModDate value in metadata')
PARSER.add_argument('filenames', metavar='file', nargs='+', help='PDF file')
PARSER.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    help='show equivalent touch command')
PARSER.add_argument('-n', '--no-run', dest='doit', action='store_false',
                    help='don\'t actually change the modification time')
ARGS = PARSER.parse_args()
for FILENAME in ARGS.filenames:
    try:
        processfile(FILENAME)
    except IOError:
        print(f"Cannot open {FILENAME}")
