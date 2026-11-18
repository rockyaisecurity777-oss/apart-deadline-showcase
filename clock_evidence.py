"""Replicate the civil-time evidence audit using Python 3.9+ and IANA zoneinfo."""
import csv
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ZONES = ('America/Los_Angeles','America/New_York','Europe/London','Europe/Berlin',
         'Australia/Sydney','Australia/Lord_Howe','Asia/Kolkata','Etc/GMT+12')
UTC = timezone.utc

def possible(wall, zone):
    candidates = set()
    for fold in (0, 1):
        instant = wall.replace(tzinfo=zone, fold=fold).astimezone(UTC)
        if instant.astimezone(zone).replace(tzinfo=None) == wall:
            candidates.add(instant)
    return candidates

def oracle(zone):
    # Enumerate from UTC independently; never attach a zone to a local label.
    mapping = {}
    instant = datetime(2025,12,31,tzinfo=UTC)
    end = datetime(2027,1,2,tzinfo=UTC)
    while instant < end:
        wall = instant.astimezone(zone).replace(tzinfo=None)
        if wall.year == 2026:
            mapping.setdefault(wall,set()).add(instant)
        instant += timedelta(minutes=30)
    return mapping

def evaluate():
    summary = Counter()
    for name in ZONES:
        zone = ZoneInfo(name)
        reference = oracle(zone)
        offset = datetime(2026,11,14,12,tzinfo=zone).utcoffset()
        wall = datetime(2026,1,1)
        while wall.year == 2026:
            truth = reference.get(wall,set())
            predictions = {
                'fixed': {(wall-offset).replace(tzinfo=UTC)},
                'first_fold': {wall.replace(tzinfo=zone).astimezone(UTC)},
                'round_trip': possible(wall,zone)
            }
            for method, prediction in predictions.items():
                kind = ('gap','unique','repeated')[len(truth)]
                status = 'match' if prediction == truth else 'error'
                summary[name, method, kind, status] += 1
            wall += timedelta(minutes=30)
    writer=csv.writer(sys.stdout)
    writer.writerow(('zone','method','source_time_type','result','count'))
    for key,value in sorted(summary.items()):
        writer.writerow((*key,value))

if __name__ == '__main__':
    evaluate()
