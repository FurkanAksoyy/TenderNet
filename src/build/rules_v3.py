# -*- coding: utf-8 -*-
"""
rules_v3.py -- all rule sets used to build master_v3 (imported by build_master_v3.py).

Everything here is deterministic keyword / regex logic on Turkish upper-cased text.
Keep this file as the single documented source of the rules (README refers to it).
"""
import re

# ----------------------------------------------------------------------------- text helpers
def tr_upper(s) -> str:
    """Turkish-aware upper case + whitespace collapse. (Python's str.upper maps 'i'->'I', which broke
    the v1 sector rules on mixed-case buyer names such as 'Belediye' -> 'BELEDIYE'.)"""
    s = "" if s is None else str(s)
    s = s.replace("i", "İ").replace("ı", "I").upper()
    s = s.replace("Â", "A").replace("Î", "İ").replace("Û", "U")
    return re.sub(r"\s+", " ", s).strip()


def rx(*alts) -> re.Pattern:
    return re.compile("|".join(alts))


# ============================================================================= 1. IT SCOPE
# Titles are matched after tr_upper(). '\b' works for Turkish letters in Python 3 regex.

# 1a. call-centre / contact-centre services (IT-enabled services; kept, flagged)
CALLCENTRE = rx(r"ÇAĞRI MERKEZ", r"\bMHRS\b", r"ÇAĞRI HİZMET", r"İLETİŞİM MERKEZİ", r"\bALO ?1\d\d\b",
                r"\bSABİM\b", r"\bCİMER\b.*(HİZMET|MERKEZ)", r"YARDIM MASASI", r"HELP ?DESK", r"MÜŞTERİ HİZMETLERİ MERKEZ")

# call-centre titles that buy software/equipment (not an outsourced service) stay plain IT
CALLCENTRE_PRODUCT = rx(r"YAZILIM", r"LİSANS", r"DONANIM", r"CİHAZ", r"SANTRAL", r"SİSTEMİ(NİN)? (ALIM|KURULUM|TEMİN)",
                        r"ALTYAPI")

# 1b. strong IT evidence
STRONG_IT = rx(
    r"YAZILIM", r"BİLİŞİM", r"BİLGİSAYAR", r"DONANIM", r"SUNUCU", r"LİSANS", r"\bHBYS\b", r"\bSBYS\b",
    r"\bLBYS\b", r"\bPACS\b", r"\bDHBYS\b", r"\bYBBYS\b", r"\bRIS\b", r"BİLGİ SİSTEM", r"BİLGİ YÖNETİM",
    r"VERİ ?TABAN", r"VERİ MERKEZ", r"VERİ DEPOLA", r"VERİ AMBAR", r"VERİ ANALİ", r"SİBER", r"NETWORK",
    r"SWİTCH", r"SWITCH", r"FİREWALL", r"GÜVENLİK DUVARI", r"\bWEB\b", r"WEB ?TABANLI", r"MOBİL UYGULAMA",
    r"PORTAL", r"(?<!-)\bERP\b(?!-)", r"KURUMSAL KAYNAK", r"\bCBS\b", r"COĞRAFİ BİLGİ", r"KENT BİLGİ", r"BİLGİ İŞLEM",
    r"YAPAY ZEKA", r"ORACLE", r"MİCROSOFT", r"\bSAP\b", r"SYBASE", r"\bIBM\b", r"STORAGE", r"SANALLAŞTIRMA",
    r"YEDEKLEME", r"SİEBEL", r"ANGULAR", r"\bRFID\b", r"\bKGYS\b", r"MOBESE", r"PLAKA TANIMA", r"İNTERNET",
    r"BULUT", r"\bVTYS\b", r"E-BELEDİYE", r"E-DEVLET", r"UYGULAMA GELİŞTİR", r"DİJİTAL DÖNÜŞÜM",
    r"IP TELEFON", r"İŞ ZEKASI", r"\bEBYS\b", r"BELGE YÖNETİM", r"DOKÜMAN YÖNETİM", r"DÖKÜMAN YÖNETİM",
    r"ARŞİV YÖNETİM", r"SAYISALLAŞTIRMA", r"LOG YÖNETİM", r"\bSIEM\b", r"KENT GÜVENLİK", r"ÖĞRENME YÖNETİM",
    r"UZAKTAN EĞİTİM", r"AKILLI TAHTA", r"ETKİLEŞİMLİ TAHTA", r"TABLET", r"YAZICI", r"TARAYICI", r"SCADA",
    r"DİJİTAL İKİZ", r"KÜTÜPHANE OTOMASYON", r"HASTANE OTOMASYON", r"BELEDİYE OTOMASYON", r"SD-WAN",
    r"KABLOSUZ", r"FİBER OPTİK", r"VERİ İLETİŞİM", r"KAMERA", r"OTOMASYON PROGRAM",
    r"TELEKOMÜNİKASYON", r"UÇ NOKTA", r"KİMLİK DOĞRULAMA", r"E-İMZA", r"DİJİTAL ARŞİV", r"İÇERİK YÖNETİM",
    r"TRAFİK YÖNETİM", r"AKILLI KAVŞAK", r"ADAPTİF", r"ELEKTRONİK DENETLEME", r"ÜCRET TOPLAMA",
    r"\bSOC\b", r"UYGULAMA YAZILIM",
    r"BİLGİ TEKNOLOJİ", r"BİLGİ GÜVENLİ", r"\bNAS\b", r"SABİT DİSK", r"\bAĞ (ALT ?YAPI|CİHAZ|SİSTEM|GÜVENLİ|ÜRÜN|KART)",
    r"AĞLARI", r"\bHPE\b", r"DEPOLAMA ÜNİTE", r"KÜTÜPHANE YÖNETİM", r"SINAV OTOMASYON", r"ÇAĞRI KAYIT", r"VERİ İŞLEM",
)
# phrases in which an IT word only names a BUILDING / unit -> removed before testing STRONG_IT
BUILDING_NAME = rx(r"BİLGİSAYAR (VE )?(BİLİŞİM )?(MÜHENDİSLİĞİ )?FAKÜLTE\w*( BİNASI)?", r"BİLİŞİM FAKÜLTE\w*",
                   r"BİLGİ İŞLEM (MERKEZİ )?BİNA\w*", r"BİLGİ EVİ", r"YAZILIM GELİŞTİRME MERKEZİ VE BAĞLI",
                   r"BİLİŞİM VADİSİ", r"BİLİŞİM TEKNOLOJİLERİ LABORATUVARI TEFRİŞAT\w*")

