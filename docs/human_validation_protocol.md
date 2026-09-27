# Human classification validation protocol

Status: prospective protocol. No human labels or human accuracy results are asserted here. AI labels in the repository are an agreement audit only.

## Materials and frozen coding

Use the existing 300-title sample in `data/audit/ai_coding/blind_markets_input.csv` and 60-pair sample in `data/audit/ai_coding/blind_renewals_input.csv`. The existing separate workbooks are at `12_GONDERIM_v3_JIBE/4_INSAN_KODLAMASI/coding_sheet_FurkanAksoy.xlsx` and `coding_sheet_ArdaSimsek.xlsx` relative to the project root (one directory above this repository); originals also exist under `10_V3/human_coding/`. Verify the workbook ID sets match the CSV samples before coding. Preserve those sampling IDs, original titles, and the codebook version. Do not resample after viewing disagreements.

Two Turkish-reading people independently code all records. They must not view rules, model labels, similarity scores, winners, incumbent indicators, or one another's coding. Existing workbook sheets must be checked for hidden/unblinded columns before distribution. The codebook gives the 14 category definitions and examples unrelated to the evaluation records. Coders assign a category plus an uncertainty flag; insufficient title information remains an explicit unresolved response. For renewal pairs, assign same recurring service, different service, or unclear, with a short rationale. A repeated service is not necessarily a legal extension or renewal of an existing contract.

Record coder identity, expertise, coding dates, training, codebook version and any permitted external context. Training uses separate examples. Freeze both original files with timestamps and SHA-256 hashes before showing any disagreement or model suggestion. Copy frozen originals; never overwrite them during reconciliation. Resolve discrepancies jointly or through a third person only after freezing, and save adjudicated labels and reasons in a separate file. If the codebook changes, record the change and recode affected records independently. An AI assistant may organize files or compute statistics; it must never create or impersonate human judgments.

## Reporting and denominators

Report the sampling frame, random seed if documented, exact record counts, missing/unresolved counts, coder disagreements, and all category and renewal-threshold strata. The existing renewal-pair set is not necessarily representative of all possible pairs; document how the 42 above-threshold and 18 below-threshold pairs were selected before extrapolation. Keep missing and unclear labels visible rather than silently excluding them. Report agreement before adjudication separately from agreement with adjudicated labels.

For market classes, provide the full confusion matrix; rule-predicted denominator, human-reference denominator and true-positive count for each category; precision, recall and F1; micro and macro summaries. Give Wilson 95% intervals for simple proportions with their denominators. For kappa and aggregate metrics use a documented bootstrap; cluster by buyer or related title family if repeated records create dependence and identifiers permit it. Sparse category intervals will be wide. If strata were oversampled, give stratum-specific results and sampling-weighted aggregate estimates; do not assume the pooled sample is self-weighting without checking its design.

For renewal pairs, tabulate rule flag versus each original human judgment and adjudicated judgment, including unclear outcomes. Report sensitivity/specificity only against a defined reference with all denominators and intervals, and give the unclear share separately. Multiple pairs sharing buyers/contracts require clustered uncertainty. Assess label errors by incumbent status only after blind coding is frozen. Misclassification need not bias the renewal-incumbency contrast toward zero.

Do not tune the title rules on this evaluation sample and then present the same labels as held-out accuracy. If rules change, separate development from new independent evaluation, or clearly label apparent in-sample agreement. Report effects of uncertain/reclassified records on substantive conclusions as sensitivity analyses, not automatic error correction. These sheets assess classification within the captured keyword sample; they cannot estimate recall of all national IT tenders or repair omitted procurement records.

## Deliverables and provenance

Retain original independent files, a reconciliation log, frozen codebook, hashes, sampling documentation, machine-readable labels, full confusion tables, and analysis script. Export market labels keyed by IKN and renewal labels by pair_id; do not release unnecessary personal information. Methods must name the human-coding process separately from AI model/version/prompt/date records. Until actual independent human coding is completed, describe human validation as outstanding, not complete.
