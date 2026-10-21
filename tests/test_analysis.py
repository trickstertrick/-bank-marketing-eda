"""Küçük yapay birim testi örnekleri; gerçek EDA verisine eklenmez."""
import unittest
import pandas as pd

from src.analysis import EXPECTED, clean_data, build_tables, iqr_profile


def fixture():
    base = {"age":"35", "job":"admin.", "marital":"married", "education":"secondary",
            "default":"no", "balance":"-200", "housing":"yes", "loan":"no",
            "contact":"cellular", "day":"15", "month":"may", "duration":"50",
            "campaign":"1", "pdays":"-1", "previous":"0", "poutcome":"unknown", "y":"no"}
    other = dict(base, age="40", job="unknown", education="unknown", contact="unknown",
                 balance="1000", pdays="0", previous="1", campaign="2", y="yes")
    return pd.DataFrame([base, other], columns=EXPECTED)


class CleaningTests(unittest.TestCase):
    def test_encoded_missing_matches_source(self):
        clean = clean_data(fixture())
        self.assertTrue(clean.loc[1, ["job","education","contact"]].isna().all())
        self.assertEqual(clean.education.isna().sum(), 1)

    def test_zero_day_is_observed_and_minus_one_structural(self):
        clean = clean_data(fixture())
        self.assertTrue(pd.isna(clean.loc[0,"pdays_since_prior"]))
        self.assertEqual(clean.loc[1,"pdays_since_prior"], 0)
        self.assertEqual(clean.loc[0,"prior_outcome_missing_reason"], "not_applicable_no_prior_contact")
        self.assertEqual(clean.loc[1,"prior_outcome_missing_reason"], "unknown_despite_prior_contact")

    def test_negative_balance_and_target_unchanged(self):
        clean = clean_data(fixture())
        self.assertEqual(clean.balance.tolist(), [-200,1000])
        self.assertEqual(clean.y.tolist(), ["no","yes"])
        self.assertEqual(clean.subscribed.tolist(), [0,1])

    def test_duplicates_retained_without_customer_id(self):
        raw = pd.concat([fixture(),fixture().iloc[[0]]], ignore_index=True)
        clean = clean_data(raw)
        self.assertEqual(len(clean),3)
        self.assertEqual(clean.source_row.tolist(), [1,2,3])

    def test_domain_errors_stop_instead_of_drop(self):
        for column, value in [("age","0"),("day","32"),("duration","-1"),
                              ("campaign","0"),("pdays","-2"),("balance","inf"),
                              ("previous","1.5")]:
            with self.subTest(column=column):
                raw = fixture()
                raw.loc[0,column] = value
                with self.assertRaises(ValueError):
                    clean_data(raw)

    def test_unexpected_category_fails(self):
        raw = fixture()
        raw.loc[0,"education"] = "undocumented"
        with self.assertRaises(ValueError):
            clean_data(raw)

    def test_input_is_not_mutated(self):
        raw = fixture()
        original = raw.copy(deep=True)
        clean_data(raw)
        pd.testing.assert_frame_equal(raw,original)

    def test_rates_and_missing_patterns_keep_denominators(self):
        raw = fixture()
        tables = build_tables(raw,clean_data(raw))
        self.assertEqual(int(tables["missing_patterns"].n.sum()),2)
        self.assertEqual(int(tables["education_rates"].n.sum()),2)
        self.assertEqual(tables["education_rates"].loc["Bilinmiyor","rate"],1)

    def test_zero_iqr_flags_are_not_removed(self):
        raw = pd.concat([fixture().iloc[[0]]]*4+[fixture().iloc[[1]]], ignore_index=True)
        clean = clean_data(raw)
        result = iqr_profile(clean).loc["previous"]
        self.assertEqual(result.iqr,0)
        self.assertEqual(result.flagged_n,1)
        self.assertEqual(len(clean),5)

    def test_wrong_dataset_schema_fails(self):
        with self.assertRaises(ValueError):
            clean_data(fixture().drop(columns="balance"))


if __name__ == "__main__":
    unittest.main()