WORKS_IT_INSTALL = rx(r"KGYS", r"KENT GÜVENLİ", r"MOBESE", r"KAMERA", r"PLAKA TANIMA", r"\bPTS\b", r"CCTV", r"SCADA",
                      r"FİBER", r"NETWORK", r"\bAĞ (ALT ?YAPI|SİSTEM)", r"KABLOSUZ", r"VERİ MERKEZ", r"SİSTEM ODASI",
                      r"SUNUCU", r"YAZILIM(I|LI|LARI)?\b(?! EĞİTİM)", r"OTOMASYON SİSTEM", r"SİNYALİZASYON",
                      r"TRAFİK YÖNETİM", r"ELEKTRONİK (DENETLEME|HABERLEŞME)", r"TELEKOMÜNİKASYON", r"HABERLEŞME",
                      r"ZAYIF AKIM", r"YAPISAL KABLO", r"UZAKTAN (İZLEME|KONTROL|YÖNETİM)", r"GÜVENLİK VE YÖNETİM SİSTEM",
                      r"GÜVENLİK YÖNETİM SİSTEM", r"KART(LI)? GEÇİŞ", r"ÜCRET TOPLAMA",
                      r"(BİLGİ|BİLİŞİM) SİSTEMİ\w*( \(\w+\))? KURULUM", r"BİLİŞİM ALT ?YAPI", r"VERİ TABANI MERKEZİ",
                      r"ELEKTRONİK BELGE", r"YARGI AĞI")
AMBIGUOUS_STRONG = rx(r"DONANIM\w*", r"KAMERA\w*")

# 1c. weak IT evidence (automation / 'system' words) -> grey unless strong evidence present
WEAK_IT = rx(r"OTOMASYON", r"SİSTEM", r"ELEKTRONİK", r"DİJİTAL", r"UYGULAMA", r"TELEKOM", r"FİBER", r"PLATFORM", r"ENTEGRASYON",
             r"\bE-", r"DEPOLAMA", r"YÖNETİM", r"AKILLI")

# 1d. weak-only titles that are nevertheless IT software/management information systems
WEAK_BUT_IT = rx(r"(FİNANS|MALİ|HARCAMA|İNSAN KAYNAKLARI|KULLANICI|İLİŞKİLERİ|İŞ AKIŞ|PROJE|VARLIK|"
                 r"BAND GENİŞLİĞİ|STOK|İHTİYAÇ VE MALİ|İLETİŞİM|MEDYA VARLIK|SOSYAL TESİSLER|KALKINMA AJANSLARI|"
                 r"DEMİRBAŞ|FİLO|AKADEMİK VERİ|ABONE ADRES|ERİŞİM|SINAV|ARŞİV|EVRAK|DOKÜMAN|BELGE|YAZICI) "
                 r"(\w+ )?(YÖNETİM|OTOMASYON|TAKİP) SİSTEM",
                 r"MALİ OTOMASYON", r"KURUMSAL OTOMASYON", r"KENT YÖNETİM PLATFORM", r"AKILLI (ŞEHİR|KENT)",
                 r"OTOMASYON SİSTEMİ (BAKIM|GÜNCELLE|YAZILIM)", r"MEVCUT OTOMASYON SİSTEMİ",
                 r"RAYLI ULAŞIM YÖNETİM SİSTEMİ", r"TOPLU ULAŞIM YÖNETİM SİSTEMİ", r"VATANDAŞ İLİŞKİLERİ",
                 r"YAŞ ÇAY ALIM OTOMASYON", r"HAL OTOMASYON", r"MEZBAHANE OTOMASYON")

# 1e. hard non-IT evidence (applies when no strong IT evidence)
NONIT_CONSTRUCTION = rx(r"İNŞAAT", r"YAPIM İŞ", r"YAPIMI\b", r"\bKONUT", r"DÜKKAN", r"DERSLİK", r"DERE\b",
                        r"ISLAH", r"ASFALT", r"KALDIRIM", r"KANALİZASYON", r"İÇME ?SUYU", r"TAŞKIN", r"SULAMA",
                        r"BARAJ", r"DEKAPAJ", r"HAFRİYAT", r"ÇEVRE DÜZENLE", r"PEYZAJ", r"MESİRE", r"KÖPRÜ",
                        r"TADİLAT", r"GÜÇLENDİRME", r"YIKIM", r"KERPİÇ", r"SATHİ KAPLAMA", r"YOL YAPIM",
                        r"PREFABRİK", r"DOĞALGAZ DÖNÜŞÜM", r"MEKANİK TESİSAT", r"ELEKTRİK TESİSAT",
                        r"KARAKOL", r"AHIR", r"TANK(I|LARI)? (İMALAT|YAPIM)")
