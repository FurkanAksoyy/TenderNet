"""Historical collector excerpts for inspection; no main entry point.
Extracted from 03_SCRAPER/ekap_v3.py. These are current-source settings, not
proof of the settings used in the historical run. No credentials or raw records
are included. Helper functions needed for live collection are intentionally
omitted; no collection is triggered by importing this module.
Original SHA-256: 4d4c6779f732ba6b4b0ae21b098f9e38e5c59813a19a3e3e5a09bcc9d95afbde
"""
from datetime import datetime
import math
import time

BASLANGIC = "2009-01-01T00:00:00"

BITIS     = datetime.today().strftime("%Y-%m-%dT23:59:59")

ARAMA_KELIMELERI = [
    # Yazılım / uygulama
    "yazılım", "yazılım geliştirme", "uygulama geliştirme",
    "mobil uygulama", "web uygulaması", "web tabanlı",
    "yazılım lisans", "lisans alım", "yazılım bakım",
    "yazılım destek", "yazılım güncelleme",
    # Sistem
    "bilgi sistemi", "yönetim sistemi", "bilgi yönetim sistemi",
    "otomasyon sistemi", "otomasyon yazılım",
    "erp", "kurumsal kaynak", "muhasebe yazılım",
    # Veri / altyapı
    "veri tabanı", "veritabanı", "veri ambarı",
    "veri analiz", "raporlama sistemi",
    # Güvenlik / ağ
    "siber güvenlik", "bilgi güvenlik", "ağ yönetim",
    # Yeni teknoloji
    "yapay zeka", "makine öğrenimi", "dijital dönüşüm",
    "bulut bilişim", "cloud",
    # Sağlık BT
    "hbys", "hasta bilgi", "hastane bilgi sistemi",
    # Kamu / belediye BT
    "e-belediye", "e-devlet", "vatandaş portal",
    "coğrafi bilgi sistemi",
    # Genel BT
    "bilişim", "bilgisayar yazılım",
    "it hizmet", "teknik destek",
    "portal yazılım", "platform yazılım",
    "entegrasyon yazılım", "api",
    "bakım destek hizmet",
]

SAYFA_BASI   = 50

MAX_KW       = 10000

ARALIK_L     = 1.0

ARALIK_D     = 1.5

CP1       = "ekap_v3_cp1.json"

BASE      = "https://ekapv2.kik.gov.tr"

def liste_cek(page, keyword, skip=0):
    veri = page.evaluate("""
    async (args) => {
        try {
            const r = await fetch(args.url, {
                method: 'POST',
                headers: {'Accept':'application/json','Content-Type':'application/json','api-version':'v1'},
                body: JSON.stringify(args.p), credentials: 'include'
            });
            if (!r.ok) return {error: r.status};
            return await r.json();
        } catch(e) { return {error: e.toString()}; }
    }
    """, {
        "url": BASE + "/b_ihalearama/api/Ihale/GetListByParameters",
        "p": {
            "searchText": keyword, "filterType": None,
            "ikNdeAra": True, "ihaleAdindaAra": True,
            "searchType": "GirdigimGibi",
            "iknYili": None, "iknSayi": None,
            "ihaleTarihSaatBaslangic": BASLANGIC,
            "ihaleTarihSaatBitis": BITIS,
            "ilanTarihSaatBaslangic": None, "ilanTarihSaatBitis": None,
            "yasaKapsami4734List": [1], "ihaleTuruIdList": [1,2,3,4],
            "ihaleUsulIdList": [], "ihaleUsulAltIdList": [],
            "ihaleIlIdList": [], "ihaleDurumIdList": [],
            "ihaleIlanTuruIdList": [], "teklifTuruIdList": [],
            "asiriDusukTeklifIdList": [], "istisnaMaddeIdList": [],
            "okasBransKodList": [], "okasBransAdiList": [],
            "titubbKodList": [], "gmdnKodList": [],
            "eIhale": None, "eEksiltmeYapilacakMi": None,
            "ortakAlimMi": None, "kismiTeklifMi": None,
            "fiyatDisiUnsurVarmi": None,
            "ekonomikVeMaliYeterlilikBelgeleriIsteniyorMu": None,
            "meslekiTeknikYeterlilikBelgeleriIsteniyorMu": None,
            "isDeneyimiGosterenBelgelerIsteniyorMu": None,
            "yerliIstekliyeFiyatAvantajiUgulaniyorMu": None,
            "yabanciIsteklilereIzinVeriliyorMu": None,
            "alternatifTeklifVerilebilirMi": None,
            "konsorsiyumKatilabilirMi": None,
            "altYukleniciCalistirilabilirMi": None,
            "fiyatFarkiVerilecekMi": None, "avansVerilecekMi": None,
            "cerceveAnlasmaMi": None,
            "personelCalistirilmasinaDayaliMi": None,
            "orderBy": "ihaleTarihi", "siralamaTipi": "desc",
            "paginationSkip": skip, "paginationTake": SAYFA_BASI,
        }
    })
    if not veri or veri.get("error"):
        return [], 0
    return veri.get("list", []), int(veri.get("totalCount", 0))

def asama1(page):
    print("\n" + "="*60)
    print("  ASAMA 1 — 2009'dan Bugüne İhale Listesi")
    print("="*60)

    cp       = cp_yukle(CP1)
    ikn_set  = set(cp.get("ikn_set", []))
    satirlar = cp.get("satirlar", [])
    if satirlar:
        print(f"\n  ♻ Checkpoint: {len(satirlar)} ihale. Atlanıyor.\n")
        return satirlar

    for ki, kw in enumerate(ARAMA_KELIMELERI, 1):
        print(f"\n[{ki:02d}/{len(ARAMA_KELIMELERI):02d}] \"{kw}\"")
        ilk, toplam = liste_cek(page, kw, 0)

        if not toplam and not ilk:
            print("     Yanit yok.")
            continue

        max_k   = min(MAX_KW, toplam)
        sayfa_n = math.ceil(max_k / SAYFA_BASI)
        print(f"     {toplam} ihale → {sayfa_n} sayfa")

        yeni = 0
        for ih in ilk:
            s = satira(ih, kw)
            if s["IKN"] and s["IKN"] not in ikn_set:
                ikn_set.add(s["IKN"]); satirlar.append(s); yeni += 1

        with tqdm(range(1, sayfa_n), desc="     Sayfa",
                  unit="s", leave=False, colour="cyan") as pbar:
            for i in pbar:
                lst, _ = liste_cek(page, kw, i * SAYFA_BASI)
                if not lst:
                    break
                for ih in lst:
                    s = satira(ih, kw)
                    if s["IKN"] and s["IKN"] not in ikn_set:
                        ikn_set.add(s["IKN"]); satirlar.append(s); yeni += 1
                pbar.set_postfix({"yeni": yeni, "toplam": len(satirlar)})
                time.sleep(ARALIK_L)

        print(f"     ✓ {yeni} yeni. Toplam: {len(satirlar)}")
        cp_kaydet(CP1, {"ikn_set": list(ikn_set), "satirlar": satirlar})

    return satirlar
