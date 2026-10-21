# GitHub'a Yükleme

Bu proje deposu: https://github.com/trickstertrick/-bank-marketing-eda

Aşağıdaki adımlar, yerel proje kopyasını yeni bir depoya yüklemek için referanstır.
Bu depoyu klonladıysan yeniden git init veya remote add çalıştırman gerekmez.

## Depo oluşturma

GitHub hesabında `-bank-marketing-eda` adlı boş bir depo (repository) oluştur.
Yerel dosyalar hazır olduğundan uzak depoya başlangıç README'si ekleme.
Git kuruluysa aşağıdaki komutları **yalnız bu proje klasöründeki terminalde**
çalıştır. Başka bir Git deposunun içindeysen önce projeyi bağımsız bir klasöre kopyala.

```powershell
git init
git add .
git status
git commit -m "Banka kampanyası EDA projesini ekle"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADI/-bank-marketing-eda.git
git push -u origin main
```

`KULLANICI_ADI` yerine kendi kullanıcı adını yaz. Kimlik doğrulamasını kendi
Git/GitHub aracınla tamamla; erişim anahtarı veya parolayı kod dosyalarına koyma.

## Yüklemeden önce kontrol

- README, çalıştırılmış `.ipynb`, `src`, `scripts`, `tests`, `docs`, `reports`
  ve `data/source_metadata.json` mevcut olmalı.
- `.venv`, `.runtime`, `.ipython`, `.mpl-cache` ve büyük ham/temiz veri dosyaları
  `.gitignore` ile dışarıda bırakılır.
- Ham veri olmadan ilk çalıştırma `python -m src.download` ile indirilir.
- Notebook içine yedi grafik gömülüdür; rapor görselleri de `reports/figures` içindedir.
- Kaynak ve CC BY 4.0 atıflarını koru; CV linkini gerçek depo adresinle güncelle.

## Önerilen depo açıklaması

“UCI Bank Marketing verisiyle eksik bilgi, aykırı gözlem ve kampanya örüntüleri:
45.211 kayıt, 7 açıklamalı grafik ve çalıştırılmış EDA defteri.”

Önerilen konu etiketleri: `python`, `pandas`, `eda`, `data-cleaning`,
`data-visualization`, `bank-marketing`, `statistics`.