NONIT_VEHICLE_MACHINE = rx(r"KAMYON", r"TUZ SERP", r"SERPİCİ", r"SERPME", r"KAR KÜRE", r"KAR KÜRÜ", r"KAR BIÇA",
                           r"İŞ MAKİN", r"CATERP", r"DOZER", r"GREYDER", r"GRAYDER", r"EKSKAVAT", r"LODER",
                           r"FORKLİFT", r"LASTİK", r"\bAKÜ\b", r"ARAÇ ALIM", r"TAŞIT KİRALA",
                           r"(KAMYON|KÜREME|SERPME|DAMPERLİ|HİZMET|BİNEK|YÜK|MİKSER|İTFAİYE|ÇÖP|VİDANJÖR|HAVA) ARAC",
                           r"OTOBÜS", r"MİNİBÜS", r"ARAÇ KİRALA", r"İNSANSIZ HAVA ARACI", r"DE-İCİNG", r"SÜPÜRGE")
NONIT_FUEL_GOODS = rx(r"AKARYAKIT", r"MOTORİN", r"BENZİN", r"\bLPG\b", r"LİKİT PETROL", r"KÖMÜR ALIM",
                      r"FUEL OİL", r"\bTUZ ALIM", r"SERPİLEN TUZ", r"TATLI", r"GIDA MADDE", r"MOBİLYA", r"TEFRİŞAT",
                      r"TEKSTİL", r"GİYİM", r"KIYAFET", r"SÜLFÜRİK", r"KİMYEVİ", r"SERPANTİN", r"COİL")
NONIT_FACILITY = rx(r"GENEL TEMİZLİK", r"TEMİZLİK HİZMET", r"TEMİZLİK PERSONEL", r"TEMİZLİK İŞÇİ",
                    r"MALZEMELİ TEMİZLİK", r"MALZEMESİZ", r"TEMİZLİK,", r"TEMİZLİK VE", r"TEMİZLİĞİ",
                    r"YEMEK", r"TABLDOT", r"MUTFAK", r"HASTA (BAKIM|DESTEK|SERVİS|YÖNLENDİR|KARŞILAMA)",
                    r"BAHÇIVAN", r"PARK-BAHÇE", r"ÇAMAŞIR", r"STERİLİZASYON", r"GÜVENLİK GÖREVLİ",
                    r"ÖZEL GÜVENLİK", r"KALORİFER", r"ŞOFÖR", r"SÜRÜCÜ", r"TEKNİSYEN", r"BÜRO DESTEK",
                    r"YARDIMCI PERSONEL", r"YARDIMCI HİZMET", r"YARDIMCI SAĞLIK", r"KLİNİK DESTEK",
                    r"KAT DESTEK", r"TIBBİ SEKRETER", r"SEKRETARYA", r"EVDE (SAĞLIK|BAKIM)", r"EĞİTİM BAKIM DESTEK",
                    r"ZİYARETÇİ YÖNLENDİR", r"DANIŞMA VE YÖNLENDİR", r"TERCÜMAN", r"BİYOMEDİKAL",
                    r"TIBBİ CİHAZ", r"TIBBİ VE TEKNİK", r"TIBBİ TEKNİK", r"RADYOTERAPİ", r"FİZİK MÜHENDİS",
                    r"SAĞLIK FİZİKÇİ", r"ULAŞIM HİZMET", r"ULAŞTIRMA\b", r"TAŞIMA(LI)? (EĞİTİM|MERKEZ|YOLUYLA)",
                    r"TEMİZLİK VE YARDIMCI", r"HASTA VE YAŞLI")
NONIT_EVENTS_CONSULT = rx(r"SANATÇI", r"ETKİNLİK", r"KONFERANS", r"KONGRE", r"TOPLANTISI", r"TÖREN",
                          r"FİLM ÇEKİM", r"TANITIM FİLM", r"ORGANİZASYON(U)? HİZMET", r"İNTERPA",
                          r"TETKİK", r"BELGELENDİRME", r"GÖZETİM VE DENETİM", r"HELAL", r"GIDA GÜVENLİĞİ",
                          r"HAVZA", r"SU TAHSİS", r"YERALTI SU", r"SİYANOBAKTERİ", r"HERPETOFAUNA", r"EROZYON",
                          r"MASTERPLAN", r"FİZİBİLİTE", r"MÜŞAVİRLİK", r"KONTROLLÜK", r"PLANLAMA MÜHENDİSLİK",
                          r"PROJE(LERİNİN)? HAZIRLAN", r"PROJE YAPIMI", r"DOKÜMANLARIN HAZIRLANMASI",
                          r"TARAMA PROGRAMI", r"KAN ALMA", r"ENDEKS TESPİT", r"FATURA DAĞIT", r"SAYAÇ DEĞİŞ",
                          r"SAYAÇLARA MÜHÜR", r"KAÇAK", r"ATIK KABİN", r"SIFIR ATIK", r"ÇEVRE DENETÇİSİ",
                          r"ÇED YÖNETMELİĞİ", r"ARAŞTIRILMASI", r"KORUNMASI")
NONIT_BUILDING_SERVICES = rx(r"KLİMA", r"HAVALANDIRMA", r"İKLİMLENDİRME", r"ISITMA", r"SOĞUTMA", r"ASANSÖR",
                             r"JENERATÖR", r"\bKAZAN(I|LARI)?\b", r"BRÜLÖR", r"AYDINLATMA", r"TRAFO",
                             r"(ELEKTRİK|KUMANDA|KUPLAJ|DAĞITIM|ŞALT) PANO", r"ŞALTER",
                             r"İZOLATÖR", r"ENERJİ İLETİM HAT", r"SOĞUK HAVA DEPO", r"YANGIN", r"BİNA BAKIM",
                             r"ATÖLYE", r"TAMİRAT")
