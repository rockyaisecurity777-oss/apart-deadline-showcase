"""Post-sprint helper (added 18 Nov 2026): check the paper's three worked examples
with the unchanged `possible()` function from clock_evidence.py."""
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from clock_evidence import possible  # noqa: E402

NY = ZoneInfo("America/New_York")
for label in (datetime(2026, 3, 8, 2, 30), datetime(2026, 11, 1, 1, 30)):
    found = sorted(i.strftime("%Y-%m-%d %H:%M UTC") for i in possible(label, NY))
    print(f"New York {label:%d %b %Y %H:%M}: {len(found)} candidate(s) {found}")

aoe = datetime(2026, 11, 15, 23, 59, tzinfo=ZoneInfo("Etc/GMT+12"))
print(f"15 Nov 2026 23:59 AoE = {aoe.astimezone(timezone.utc):%d %b %H:%M} UTC = "
      f"{aoe.astimezone(ZoneInfo('Asia/Kolkata')):%d %b %H:%M} Asia/Kolkata")
