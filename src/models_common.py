# -*- coding: utf-8 -*-
"""Shared helpers for the `models` topic: data loading, deflation, two-way clustering."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contracts_v3.csv"
RES = ROOT / "results" / "models"
FIG = ROOT / "figures"
LAW7144 = pd.Timestamp("2018-05-25")

OTHER_NEG = {"negotiated_21a", "negotiated_21c", "negotiated_21d", "negotiated_21e", "negotiated_21f"}


def cpi_factors():
    """Multiplicative factor converting nominal TRY of year y into 2025 TRY."""
    a = pd.read_csv(ROOT / "data" / "cpi_turkey.csv")
    cpi = dict(zip(a.year, a.cpi_index_annual_avg))
    m = pd.read_csv(ROOT / "data" / "cpi_turkey_2026_monthly.csv")
    # brief: 2026 = average of the linked 2026 monthly index values available
    cpi[2026] = m["cpi_2003eq100_linked"].astype(float).mean()
    base = cpi[2025]
    return {y: base / v for y, v in cpi.items()}, cpi


def load(sample="main", firm_col="firma_v3", buyer_col="kurum_il_split"):
    d = pd.read_csv(DATA, encoding="utf-8-sig", low_memory=False)
    if sample == "main":
        d = d[d.in_scope_main == True]
    elif sample == "it_only":
        d = d[d.scope_v3 == "IT"]
    elif sample == "broad":
        d = d[d.in_scope_broad == True]
    d = d.copy()
    d["date"] = pd.to_datetime(d.tarih_v3)
    d["year"] = d.yil_v3.astype(int)
    f, _ = cpi_factors()
    d["real_value"] = d.bedel_num * d.year.map(f)
    d["log_real_value"] = np.log(d.real_value)
    d["firm"] = d[firm_col]
    d["buyer"] = d[buyer_col]
    d["market"] = d.urun_pazari
    d["proc"] = np.where(d.usul_v3 == "negotiated_21b", "21b",
                 np.where(d.usul_v3.isin(OTHER_NEG), "oth_neg", "open"))  # restricted (n=17) -> reference
    d["proc3"] = np.where(d.usul_v3 == "negotiated_21b", "21b",
                  np.where(d.usul_v3 == "negotiated_21f", "21f",
                   np.where(d.usul_v3.isin(OTHER_NEG), "oth_neg", "open")))
    d["is21b"] = (d.proc == "21b").astype(int)
    d["post7144"] = (d.date >= LAW7144).astype(int)
    d = d.sort_values(["date", "IKN"]).reset_index(drop=True)
    return d


# ------------------------------------------------------------------ clustering
def _meat(S, g):
    """Sum over clusters of s_g s_g' with small-sample factor G/(G-1)."""
    codes, uniq = pd.factorize(pd.Series(g).astype(str))
    G = len(uniq)
    Sg = np.zeros((G, S.shape[1]))
    np.add.at(Sg, codes, S)
    return Sg.T @ Sg * G / (G - 1), G


def twoway_vcov(S, Hinv, g1, g2, k=None):
    """Cameron-Gelbach-Miller two-way clustered vcov.
    S: n x k score contributions, Hinv: inverse of (negative) Hessian (bread).
    Returns V, (G1, G2, G12), n_negative_eigen_clipped."""
    n = S.shape[0]
    k = S.shape[1] if k is None else k
    adj = (n - 1) / (n - k)
    M1, G1 = _meat(S, g1)
    M2, G2 = _meat(S, g2)
    g12 = pd.Series(g1).astype(str).values + "||" + pd.Series(g2).astype(str).values
    M12, G12 = _meat(S, g12)
    V = Hinv @ (M1 + M2 - M12) @ Hinv * adj
    V = (V + V.T) / 2
    w, Q = np.linalg.eigh(V)
    nneg = int((w < 0).sum())
    if nneg:
        V = Q @ np.diag(np.clip(w, 0, None)) @ Q.T
    return V, (G1, G2, G12), nneg


def oneway_vcov(S, Hinv, g, k=None):
    n = S.shape[0]
    k = S.shape[1] if k is None else k
    M, G = _meat(S, g)
    return Hinv @ M @ Hinv * (n - 1) / (n - k), G


def mle_twoway(res, g1, g2):
    """Two-way clustered vcov for a fitted statsmodels MLE (Logit/Poisson/NB)."""
    m = res.model
    S = m.score_obs(res.params)
    H = m.hessian(res.params)
    Hinv = np.linalg.inv(-H)
    return twoway_vcov(np.asarray(S), Hinv, g1, g2)


def ols_scores(X, y, beta):
    e = y - X @ beta
    S = X * e[:, None]
    Hinv = np.linalg.inv(X.T @ X)
    return S, Hinv


def pstars(p):
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