NONIT_ALL = [NONIT_CONSTRUCTION, NONIT_VEHICLE_MACHINE, NONIT_FUEL_GOODS, NONIT_FACILITY, NONIT_EVENTS_CONSULT,
             NONIT_BUILDING_SERVICES]
NONIT_NAMES = ["construction", "vehicle_machinery", "fuel_goods", "facility_staffing", "events_consulting_other",
               "building_services"]

# 1e'. dominant non-IT components that turn an otherwise-IT title into a mixed bundle (-> grey)
HARD_BUNDLE = rx(r"GENEL TEMİZLİK", r"(?<!VERİ )TEMİZLİK", r"YEMEK", r"ÇAMAŞIR", r"STERİLİZASYON(?! TAKİP)",
                 r"ÖZEL GÜVENLİK", r"GÜVENLİK GÖREVLİ", r"HASTA (KARŞILAMA|BAKIM|DESTEK|YÖNLENDİR|SERVİS)",
                 r"KLİNİK DESTEK", r"TIBBİ SEKRETER", r"SAYAÇ OKUMA", r"ENDEKS", r"İHBARNAME", r"SANATÇI", r"TÖREN",
                 r"ETKİNLİKLERİ", r"FİLM ÇEKİM", r"\bKONUT", r"İNŞAATI\b", r"YAPIM İŞİ", r"KAMYON", r"AKARYAKIT",
                 r"MOTORİN", r"BENZİN", r"ASANSÖR", r"KALORİFER", r"BAHÇIVAN", r"MUTFAK", r"BİYOMEDİKAL",
                 r"ARAÇ ALIM", r"MOBİLYA", r"TEFRİŞAT")

# 1f. IT-user staffing (data entry / system-user clerks) -> grey, flagged
IT_STAFFING = rx(r"KULLANIM ELEMAN", r"VERİ İŞLE(M|ME) ELEMAN", r"MESLEK ELEMANI VE VERİ", r"KULLANIMINA",
                 r"KULLANIM VE/VEYA", r"BİLGİ İŞLEM VE BİLGİ SİSTEMİ",r"BİLGİ SİSTEMİ? KULLANIM", r"SİSTEM KULLANIM", r"KULLANICISI\b",r"BİLGİSAYAR KULLANICI", r"VERİ GİRİŞ", r"VERİ KAYIT", r"VERİ HAZIRLAMA",
                 r"VERİ İŞLEME VE OTOMASYON", r"KONTROL İŞLETMEN", r"OTOMASYON SİSTEMİNE YÖNELİK",
                 r"BİLGİ İŞLEM (VE BİLGİ SİSTEMİ )?(KULLANIM )?(ELEMAN|PERSONEL)", r"VERİLERİN OTOMASYON",
                 r"(NİTELİKLİ|VASIFLI) PERSONEL", r"PERSONEL DESTEK HİZMET")
# 'teknik destek personeli' style contracts WITHOUT any IT word = facility technicians
TECH_SUPPORT_STAFF = rx(r"TEKNİK DESTEK", r"BAKIM DESTEK", r"BAKIM,? ONARIM")


def classify_scope(title: str, turu: str):
    """Return (scope_v3, reason). title must be tr_upper()'d."""
    t = title
    t_it = BUILDING_NAME.sub(" ", t)
    strong = bool(STRONG_IT.search(t_it))
    weak = bool(WEAK_IT.search(t_it))
    nonit_hits = [n for n, r in zip(NONIT_NAMES, NONIT_ALL) if r.search(t)]
    staffing = bool(IT_STAFFING.search(t))
    if staffing:
        if "facility_staffing" in nonit_hits and not re.search(r"BİLGİ SİSTEM|BİLGİ İŞLEM|NETWORK|YAZILIM", t):
            return "nonIT", "facility_staffing(with data-entry)"
        return "gray", "IT_user_staffing"
    if CALLCENTRE.search(t):
        if "facility_staffing" in nonit_hits:
            return "nonIT", "facility_staffing+callcentre"
        if CALLCENTRE_PRODUCT.search(t):
            return "IT", "callcentre_software_or_equipment"
        return "IT_service_callcentre", "callcentre_service"
    if turu == "Yapım":
        # works contracts: grey only when they install an IT/OT system; building works named after an IT unit
        # (e.g. 'Bilişim Lisesi onarımı', 'Adli Bilişim Dairesi binası') are non-IT
        if WORKS_IT_INSTALL.search(t_it):
            return "gray", "works_contract_IT_installation"
        return "nonIT", "works_contract" + ("(IT_word_in_building_name)" if strong else "")
    if strong and nonit_hits and not STRONG_IT.search(AMBIGUOUS_STRONG.sub(" ", t_it)):
        # the only 'IT' word is an ambiguous one (DONANIM = fittings/equipment, KAMERA on vehicles)
        return "nonIT", "+".join(nonit_hits) + "(ambiguous_IT_word)"
    if strong:
        # strong IT evidence wins, unless the title bundles IT with a dominant non-IT service/good
        if HARD_BUNDLE.search(t):
            return "gray", "mixed_bundle:" + ("+".join(nonit_hits) or "other")
        return "IT", "strong_IT_term"
    if nonit_hits:
        return "nonIT", "+".join(nonit_hits)
    if weak:
        if WEAK_BUT_IT.search(t):
            return "IT", "weak_term_IT_system"
        if re.search(r"(KALİTE|ENTEGRE|ENERJİ|ÇEVRE|İŞ SAĞLIĞI|İSG) YÖNETİM SİSTEM", t):
            return "nonIT", "ISO_management_system"
        return "gray", "automation_or_management_system_only"
    if TECH_SUPPORT_STAFF.search(t):
        return "nonIT", "technical_support_staff_no_IT_term"
    return "nonIT", "no_IT_term"


