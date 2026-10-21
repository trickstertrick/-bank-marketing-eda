# Banka Kampanyalarında Keşifsel Veri Analizi

[GitHub deposu](https://github.com/trickstertrick/-bank-marketing-eda)

**bank-marketing-eda** · Python / pandas / NumPy / matplotlib / Jupyter

Bir bankanın kampanya verisinde eksik bilgileri, bakiye dağılımını ve gözlenen
abonelik örüntülerini inceleyen, açıklamalı bir keşifsel veri analizi
(exploratory data analysis — EDA). **Tahmin modeli veya nedensel analiz içermez.**

## Tamamlanan çalışma ve ilk bulgular

- **45.211 kaynak kaydı, 17 kaynak alanı**; temizlemede satır silinmedi.
- `contact` 13.020, `education` 1.857, `job` 288 kayıtta bilinmiyor.
- Üç alandan en az biri bilinmeyen 14.304 kayıt korundu.
- Ortalama bakiye **1.362,27 EUR**, medyan **448 EUR**.
- **4.729 bakiye** IQR çitlerinin dışında (%10,46); silinmedi.
- Yedi açıklamalı grafik, baştan sona çalıştırılmış 24 hücreli defter,
  **12 geçen bütünlük kontrolü ve 10 geçen birim testi**.

## Araştırma soruları

1. Eksik müşteri/temas bilgisi hangi alanlarda ve birlikte eksiklik örüntülerinde yoğunlaşıyor?
2. Bakiye dağılımındaki çarpıklık, negatif bakiyeler ve IQR aykırıları nasıl yorumlanmalı?
3. Eğitim düzeyi ve kampanya temas sayısı gruplarında gözlenen abonelik oranları nasıl farklılaşıyor?

## Önce bunları açın

- [Çalıştırılmış Jupyter Notebook](notebooks/01_bank_marketing_eda.ipynb): tablolar,
  yedi gömülü grafik, her grafiğin altında bulgu ve sınırlama.
- [Kısa bulgu raporu](reports/findings.md): aynı sonuçların Markdown sürümü.
- [Temizleme kararları](docs/cleaning_decisions.md), [veri sözlüğü](docs/data_dictionary.md).
- [Mülakat cevapları ve CV açıklaması](docs/interview_and_cv.md).
- [GitHub'a yükleme adımları](docs/github_upload.md).

## Örnek görseller

![Kaynak unknown kodlarıyla eksik bilgiler](reports/figures/01_missing.png)

![Bakiye dağılımı ve aykırı gözlemler](reports/figures/03_balance_distribution.png)

Her grafiğin ölçülmüş bulgusu ve sınırlaması defterde ve bulgu raporunda yer alır.

## Veri kaynağı ve kullanım koşulları

[UCI Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing),
**bank-full.csv eski sürümü**; Portekiz'de bir bankanın 2008–2010 dönemindeki
telefon kampanyaları. `bank-additional-full.csv` kullanılmıyor.

Lisans: **CC BY 4.0**; kaynak, lisans ve değişiklik bilgileri korunmalıdır.
Atıflar ve bağlantılar [kaynak/lisans belgesinde](docs/sources_and_license.md).
Ham dosya ve kaynak arşivi bu başlangıç paketinde bulunur; CSV büyüklüğü GitHub
sınırlarının altındadır. Git deposuna veri eklemek yerine varsayılan `.gitignore`
politikasıyla betik üzerinden indirme tercih edilir.

**Eksiklik ayrımı:** Kaynakta literal boş/NA olmaması, bilgi eksikliği olmadığı
anlamına gelmez. `job`, `education`, `contact` alanlarının gerçek `unknown`
kodları eksik tutulur. `pdays=-1` daha önce temas edilmemesi anlamındadır;
gerçek gün veya sıradan eksik değer değildir. Yapay eksik/aykırı veri eklenmedi.

## Kurulum — Windows PowerShell

Python 3.11+ önerilir. Proje klasöründe çalıştırın; etkinleştirme zorunlu değil.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.download
.\.venv\Scripts\python.exe scripts\build_notebook.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Notebook üretim betiği doğru Python ortamıyla yerel çekirdek başlatır; kullanıcı
düzeyinde çekirdek kaydı gerekmez. Çalıştırma tamamlanınca defteri çıktılarıyla
kaydeder. Mevcut ham dosyayı yeniden indirmez; kaynak kaydı ve hash'i doğrular.
Yeni veri anlık görüntüsü için mevcut dosyaları sessizce değiştirmek yerine ayrı
proje kopyası kullanın. İlk indirme ve paket kurulumu internet gerektirir.

Notebook'u yalnız okumak için Python kurulumu gerekmez; GitHub önizlemesi veya
VS Code/Jupyter uyumlu bir görüntüleyici kullanılabilir. İnteraktif JupyterLab
kurulumu bu minimum bağımlılık listesinin kapsamında değildir.

## Analiz kararları

- Hiçbir satır veya IQR aykırısı otomatik silinmez; bakiye değiştirilmez.
- `unknown` değerler modla doldurulmaz, grup özetlerinde bilinmeyen ayrı gösterilir.
- Yapısal uygulanamazlık ile eksik bilgi ayrı türetilmiş alanlarda izlenir.
- Sayısal ve kategorik alan kuralları ihlalinde süreç sessizce veri silmez; durur.
- Birebir özellik tekrarı, müşteri kimliği olmadığı için otomatik yinelenen kişi sayılmaz.
- Asinh/symlog yalnız grafik ölçeğini değiştirir; negatif bakiyeleri korur.
- Spearman, eksiksiz sayısal sütunların ortalama bağlı sıraları üzerinden hesaplanır.
- Oranlar, paydalarıyla birlikte betimseldir; p değeri/güven aralığı hesaplanmaz.

## Dosya yapısı

```text
bank-marketing-eda/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/                   # Kaynak ZIP, CSV ve orijinal sözlük
│   ├── processed/             # Ayrı temiz veri
│   └── source_metadata.json   # Kaynak, indirme zamanı, SHA-256
├── docs/                      # Kararlar, sözlük, lisans, mülakat/CV
├── notebooks/
│   └── 01_bank_marketing_eda.ipynb
├── src/                       # Veri edinme ve yeniden kullanılabilir EDA
├── scripts/build_notebook.py  # Üretim + baştan sona gerçek yürütme
├── tests/                     # Yapay küçük birim testi örnekleri; EDA'ya eklenmez
└── reports/                   # Bulgular, grafikler, CSV tablolar ve ortam kaydı
```

## Kontroller ve tekrar üretilebilirlik

Ham dosya SHA-256, gözlem sayısı, bakiye/sonuç etiketlerinin korunması, eksiklik
kodlarının eşleşmesi, kaynak sırası, grup paydaları ve yedi grafik doğrulanır.
Notebook hata çıktısı olmadan baştan sona çalıştırılır; ek birim testleri kenar
durumlarını kontrol eder. Sonuçlar `reports/audit.json` dosyasına kaydedilir.
Python/paket sürümleri `reports/environment.json` içindedir.

## Örneklem ve yorum sınırları

Veri tek bankanın tarihsel kampanya kayıtlarıdır; rastgele nüfus örneklemi veya
güncel Türkiye müşterileri değildir. Müşteri kimliği ve tam tarih yoktur; kayıtlar
bağımsız kişiler olarak varsayılmıyor. Daha fazla arama ile düşük abonelik
birlikteliği, aramanın olumsuz nedensel etkisini kanıtlamaz. `duration` görüşme
sonrası bilinir. Bu EDA'dan doğrudan müşteri hedefleme kararı verilmez.

## Atıf

Moro, S., Rita, P., & Cortez, P. (2014). *Bank Marketing* [Dataset].
UCI Machine Learning Repository. https://doi.org/10.24432/C5K306

Eski sürümle gelen 2011 makale atfı da `docs/sources_and_license.md` içindedir.
