# Veri Sözlüğü (Data Dictionary)

Kaynak: UCI Bank Marketing arşivindeki **bank-full.csv / bank-names.txt**.
Veri 2008–2010 döneminde Portekiz'de tek bankanın telefon kampanyalarıyla ilgilidir.
Yıl/tam tarih ve müşteri kimliği CSV'de yoktur. Kaynak sırası tam tarih değildir.

| Alan | Açıklama | Tip / birim | Karar |
|---|---|---|---|
| age | Yaş | Tamsayı, yıl | Pozitiflik kontrolü |
| job | Meslek | Kategori | unknown → eksik |
| marital | Medeni durum | married, single, divorced | divorced dul kişileri de kapsar |
| education | Eğitim | primary, secondary, tertiary | unknown → eksik |
| default | Temerrütte kredi var mı? | yes/no | Korunur; hedef değil |
| balance | Yıllık ortalama bakiye | Tamsayı, EUR | Negatifler ve uçlar korunur |
| housing | Konut kredisi var mı? | yes/no | Korunur |
| loan | Bireysel kredi var mı? | yes/no | Korunur |
| contact | İletişim kanalı | telephone/cellular | unknown → eksik |
| day | Son temasın ayın kaçıncı günü olduğu | 1–31 | Tam tarih değil |
| month | Son temas ayı | jan–dec | Yıl bilgisi yok |
| duration | Son görüşme süresi | Tamsayı, saniye | Sıfırlar ve uçlar korunur; görüşme öncesi bilinmez |
| campaign | Mevcut kampanyadaki temas sayısı | Tamsayı, adet | Son temas dahil; en az 1 |
| pdays | Önceki kampanya temasından geçen gün | Tamsayı, gün veya -1 | -1: önceki temas yok |
| previous | Mevcut kampanyadan önceki temas sayısı | Tamsayı, adet | Sıfır geçerli |
| poutcome | Önceki kampanya sonucu | success/failure/other/unknown | Ham kod korunur |
| y | Vadeli mevduata abone olmuş mu? | yes/no | Betimsel sonuç değişkeni; model yok |

## Türetilmiş alanlar

| Alan | Anlam |
|---|---|
| source_row | Ham CSV veri satırının 1 tabanlı sırası; müşteri ID'si değil |
| subscribed | y=yes için 1, y=no için 0 |
| prior_contact | pdays != -1 |
| pdays_since_prior | Sadece önceki temas varsa gün sayısı; diğerleri yapısal boş |
| prior_outcome | poutcome=unknown için boş; diğerleri kaynak etiketi |
| prior_outcome_missing_reason | observed / not_applicable_no_prior_contact / unknown_despite_prior_contact |

Temas grupları 1, 2, 3, 4, 5, 6–10, 11+ olarak yalnız tablo/görsel için türetilir.
Kategorik oran tablolarında bilinmeyenler `Bilinmiyor` etiketiyle gösterilir;
temiz dosyada eksiklik olarak saklanır.