# ============================================================================= 2. PRODUCT MARKET
PRODUCT_RULES = [  # (code, regex) -- first match wins; order = priority
    ("call_centre_helpdesk", CALLCENTRE),
    ("IT_staffing_data_entry", IT_STAFFING),
    ("health_information_systems", rx(r"\bHBYS\b", r"\bSBYS\b", r"\bLBYS\b", r"\bPACS\b", r"\bDHBYS\b", r"\bYBBYS\b",
        r"\bRIS\b", r"\bHBS\b.*HASTANE", r"HASTANE BİLGİ", r"SAĞLIK BİLGİ", r"LABORATUVAR BİLGİ", r"E-NABIZ",
        r"TELE ?RADYOLOJİ", r"TELETIP", r"HASTA (TAKİP|KAYIT|BİLGİ)", r"TIBBİ (KAYIT|GÖRÜNTÜ)", r"GÖRÜNTÜ ARŞİV",
        r"YOĞUN BAKIM BİLGİ", r"\bTELE ?ICU\b", r"KAN ALMA YÖNETİM", r"İLAÇ YÖNETİM", r"SOĞUK ZİNCİR",
        r"HASTANE (OTOMASYON|YAZILIM)", r"TIBBİ CİHAZ SERVİS YÖNETİM", r"KAĞITSIZ HASTANE")),
    ("GIS_city_information", rx(r"\bCBS\b", r"COĞRAFİ BİLGİ", r"KENT BİLGİ", r"HARİTA", r"NETCAD", r"\bGIS\b",
        r"ORTOFOTO", r"NUMARATAJ", r"ADRES (BİLGİ|YÖNETİM|KAYIT)", r"KADASTRO", r"İMAR (BİLGİ|OTOMASYON|DURUM)",
        r"3 ?BOYUTLU", r"LİDAR", r"UYDU GÖRÜNTÜ", r"MEKANSAL", r"KONUMSAL", r"ORBİS", r"TAPU")),
    ("cybersecurity", rx(r"SİBER", r"FİREWALL", r"GÜVENLİK DUVARI", r"\bSIEM\b", r"LOG YÖNETİM", r"UÇ NOKTA",
        r"ANTİ ?VİRÜS", r"VERİ SIZINTI", r"\bSOC\b", r"BİLGİ GÜVENLİĞ", r"BİLİŞİM GÜVENLİĞ", r"ERİŞİM YÖNETİM",
        r"İNTERNET GÜVENLİĞ", r"SIZMA TEST", r"\bDLP\b", r"\bWAF\b", r"TEHDİT", r"İÇERİK FİLTRE", r"5651")),
    ("physical_security_surveillance", rx(r"KAMERA", r"\bKGYS\b", r"MOBESE", r"KENT GÜVENLİK", r"PLAKA TANIMA",
        r"\bPTS\b", r"CCTV", r"GÜVENLİK SİSTEM", r"GEÇİŞ KONTROL", r"TURNİKE", r"X-RAY", r"GÜVENLİK YÖNETİM SİSTEM")),
    ("education_technology", rx(r"AKILLI TAHTA", r"ETKİLEŞİMLİ", r"EĞİTİM YAZILIM", r"UZAKTAN EĞİTİM",
        r"ÖĞRENME YÖNETİM", r"E-ÖĞRENME", r"\bLMS\b", r"DİJİTAL (İÇERİK|KAYNAK)", r"SINAV", r"ÖĞRENCİ",
        r"KÜTÜPHANE", r"DENEYAP", r"FATİH PROJE", r"OKUL", r"DERS İÇERİK", r"EĞİTİM PLATFORM", r"ROBOTİK",
        r"KODLAMA", r"YAZILIM AKADEMİ", r"EĞİTİM İÇERİ", r"DİJİTAL İKİZ")),
    ("smart_city_traffic_OT", rx(r"TRAFİK", r"SİNYALİZASYON", r"KAVŞAK", r"SCADA", r"OTOPARK", r"AKILLI (ŞEHİR|KENT)",
        r"ULAŞIM YÖNETİM", r"ELEKTRONİK DENETLEME", r"ÜCRET TOPLAMA", r"KARTLI", r"UZAKTAN OKUMA", r"TELEMETRİ",
        r"\bRTU\b", r"AKILLI ŞEBEKE", r"AKILLI SAYAÇ", r"FİLO YÖNETİM", r"ARAÇ TAKİP", r"YOLCU BİLGİLENDİRME",
        r"DEĞİŞKEN MESAJ", r"BİNA OTOMASYON", r"SU YÖNETİM SİSTEM",
        r"(BİNA|İKLİMLENDİRME|KAPI|SULAMA|ARITMA|POMPA|DEPO|TESİS|JEOTERMAL|AMELİYATHANE|HAVUZ|LİMAN|ENERJİ) OTOMASYON",
        r"DEPOZİTO", r"ERKEN UYARI")),
    ("ERP_management_software", rx(r"\bERP\b", r"KURUMSAL KAYNAK", r"MUHASEBE", r"BÜTÇE", r"İNSAN KAYNAKLARI",
        r"MAAŞ", r"BORDRO", r"\bEBYS\b", r"BELGE YÖNETİM", r"DOKÜMAN", r"DÖKÜMAN", r"ARŞİV", r"E-BELEDİYE",
        r"BELEDİYE OTOMASYON", r"BELEDİYE BİLGİ", r"YÖNETİM BİLGİ SİSTEM", r"BİLGİ YÖNETİM SİSTEM", r"MALİ",
        r"FİNANS", r"STOK", r"TAŞINIR", r"\bSAP\b", r"\bCRM\b", r"İŞ AKIŞ", r"SÜREÇ YÖNETİM", r"KALİTE YÖNETİM",
        r"PERSONEL (TAKİP|BİLGİ|YÖNETİM)", r"EVRAK", r"KURUMSAL (YÖNETİM|OTOMASYON|UYGULAMA)", r"İHALE (YÖNETİM|TAKİP)",
        r"VARLIK YÖNETİM", r"TARIM BİLGİ", r"HAYVAN BİLGİ")),
    ("software_licences", rx(r"LİSANS", r"MİCROSOFT", r"ORACLE", r"VMWARE", r"ADOBE", r"AUTOCAD", r"OFFİCE",
        r"\bIBM\b", r"SYBASE", r"SİEBEL", r"RED ?HAT", r"ABONELİK", r"PREMİER")),
    ("network_datacentre_infrastructure", rx(r"SUNUCU", r"STORAGE", r"DEPOLAMA", r"VERİ MERKEZ", r"SİSTEM ODASI",
        r"SWİTCH", r"SWITCH", r"ANAHTAR", r"ROUTER", r"NETWORK", r"\bAĞ\b", r"AĞLARI", r"KABLOSUZ", r"FİBER", r"OPTİK",
        r"SD-WAN", r"SANALLAŞTIRMA", r"YEDEKLEME", r"KESİNTİSİZ GÜÇ", r"\bUPS\b", r"IP TELEFON", r"SANTRAL",
        r"TELEKOMÜNİKASYON", r"HABERLEŞME", r"İNTERNET", r"METRO ETHERNET", r"DATA HAT", r"\bVPN\b", r"ALTYAPI",
        r"ALT YAPI", r"KABİNET", r"DİSK", r"BULUT", r"YÜK DENGELEYİCİ", r"UYDU", r"TELSİZ", r"VERİ İLETİŞİM")),
    ("computers_peripherals", rx(r"BİLGİSAYAR (VE |, )?(ALIM|ALIMI|SATIN|TEMİN|MALZEME|DONANIM|SARF|ÇEVRE)",
        r"BİLGİSAYAR,", r"DİZÜSTÜ", r"MASAÜSTÜ", r"TABLET", r"YAZICI", r"TARAYICI", r"MONİTÖR", r"PROJEKSİYON",
        r"TONER", r"KARTUŞ", r"ÇEVRE BİRİM", r"DONANIM (ALIM|MALZEME|TEMİN)", r"BİLİŞİM (MALZEME|ÜRÜN|CİHAZ)\w* ALIM",
        r"BİLGİSAYAR ALIM", r"KİOSK", r"EKRAN", r"LED ", r"SES,? (IŞIK|GÖRÜNTÜ)", r"GÖRÜNTÜ SİSTEM",
        r"BİLİŞİM MALZEME", r"BİLİŞİM ÜRÜN")),
    # generic 'information / management / automation system' titles -> management software (low priority)
    ("ERP_management_software", rx(r"BİLGİ SİSTEMİ", r"BİLGİ SİSTEMLERİ YAZILIM", r"YÖNETİM SİSTEM", r"OTOMASYON")),
    ("maintenance_support_services", rx(r"BAKIM", r"ONARIM", r"DESTEK HİZMET", r"TEKNİK DESTEK", r"GÜNCELLE",
        r"İDAME", r"YERİNDE DESTEK", r"İŞLETİM", r"İŞLETME HİZMET", r"SÜRDÜRÜLEBİLİR")),
    ("custom_software_web_mobile", rx(r"YAZILIM", r"UYGULAMA", r"\bWEB\b", r"PORTAL", r"MOBİL", r"PLATFORM",
        r"DİJİTAL", r"YAPAY ZEKA", r"VERİ ANALİ", r"ENTEGRASYON", r"PROGRAM", r"SİSTEM")),
]


