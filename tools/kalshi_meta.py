"""Безопасные метаданные рынков Kalshi для ex-ante досье.

Выводит только whitelist-полей. result, цены, объёмы, open_interest, свечи
и settlement-поля не читаются в вывод никогда.

Использование:
  python tools/kalshi_meta.py COST                 # все события тикера
  python tools/kalshi_meta.py COST --event KXEARNINGSMENTIONCOST-26SEP24
  python tools/kalshi_meta.py COST --list-events   # только event_ticker и число рынков
"""
import argparse
import json
import sys
from pathlib import Path

SAFE_FIELDS = [
    "ticker", "event_ticker", "title", "yes_sub_title", "custom_strike",
    "created_time", "open_time", "rules_primary", "rules_secondary",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--event")
    ap.add_argument("--list-events", action="store_true")
    a = ap.parse_args()

    path = Path(__file__).resolve().parent.parent / "kalshi_raw" / f"{a.ticker.upper()}.json"
    if not path.exists():
        sys.exit(f"нет файла {path}")
    markets = json.loads(path.read_text(encoding="utf-8")).get("markets", [])

    if a.list_events:
        counts = {}
        for m in markets:
            counts[m.get("event_ticker")] = counts.get(m.get("event_ticker"), 0) + 1
        print(json.dumps(counts, ensure_ascii=False, indent=2))
        return

    out = [{k: m.get(k) for k in SAFE_FIELDS}
           for m in markets if not a.event or m.get("event_ticker") == a.event]
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
