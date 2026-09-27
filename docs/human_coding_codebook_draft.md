# İnsan kodlaması: kategori ve tekrar alım kılavuzu taslağı

Durum: henüz insan kodlaması yapılmadı. Bu kılavuz, mevcut 14 kategorinin anlamını kodlayıcıya açıklamak içindir; değerlendirme örneğindeki AI etiketlerini içermez. Yazarlar kategori sınırlarını kodlama başlamadan onaylayıp sürümü dondurmalıdır. Sonradan değişen tanımlar ve yeniden kodlanan kayıtlar ayrıca kaydedilmelidir.

## Bağımsız çalışma

İki kodlayıcı aynı 300 başlığı ve 60 başlık çiftini birbirlerinin ve algoritmaların yanıtlarını görmeden inceler. Kazanan firma ve önceki tedarikçi durumu gösterilmez. Emin olunmayan yanıtı zorlamayın: `unclear` ve kısa bir gerekçe kullanın. Kaynak başlığı veya kimlikleri değiştirmeyin. İki özgün dosya zaman damgası ve SHA-256 ile dondurulduktan sonra uzlaşma yapılır; uzlaşılmış etiketler ayrı dosyaya yazılır.

## Ürün kategorileri

Başlığın anlattığı esas teslimatı değerlendirin. Birden çok eşit ağırlıklı teslimat varsa belirsizliği kaydedin. Kurumun sektörü tek başına ürün kategorisini belirlemez: hastanenin genel bilgisayar alımı, hastane bilgi sistemi değildir.

| Kod | Anlamı |
|---|---|
| `health_information_systems` | Hastane, hasta veya klinik süreçlerini yöneten sağlık bilgi sistemleri; açıkça bu sistemle ilgili kurulum, lisans veya destek. |
| `ERP_management_software` | Kurumsal kaynak planlama veya muhasebe, personel, belge ve iş süreçlerini yöneten genel kurumsal yönetim yazılımı. |
| `custom_software_web_mobile` | Kuruma özel yazılım geliştirme, web sitesi/uygulaması veya mobil uygulama yapımı ve geliştirilmesi. |
| `software_licences` | Başka bir özel kategoriye açıkça girmeyen mevcut yazılımın kullanım hakkı, lisansı veya aboneliği. |
| `network_datacentre_infrastructure` | Ağ, sunucu, veri merkezi, depolama, bağlantı veya bu altyapının kurulumu. |
| `computers_peripherals` | Kişisel bilgisayar, dizüstü, yazıcı ve benzeri son kullanıcı donanımı/çevre birimleri. |
| `maintenance_support_services` | Esas teslimatı bakım, teknik destek veya işletim olan genel IT hizmetleri; yeni geliştirme veya yalın lisans alımından ayırın. |
| `physical_security_surveillance` | Kamera, görüntülü gözetim, fiziksel erişim veya elektronik güvenlik sistemleri. |
| `GIS_city_information` | Coğrafi bilgi, kent bilgi, haritalama veya açıkça mekânsal bilgi sistemi. |
| `cybersecurity` | Bilgi/ağ güvenliği, siber savunma, güvenlik testi veya güvenlik yazılımı ve cihazları. |
| `smart_city_traffic_OT` | Akıllı şehir, trafik yönetimi, endüstriyel/operasyonel kontrol ve otomasyon sistemleri. |
| `education_technology` | Öğrenme, sınav veya eğitim süreçlerine özgü dijital sistem ve teknolojiler. |
| `call_centre_helpdesk` | Çağrı merkezi, iletişim merkezi veya yardım masası sistemi/hizmeti. |
| `other_IT` | Başlık açıkça IT alımıdır ancak yukarıdaki kategorilerden biriyle yeterince tanımlanamaz. Bilgi yetersizliği ile başka kategoriye ait olma arasında ayrım yapın. |

Sağlık/GIS gibi adı açıkça belirtilen uzmanlaşmış sistemin bakım veya lisansı, genel bakım/lisans ile karışabilir. Kodlayıcı uzmanlaşmış sistemi seçerken gerekçesini kaydetmelidir. Hem yeni geliştirme hem mevcut sistem bakımı gibi sınır durumlarını belirsiz işaretleyin. Bu kılavuz, başlıktan anlaşılmayan teknik şartname bilgilerini varsaymanızı istemez; kategori bir rekabet hukuku ilgili pazarı değildir.

Her kayıt için `IKN`, `your_label`, `unclear` (yes/no) ve `note` saklanır. Kategori kararının yanı sıra başlığın yeterli bilgi verip vermediği de kaydedilir. Karar verilemiyorsa `your_label=unclear` kullanılır; sessizce silinmez.

## Başlık çiftleri

İki başlığın aynı tekrarlanan hizmet/ürün ihtiyacını anlatıp anlatmadığını değerlendirin:

- `same`: açıkça aynı temel sistem/hizmetin yeniden alımıdır.
- `different`: esas sistem veya teslimat farklıdır.
- `unclear`: benzer sözcükler vardır ancak başlıklar karar vermeye yetmez veya paket kapsamı belirsizdir.

Yalnızca ortak genel kelimeler, aynı kurum veya yakın tarihler `same` için yeterli değildir. Karar, hukuki sözleşme uzatmasını doğrulamaz. Her çiftte `pair_id`, `your_label` ve kısa gerekçe saklanır. Zaman aralığını görmek, önceki tedarikçinin kimliğini bilmek anlamına gelmez.

## Sonuçların kullanımı

Asıl analiz ve belirsizlik planı `human_validation_protocol.md` içindedir. Çift örneği benzerlik bantlarına göre seçildiği için basit toplam doğruluk, tüm alımların duyarlılık/özgüllüğü olarak sunulmaz. AI veya kural yanıtları ancak özgün insan etiketleri dondurulduktan sonra karşılaştırılır. Bu dosya ve boş formlar, insan doğrulamasının tamamlandığını göstermez.
