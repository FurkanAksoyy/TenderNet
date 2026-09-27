# Classification and observed-history stress tests

Prespecified variants; 1,000 within-cell permutations per variant; fixed seed 20260927. Incumbency requires a strictly earlier tender date. Calendar-year demand, buyer identities, dates, and supplier win totals within each reported cell remain fixed. Null intervals are permutation percentiles, not confidence intervals for the observed rate.

| Variant | History N | Evaluation N | Eligible | Observed | Null mean [2.5%,97.5%] | Ratio | Upper-tail p |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 9991 | 9991 | 4913 | 0.4523 | 0.2073 [0.2009, 0.2131] | 2.182 | 0.000999 |
| merged_software_services | 9991 | 9991 | 5397 | 0.4334 | 0.1848 [0.1792, 0.1907] | 2.345 | 0.000999 |
| category_free_buyer | 9991 | 9991 | 7087 | 0.3893 | 0.1033 [0.0981, 0.1084] | 3.768 | 0.000999 |
| health_only | 2189 | 2189 | 1252 | 0.7157 | 0.4069 [0.3914, 0.4209] | 1.759 | 0.000999 |
| evaluate_2013_onward | 9991 | 8715 | 4671 | 0.4573 | 0.2109 [0.2047, 0.2171] | 2.168 | 0.000999 |
| evaluate_2015_onward | 9991 | 7323 | 4142 | 0.4640 | 0.2177 [0.2108, 0.2245] | 2.132 | 0.000999 |
| exclude_other_IT | 9714 | 9714 | 4801 | 0.4537 | 0.2066 [0.2006, 0.2131] | 2.195 | 0.000999 |

All variants use category x year x buyer-province cells, except category-free buyer incumbency, which uses year x buyer province. The merged variant changes both the history category and the null category. It merges ERP, custom software, maintenance and other IT into software_services solely as a taxonomic stress test; it does not establish an economic relevant market.

Later evaluation windows retain all pre-window observed history in both observed and permuted records. Health-only and no-other-IT variants restrict the sample before computing histories. All null draws and cell-mobility diagnostics are saved. Movable means a cell contains at least two distinct supplier labels; it does not guarantee a given record moves in each draw.

The keyword-defined extract does not measure national IT procurement coverage or identify omitted titles. 2010 and 2026 are partial years (October 2010–March 2026 in the present extract). Later outcome windows cannot recover pre-2010 history or correct changes in keyword capture. No variant establishes switching costs, corruption, or causal effects. Permutation p=(1+exceedances)/(1001); resolution is 1/1001. These correlated sensitivity checks are not independent replications.

## Available AI agreement audit

{
  "available": true,
  "sample_n": 300,
  "complete_n": 300,
  "common_n": 266,
  "disagreement_n": 34,
  "rule_agreement_coderA": 0.7466666666666667,
  "rule_agreement_coderB": 0.73,
  "rule_agreement_AI_common": 0.793233082706767,
  "interpretation": "AI agreement audit, not human accuracy; consensus conditions on easier/agreed cases."
}

Class-level rule denominators, AI-consensus denominators, disagreements, and pairwise confusion matrices accompany this report. Two model labels are not human truth, and consensus-only agreement can overstate performance on difficult titles.
