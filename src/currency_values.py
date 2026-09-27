"""Auditable contract currency parsing and nominal TRY valuation.

Unknown explicit currencies fail closed. Unlabelled values retain an explicit
TRY assumption; FX midpoint valuation is a tender-date proxy, not payment value.
"""
import html
import math
import re
from datetime import date
import xml.etree.ElementTree as ET


def parse_amount(raw):
    s = html.unescape(str(raw)).replace("\xa0", " ").strip()
    match = re.fullmatch(r"([0-9][0-9., ]*)\s*([A-Za-z]+|₺|€|\$)?", s)
    if not match:
        raise ValueError(f"Unrecognized monetary value: {raw!r}")
    number, label = match.groups()
    label = (label or "").upper()
    aliases = {"TRY": "TRY", "TL": "TRY", "₺": "TRY", "USD": "USD", "$": "USD", "EUR": "EUR", "€": "EUR"}
    if label and label not in aliases:
        raise ValueError(f"Unsupported explicit currency: {label}")
    currency = aliases.get(label, "TRY")
    number = number.replace(" ", "")
    if not re.fullmatch(r"(?:[0-9]+(?:[.,][0-9]{1,2})?|[0-9]{1,3}(?:\.[0-9]{3})+(?:,[0-9]{1,2})?|[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?)", number):
        raise ValueError(f"Malformed monetary number: {raw!r}")
    if "," in number and "." in number:
        number = number.replace(".", "").replace(",", ".") if number.rfind(",") > number.rfind(".") else number.replace(",", "")
    elif "," in number:
        number = number.replace(",", ".") if len(number.rsplit(",", 1)[1]) in (1, 2) else number.replace(",", "")
    elif number.count(".") > 1 or ("." in number and len(number.rsplit(".", 1)[1]) == 3):
        number = number.replace(".", "")
    amount = float(number)
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError(f"Nonpositive/nonfinite amount: {raw!r}")
    return amount, currency, "explicit" if label else "unspecified_assumed_TRY"


def xml_rates(payload, expected_date):
    root = ET.fromstring(payload)
    observed = date.fromisoformat(expected_date)
    if root.attrib.get("Tarih") != observed.strftime("%d.%m.%Y"):
        raise ValueError("TCMB XML date does not match requested rate date")
    result = {}
    for node in root.findall("Currency"):
        currency = node.attrib.get("Kod") or node.attrib.get("CurrencyCode")
        if currency in ("USD", "EUR"):
            unit = float(node.findtext("Unit"))
            buy, sell = float(node.findtext("ForexBuying")), float(node.findtext("ForexSelling"))
            if not all(math.isfinite(x) and x > 0 for x in (unit, buy, sell)) or sell < buy:
                raise ValueError("Invalid TCMB rate")
            result[currency] = (buy, sell, unit, (buy + sell) / (2 * unit))
    if set(result) != {"USD", "EUR"}:
        raise ValueError("Missing USD/EUR TCMB rates")
    return result


def normalize_frame(frame, rates):
    """Recompute from immutable bedel strings; never compound conversions."""
    out = frame.copy()
    parsed = [parse_amount(x) for x in out.bedel]
    out["bedel_amount_original"] = [x[0] for x in parsed]
    out["bedel_currency"] = [x[1] for x in parsed]
    out["bedel_currency_status"] = [x[2] for x in parsed]
    lookup = {(str(r.tender_date), r.currency): r for r in rates.itertuples()}
    fx, dates, methods = [], [], []
    for tender, (_, currency, status) in zip(out.tarih_v3, parsed):
        if currency == "TRY":
            fx.append(1.0); dates.append(""); methods.append(status)
            continue
        rate = lookup[(str(tender), currency)]
        lag = (date.fromisoformat(str(tender)) - date.fromisoformat(str(rate.rate_date))).days
        if not 0 <= lag <= 7 or not math.isfinite(rate.try_per_unit) or rate.try_per_unit <= 0:
            raise ValueError("Invalid or out-of-window FX rate")
        fx.append(rate.try_per_unit); dates.append(rate.rate_date)
        methods.append("TCMB_tender_date_midpoint_proxy" if lag == 0 else "TCMB_prior_business_day_midpoint_proxy")
    out["bedel_fx_try_per_unit"] = fx
    out["bedel_fx_date"] = dates
    out["bedel_valuation_method"] = methods
    out["bedel_try"] = out.bedel_amount_original * out.bedel_fx_try_per_unit
    return out