def classify_product(title: str) -> str:
    for code, r in PRODUCT_RULES:
        if r.search(title):
            return code
    return "other_IT"


# ============================================================================= 3. BUYER SECTOR (v3)
# Ordered rules on tr_upper(kurum). First match wins. Differences to v1 are listed in FIXES_V3 below.
SECTOR_RULES_V3 = [
    ("Belediye/Yerel", rx(r"BELEDİYE", r"BÜYÜKŞEHİR", r"\bİSKİ\b", r"\bASKİ\b", r"\bİZSU\b", r"\bBUSKİ\b",
                          r"\bKASKİ\b", r"\bMASKİ\b", r"\bİETT\b", r"İ\.E\.T\.T", r"\bEGO\b", r"İGDAŞ", r"İSTTELKOM",
                          r"İSBAK", r"METRO İSTANBUL", r"\bİSPER\b", r"İSTON")),
    ("İl Özel/Taşra", rx(r"İL ÖZEL İDARE")),
    ("Sağlık", rx(r"SAĞLIK(?! KÜLTÜR)", r"HASTANE", r"\bTIP\b", r"DİŞ HEK", r"HALK SAĞ", r"TIP MERKEZ")),
    ("Savunma", rx(r"SAVUNMA", r"\bMSB\b", r"KUVVET", r"ASKERİ", r"JANDARMA", r"SAHİL GÜVENLİK", r"SAHİL GÜV",
                   r"TEDARİK MERKEZ", r"TED\.MRKZ", r"TED\.BLG", r"HARP ", r"MKE\b")),
    ("Güvenlik/İçişleri", rx(r"EMNİYET", r"POLİS", r"GÖÇ İDARE", r"NÜFUS", r"İÇİŞLER", r"AFAD", r"AFET VE ACİL")),
    ("Eğitim", rx(r"ÜNİVERSİTE", r"REKTÖR", r"FAKÜLTE", r"MİLLİ EĞİTİM", r"YÜKSEKÖĞRETİM", r"OKUL", r"LİSE",
                  r"SAĞLIK KÜLTÜR", r"MESLEK YÜKSEK", r"ÖSYM", r"ÖLÇME, SEÇME")),
    ("Altyapı/Ulaşım", rx(r"SU VE KANAL", r"GAZ DAĞ", r"ELEKTRİK", r"EDAŞ\b", r"\bTEİAŞ\b", r"\bEÜAŞ\b", r"\bULAŞIM",
                          r"\bULAŞTIRMA", r"KARAYOLLARI", r"HAVALİMAN", r"HAVA LİMAN",
                          r"\bDHMİ\b", r"DEVLET HAVA MEYDAN", r"\bTCDD\b", r"DEMİRYOL", r"\bDSİ\b", r"DEVLET SU İŞLERİ",
                          r"\bLİMAN", r"\bMETRO\b", r"ENERJİ", r"BOTAŞ", r"TELEKOMÜNİKASYON", r"İLETİŞİM BAŞKAN",
                          r"PTT", r"KIYI EMNİYET", r"HAVA TRAFİK")),
    ("Adalet", rx(r"ADALET", r"MAHKEME", r"SAVCILI", r"CEZA İNFAZ", r"YARGITAY", r"DANIŞTAY", r"HSK\b", r"ANAYASA MAHK")),
    ("Sosyal/Maliye", rx(r"\bSGK\b", r"SOSYAL GÜVENLİK", r"VERGİ", r"MALİYE", r"HAZİNE", r"AİLE VE SOSYAL",
                         r"AİLE, ÇALIŞMA", r"ÇALIŞMA VE SOSYAL", r"ÇALIŞMA GENEL MÜDÜR", r"GELİR İDARE", r"İŞ KURUMU", r"İŞKUR", r"GÜMRÜK",
                         r"TİCARET BAKANLIĞI", r"SAYIŞTAY", r"BANKASI")),
    ("İl Özel/Taşra", rx(r"İL ÖZEL İDARE", r"VALİLİ", r"KAYMAKAM", r"YATIRIM İZLEME VE KOORDİNASYON")),
    ("Tarım/Çevre", rx(r"TARIM", r"ORMAN", r"ÇEVRE", r"ŞEHİRCİLİK", r"COĞRAFİ BİLGİ", r"METEOROLOJİ", r"SU İŞLERİ",
                       r"TOPLU KONUT", r"DOĞA KORUMA", r"İKLİM", r"ŞEKER FABRİKA", r"ÇAY İŞLETME", r"TİGEM")),
]

