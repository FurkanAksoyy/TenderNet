"""Normalize contract currency using cached TCMB XML. Network is opt-in.

Run python src/build/normalize_currency.py --fetch once to populate the cache;
ordinary runs verify XML hashes/rates and reproduce data entirely offline.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
import hashlib
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from currency_values import normalize_frame, parse_amount, xml_rates

CACHE = ROOT / "data" / "fx_cache_tcmb"
RATES = ROOT / "data" / "fx_rates_tcmb.csv"


def fetch_date(tender_date):
    tender = date.fromisoformat(tender_date)
    for lag in range(8):
        day = tender - timedelta(days=lag)
        if day.weekday() >= 5:
            continue
        url = f"https://www.tcmb.gov.tr/kurlar/{day:%Y%m}/{day:%d%m%Y}.xml"
        path = CACHE / f"{day.isoformat()}.xml"
        if path.exists():
            payload = path.read_bytes()
        else:
            try:
                with urlopen(url, timeout=60) as response:
                    payload = response.read()
            except HTTPError as exc:
                if exc.code == 404:
                    continue
                raise
            path.write_bytes(payload)
        rates = xml_rates(payload, day.isoformat())
        return [{"tender_date": tender_date, "currency": currency, "rate_date": day.isoformat(),
                 "forex_buying": b, "forex_selling": s, "unit": u, "try_per_unit": mid,
                 "source_url": url, "source_sha256": hashlib.sha256(payload).hexdigest(),
                 "cache_file": path.name} for currency, (b, s, u, mid) in rates.items()]
    raise ValueError(f"No TCMB business-day rate within seven days of {tender_date}")


def verify_rates(rates):
    if rates.duplicated(["tender_date", "currency"]).any():
        raise ValueError("Duplicate FX keys")
    for row in rates.itertuples():
        payload = (CACHE / row.cache_file).read_bytes()
        if hashlib.sha256(payload).hexdigest() != row.source_sha256:
            raise ValueError(f"TCMB cache hash mismatch: {row.cache_file}")
        actual = xml_rates(payload, row.rate_date)[row.currency]
        recorded = (row.forex_buying, row.forex_selling, row.unit, row.try_per_unit)
        if any(abs(a - b) > 1e-10 for a, b in zip(actual, recorded)):
            raise ValueError("Rate table differs from source XML")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    path = ROOT / "data" / "contracts_v3.csv"
    data = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    if args.fetch:
        CACHE.mkdir(parents=True, exist_ok=True)
        dates = sorted({str(d) for d, amount in zip(data.tarih_v3, data.bedel) if parse_amount(amount)[1] != "TRY"})
        with ThreadPoolExecutor(max_workers=6) as pool:
            rows = [r for batch in pool.map(fetch_date, dates) for r in batch]
        pd.DataFrame(rows).sort_values(["tender_date", "currency"]).to_csv(RATES, index=False)
    rates = pd.read_csv(RATES)
    verify_rates(rates)
    output = normalize_frame(data, rates)
    output.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"Currency normalized: {len(output)} records; {(output.bedel_currency != 'TRY').sum()} FX records")


if __name__ == "__main__":
    main()
