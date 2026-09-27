"""Currency regression checks; run python -m unittest discover -s src/build."""
import sys
from pathlib import Path
import unittest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from currency_values import normalize_frame, parse_amount, xml_rates
from normalize_currency import ROOT, verify_rates


class CurrencyTests(unittest.TestCase):
    def test_parser_and_unknown_currency(self):
        self.assertEqual(parse_amount("219.500,00&nbsp;USD"), (219500, "USD", "explicit"))
        self.assertEqual(parse_amount("1,234,567.89 EUR"), (1234567.89, "EUR", "explicit"))
        self.assertEqual(parse_amount("109668,4")[0], 109668.4)
        self.assertEqual(parse_amount("13.810,00"), (13810, "TRY", "unspecified_assumed_TRY"))
        for bad in ("100 GBP", "unknown", "0 TRY", "12.3.4 USD"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse_amount(bad)

    def test_actual_xml_rate_and_hashes(self):
        rates = pd.read_csv(ROOT / "data/fx_rates_tcmb.csv")
        verify_rates(rates)
        r = rates[(rates.tender_date == "2016-11-04") & (rates.currency == "USD")].iloc[0]
        self.assertAlmostEqual(r.try_per_unit, (3.1348 + 3.1405) / 2)

    def test_conversion_idempotence_and_fallback_window(self):
        data = pd.DataFrame({"bedel": ["100 USD", "100 TRY", "100"], "tarih_v3": ["2014-10-28"] * 3})
        rates = pd.DataFrame([{"tender_date": "2014-10-28", "currency": "USD", "rate_date": "2014-10-27", "try_per_unit": 2.25}])
        first = normalize_frame(data, rates)
        pd.testing.assert_frame_equal(first, normalize_frame(first, rates))
        self.assertEqual(first.bedel_try.tolist(), [225, 100, 100])
        self.assertIn("prior_business_day", first.bedel_valuation_method.iloc[0])
        for invalid_date in ("2014-10-29", "2014-10-20"):
            with self.assertRaises(ValueError):
                normalize_frame(data, rates.assign(rate_date=invalid_date))
        with self.assertRaises(KeyError):
            normalize_frame(data, rates.iloc[0:0])

    def test_xml_unit_and_date(self):
        xml = b'<Tarih_Date Tarih="01.01.2020"><Currency Kod="USD"><Unit>100</Unit><ForexBuying>200</ForexBuying><ForexSelling>220</ForexSelling></Currency><Currency Kod="EUR"><Unit>1</Unit><ForexBuying>3</ForexBuying><ForexSelling>4</ForexSelling></Currency></Tarih_Date>'
        self.assertEqual(xml_rates(xml, "2020-01-01")["USD"][3], 2.1)
        with self.assertRaises(ValueError):
            xml_rates(xml, "2020-01-02")

    def test_preserved_sample_and_raw_values(self):
        data = pd.read_csv(ROOT / "data/contracts_v3.csv", low_memory=False)
        self.assertEqual(len(data), 13024)
        main = data[data.in_scope_main]
        self.assertEqual(len(main), 9991)
        self.assertEqual(main.bedel_currency.value_counts().to_dict(), {"TRY": 9924, "USD": 54, "EUR": 13})
        self.assertEqual((main.bedel_currency_status == "unspecified_assumed_TRY").sum(), 845)
        self.assertTrue((data.bedel_amount_original - data.bedel_num).abs().lt(0.001).all())


if __name__ == "__main__":
    unittest.main()