FIXES_V3 = [
    "F1 Turkish-aware upper-casing (v1 used str.upper: 'i'->'I', so mixed-case labels such as 'Belediye', 'İl Özel "
    "İdaresi', 'Milli Eğitim' did not match their rules).",
    "F2 Belediye/Yerel evaluated first: municipal units and municipal companies (İSKİ, İETT, İGDAŞ, İSTTELKOM, İSBAK, "
    "EGO, İZSU...) are municipal buyers even when the label contains SAĞLIK/ULAŞIM/ELEKTRİK.",
    "F3 JANDARMA and SAHİL GÜVENLİK -> Savunma (v1 put 'JANDARMA' in Security before the Defense rule "
    "'JANDARMA GEN', so the Defense rule was dead code).",
    "F4 Word-boundary matching for short tokens: METRO no longer matches METROLOJİ; TIP needs a word boundary "
    "(v1 ' TIP' missed labels starting with 'Tıp Fakültesi'); DSİ, ASKİ, İSKİ, LİMAN, MSB bounded.",
    "F5 'SAĞLIK KÜLTÜR (VE SPOR)' = university Health-Culture-Sports directorates -> Eğitim, not Sağlık.",
    "F6 Defence before Security; MSB supply units ('TED.BLG.BŞK', 'Ted.Mrkz') and 'SAVUNMA SANAYİ' -> Savunma.",
    "F7 Added missing national buyers: ÖSYM/Ölçme-Seçme -> Eğitim; DHMİ spelled out, Demiryolları, BOTAŞ, PTT, "
    "İletişim Başkanlığı -> Altyapı/Ulaşım; Gümrük, İŞKUR, Ticaret Bakanlığı, Sayıştay, banks -> Sosyal/Maliye; "
    "YİKOB -> İl Özel/Taşra; TOKİ, Şeker Fabrikaları, TİGEM, ÇAYKUR -> Tarım/Çevre; AFAD -> Güvenlik/İçişleri; "
    "airports (HAVALİMANI), TEİAŞ/EÜAŞ -> Altyapı/Ulaşım; 'ÇALIŞMA GENEL MÜDÜRLÜĞÜ' -> Sosyal/Maliye.",
    "F8 v1 ' TIP' also matched prison labels 'L TİPİ / F Tipi Cezaevi' (upper-cased to 'TIPI') -> they were Sağlık; "
    "now Adalet. v1 'DİŞ HEK' never matched mixed-case 'Diş Hekimliği Fakültesi' -> now Sağlık (consistent with "
    "'Tıp Fakültesi' -> Sağlık).",
    "F9 'ULAŞTIRMA' inside 'TOPLULAŞTIRMA/KAMULAŞTIRMA' no longer triggers Altyapı; Devlet Su İşleri (spelled out) "
    "-> Altyapı/Ulaşım like 'DSİ' (v1 sent the spelled-out form to Tarım/Çevre via 'SU İŞLERİ').",
    "F10 'İL ÖZEL İDARESİ' is evaluated right after Belediye so its AFAD / health units stay İl Özel/Taşra.",
]


