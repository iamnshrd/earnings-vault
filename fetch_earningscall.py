"""
Earnings call transcripts via EarningsCall.biz (pip install earningscall).
Free without a key: only AAPL and MSFT (good for a dry run).
Paid key: set EARNINGSCALL_API_KEY. Speaker split (level 2) and prepared/Q&A split (level 4)
need the Premium plan; Starter only gives plain text (level 1). The script falls back automatically.

Run:   python fetch_earningscall.py AAPL          # one or more tickers
       python fetch_earningscall.py               # all 113 companies from companies.json
Opts:  --years 5  --delay 3.1  --level 4          # delay: Premium 20 req/min ~ 3.1s, Starter 10/min ~ 6.2s
Re-runnable: existing files are skipped.
Output per call: <company folder>/<year>Q<q>.txt and .json ; errors in ec_log.txt
"""
import argparse, datetime as dt, json, time
from pathlib import Path
from earningscall import get_company

ROOT = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("tickers", nargs="*")
ap.add_argument("--years", type=int, default=5)
ap.add_argument("--delay", type=float, default=3.1)
ap.add_argument("--level", type=int, default=4, choices=[1, 2, 4])
args = ap.parse_args()

companies = json.loads((ROOT / "companies.json").read_text(encoding="utf-8"))
only = {t.upper() for t in args.tickers}
log = open(ROOT / "ec_log.txt", "a", encoding="utf-8")
cutoff = dt.datetime.now() - dt.timedelta(days=365 * args.years + 2)
now = dt.datetime.now()

def call(fn, *a, **kw):
    """one retry after a pause (rate limits / transient errors)"""
    for i in range(3):
        time.sleep(args.delay)
        try:
            return fn(*a, **kw)
        except Exception as e:
            msg = str(e)
            if i == 2 or "404" in msg or "not found" in msg.lower():
                raise
            time.sleep(20 * (i + 1))

def render(t, level):
    """returns (text, used_level)"""
    if level >= 4 and getattr(t, "prepared_remarks", None):
        return ("=== PREPARED REMARKS ===\n" + t.prepared_remarks +
                "\n\n=== Q&A ===\n" + (getattr(t, "questions_and_answers", "") or "")), 4
    if level >= 2 and getattr(t, "speakers", None):
        out = []
        for s in t.speakers:
            info = getattr(s, "speaker_info", None)
            who = getattr(info, "name", None) or getattr(s, "speaker", "")
            title = getattr(info, "title", None)
            out.append(f"{who}{' (' + title + ')' if title else ''}:\n{s.text}")
        return "\n\n".join(out), 2
    return (t.text or ""), 1

for c in companies:
    if only and c["ticker"] not in only:
        continue
    folder = ROOT / c["folder"]
    folder.mkdir(exist_ok=True)
    try:
        company = get_company(c["symbol"].split(".")[0].lower())
        events = [e for e in company.events()
                  if cutoff <= e.conference_date.replace(tzinfo=None) <= now]
    except Exception as e:
        log.write(f"{c['ticker']}: company/events failed: {type(e).__name__}: {str(e)[:200]}\n"); log.flush()
        print(f"{c['ticker']}: not available ({type(e).__name__})")
        continue
    got = 0
    for e in sorted(events, key=lambda e: e.conference_date):
        base = folder / f"{e.year}Q{e.quarter}"
        if base.with_suffix(".txt").exists():
            got += 1
            continue
        t = None
        for lvl in sorted({args.level, 2, 1}, reverse=True):
            if lvl > args.level:
                continue
            try:
                t = call(company.get_transcript, event=e, level=lvl)
            except Exception as ex:
                log.write(f"{c['ticker']} {e.year}Q{e.quarter} level{lvl}: {type(ex).__name__}: {str(ex)[:200]}\n"); log.flush()
                t = None
                continue
            if t is not None:
                break
        if t is None:
            continue
        text, used = render(t, args.level)
        if not text.strip():
            continue
        date = e.conference_date.strftime("%Y-%m-%d")
        base.with_suffix(".json").write_text(json.dumps(
            {"company": c["company"], "ticker": c["ticker"], "year": e.year, "quarter": e.quarter,
             "date": date, "level": used, "text": text}, ensure_ascii=False, indent=1), encoding="utf-8")
        base.with_suffix(".txt").write_text(
            f"{c['company']} ({c['ticker']}) FY{e.year} Q{e.quarter}\n{date}\n\n{text}", encoding="utf-8")
        got += 1
    print(f"{c['ticker']}: {got}/{len(events)} transcripts")
print("done")
