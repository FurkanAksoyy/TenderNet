"""TenderNet v3 - revision A: title normalisation and renewal classification helpers.

Used by revision_a.py.  A contract is a *renewal* if the same buyer had an earlier
contract in the same product market whose normalised title is similar
(token-set Jaccard >= THRESH) and whose tender date lies 6-18 months earlier.
"""
import re
import numpy as np
import pandas as pd

FOLD = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
                      "â": "a", "î": "i", "û": "u", "é": "e"})
MONTHS = {"ocak", "subat", "mart", "nisan", "mayis", "haziran", "temmuz", "agustos",
          "eylul", "ekim", "kasim", "aralik"}
NUMWORDS = {"bir", "iki", "uc", "dort", "bes", "alti", "yedi", "sekiz", "dokuz", "on",
            "yirmi", "otuz", "kirk", "elli", "altmis", "yetmis", "seksen", "doksan", "yuz",
            "bin", "ii", "iii", "iv", "vi", "vii", "viii", "ix", "xi", "xii"}
# generic procurement words that say nothing about *what* is bought (compared after folding)
GENERIC = {
    "hizmet", "hizmeti", "hizmetleri", "hizmetlerinin", "hizmetinin", "alim", "alimi", "alimlari",
    "alinmasi", "satin", "temin", "temini", "tedarik", "tedariki", "is", "isi", "isleri", "mal",
    "yil", "yili", "yillik", "yilligi", "yillari", "ay", "aylik", "ayligi", "sureli", "surelik",
    "gun", "gunluk", "donem", "donemi", "donemlik", "adet", "kalem", "kisim", "kisimlik", "lot",
    "grup", "ve", "ile", "icin", "ait", "olan", "olarak", "bu", "da", "de", "vb", "vs", "dahil",
    "kapsaminda", "kapsamindaki", "ihtiyaci", "ihtiyac", "ihtiyaclari", "ihtiyacina",
    "ihtiyacimiz", "kullanilmak", "uzere", "yapilmasi", "yaptirilmasi", "yaptirilmasi",
    "mudurlugu", "mudurlugumuz", "mudurlugune", "baskanligi", "baskanligimiz", "belediyesi",
    "belediye", "belediyemiz", "hastanesi", "hastanemiz", "universitesi", "genel", "il",
    "ilce", "idaresi", "kurumu", "merkezi", "birimleri", "birimlerinin", "bagli", "muhtelif",
    "cesitli", "sartname", "teknik", "sartnamede", "belirtilen", "kurumumuz", "idaremiz",
    "sirket", "trf", "try", "tl", "no", "nolu", "sayili", "yeni", "ek",
}


def tr_lower(s):
    s = str(s).replace("I", "ı").replace("İ", "i")
    return s.lower()


def norm_tokens(title, stem=5):
    s = tr_lower(title).translate(FOLD)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    out = set()
    for t in s.split():
        if any(ch.isdigit() for ch in t):
            continue
        if len(t) < 3 or t in GENERIC or t in MONTHS or t in NUMWORDS:
            continue
        st = t[:stem]
        if st in GENERIC:
            continue
        out.add(st)
    return frozenset(out)


def jaccard(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def prior_matches(df, tok, buyer, mkt, day):
    """For every contract, all strictly earlier contracts of the same buyer-market:
    returns long DataFrame (i, j, gap_days, sim)."""
    rows = []
    groups = pd.Series(np.arange(len(df))).groupby(buyer.astype(np.int64) * 1000 + mkt).groups
    for _, idx in groups.items():
        idx = np.asarray(idx)
        if len(idx) < 2:
            continue
        for i in idx:
            for j in idx:
                if day[j] < day[i]:
                    rows.append((i, j, int(day[i] - day[j]), jaccard(tok[i], tok[j])))
    return pd.DataFrame(rows, columns=["i", "j", "gap", "sim"])
