"""
Earnings call transcripts via llama-index-readers-earnings-call-transcript
(source: discountingcashflows.com; US companies only; library is non-commercial).

Setup (once):   pip install llama-index-readers-earnings-call-transcript
Run:            python fetch_transcripts.py NKE          # one or more tickers
                python fetch_transcripts.py              # all companies in companies.json
Options:        --years 5   --delay 0.5
Re-runnable: finished quarters and known-missing quarters (manifest.json) are skipped.
Output: <company folder>/<year>Q<q>.txt and .json ; manifest.json ; fetch_log.txt
"""
import argparse, datetime as dt, json, time, traceback
from pathlib import Path
from llama_index.readers.earnings_call_transcript import EarningsCallTranscript

ROOT = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("tickers", nargs="*")
ap.add_argument("--years", type=int, default=5)
ap.add_argument("--delay", type=float, default=0.5)
args = ap.parse_args()

companies = json.loads((ROOT / "companies.json").read_text(encoding="utf-8"))
only = {t.upper() for t in args.tickers}
manifest_path = ROOT / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
log = open(ROOT / "fetch_log.txt", "a", encoding="utf-8")

def save_manifest():
    manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")

this_year = dt.date.today().year
years = range(this_year - args.years, this_year + 1)

for c in companies:
    if only and c["ticker"] not in only:
        continue
    # the library only knows US tickers; strip exchange suffix
    ticker = c["symbol"].split(".")[0] if c["symbol"] != "BRK.B" else "BRK-B"
    folder = ROOT / c["folder"]
    folder.mkdir(exist_ok=True)
    got = 0
    for y in years:
        for q in ("Q1", "Q2", "Q3", "Q4"):
            key = f"{c['ticker']}|{y}|{q}"
            base = folder / f"{y}{q}"
            if base.with_suffix(".txt").exists():
                got += 1
                continue
            if manifest.get(key) == "missing":
                continue
            try:
                docs = EarningsCallTranscript(y, ticker, q).load_data()
                doc = docs[0] if docs else None
                if doc is None or not (doc.text or "").strip():
                    manifest[key] = "missing"
                    continue
                meta = dict(doc.metadata or {})
                base.with_suffix(".json").write_text(
                    json.dumps({"metadata": meta, "text": doc.text}, ensure_ascii=False, indent=1, default=str),
                    encoding="utf-8")
                head = f"{c['company']} ({c['ticker']}) {y} {q}\n{meta.get('date_time', '')}\n\n"
                base.with_suffix(".txt").write_text(head + doc.text, encoding="utf-8")
                manifest[key] = "ok"
                got += 1
            except AssertionError as e:          # e.g. year not allowed by the library
                manifest[key] = "missing"
                log.write(f"{key}: assertion {e}\n")
            except Exception as e:                # not found / network / parse error
                manifest[key] = "missing"
                log.write(f"{key}: {type(e).__name__}: {str(e)[:200]}\n")
            log.flush()
            time.sleep(args.delay)
        save_manifest()
    print(f"{c['ticker']}: {got} transcripts")
save_manifest()
print("done")