def sector_v3(kurum: str) -> str:
    u = tr_upper(kurum)
    for name, r in SECTOR_RULES_V3:
        if r.search(u):
            return name
    return "Diğer Kamu"


SECTOR_EN = {"Sağlık": "Health", "Belediye/Yerel": "Municipal/Local", "Eğitim": "Education",
             "Altyapı/Ulaşım": "Infrastructure/Transport", "Tarım/Çevre": "Agriculture/Environment",
             "Güvenlik/İçişleri": "Security/Interior", "Sosyal/Maliye": "Social/Finance",
             "İl Özel/Taşra": "Provincial admin", "Savunma": "Defence", "Adalet": "Justice",
             "Diğer Kamu": "Other public"}

# ============================================================================= 4. PROCEDURE
def procedure_v3(u: str):
    """Returns (usul_v3, usul_v3_group)."""
    s = tr_upper(u).replace("İHALE USULÜ:", "").strip()
    if not s or s == "NAN":
        return "unknown", "unknown"
    if s.startswith("AÇIK"):
        return "open", "open"
    if s.startswith("BELLİ"):
        return "restricted", "restricted"
    m = re.search(r"PAZARLIK\s*\(MD\s*21\s*([A-F])\)", s)
    if m:
        return f"negotiated_21{m.group(1).lower()}", "negotiated"
    if "PAZARLIK" in s:
        return "negotiated_untyped", "negotiated"
    if "DOĞRUDAN" in s or "22" in s:
        return "direct_22", "direct"
    return "other", "other"

# ============================================================================= 5. NATURAL PERSONS
LEGAL_TOKENS = rx(r"A\.?\s?Ş", r"\bAŞ\b", r"ANONİM", r"LİMİTED", r"\bLTD", r"ŞTİ", r"ŞİRKET", r"\bKOOP", r"KOOPERATİF",
                  r"VAKF", r"VAKIF", r"BİRLİĞİ", r"ORTAKLI", r"ORTAK GİRİŞİM", r"KONSORS", r"DERNEĞ", r"ODASI",
                  r"ENSTİTÜ", r"ÜNİVERSİTE", r"MÜDÜRLÜĞÜ", r"BAŞKANLIĞI", r"KURUMU", r"İDARESİ", r"\bGMBH", r"\bLLC",
                  r"\bINC\b", r"\bS\.?P\.?A\b", r"\bS\.?A\.?\b", r"\bKG\b", r"\bLTD\b", r"\bPLC\b", r"\bBV\b", r"\bAG\b",
                  r"LİMİTED", r"LIMITED", r"COMPANY", r"CORPORATION", r"\bCO\b", r"\bKOLL", r"\bKOM\b", r"TİC\b",
                  r"TİCARET", r"SANAYİ", r"SAN\b", r"İŞLETME", r"MERKEZİ", r",", r"\+", r"&")
BUSINESS_WORDS = rx(r"BİLİŞİM", r"YAZILIM", r"BİLGİSAYAR", r"TEKNOLOJİ", r"ELEKTRONİK", r"ELEKTRİK", r"İNŞAAT",
                    r"TEMİZLİK", r"GIDA", r"TURİZM", r"OTOMOTİV", r"MÜHENDİSLİK", r"DANIŞMANLIK", r"MEDİKAL", r"SİSTEM",
                    r"GRUP", r"HOLDİNG", r"TELEKOM", r"İLETİŞİM", r"PAZARLAMA", r"HİZMET", r"NAKLİYAT", r"PETROL",
                    r"ENERJİ", r"MAKİNA", r"MAKİNE", r"YAPI", r"TAAHHÜT", r"ORGANİZASYON", r"BİLGİ", r"SOFT", r"DATA",
                    r"NET\b", r"MEDYA", r"REKLAM", r"TEKSTİL", r"EĞİTİM", r"SAĞLIK", r"TIBBİ", r"ARGE", r"AR-GE",
                    r"OTOMASYON", r"TEKNİK", r"PROJE", r"YAYIN", r"MATBAA", r"MOBİLYA", r"KIRTASİYE", r"BÜRO",
                    r"DİJİTAL", r"GLOBAL", r"ULUSLARARASI", r"KURUMSAL", r"SOSYAL", r"ÜRÜN", r"MALZEME", r"TİCARET",
                    r"SANAYİ", r"İTHALAT", r"İHRACAT", r"LOJİSTİK", r"TAŞIMACILIK", r"GÜVENLİK", r"İNSAN KAYNAK",
                    r"MİMARLIK", r"HARİTA", r"PEYZAJ", r"ORMAN", r"TARIM", r"MADENCİLİK", r"KİMYA", r"LABORATUVAR")


def is_natural_person(name: str) -> bool:
    s = tr_upper(name)
    if LEGAL_TOKENS.search(s) or BUSINESS_WORDS.search(s):
        return False
    toks = s.split()
    if not 2 <= len(toks) <= 4:
        return False
    return all(re.fullmatch(r"[A-ZÇĞİIÖŞÜ]+", t) for t in toks)
