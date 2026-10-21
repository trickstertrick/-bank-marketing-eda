# Temizleme Kararları (Cleaning Decisions)

1. **Satırlar:** Hiçbiri silinmez. Birebir tekrarlar sayılır; müşteri kimliği
   olmadığından özellik eşitliği aynı müşterinin yanlış tekrarı sayılmaz.
2. **job:** `unknown` → eksik. Mesleği başka alanlardan tahmin etmek yanlış
   kesinlik yaratır; modla doldurulmaz. Grafiklerde bilinmeyen ayrı tutulur.
3. **education:** `unknown` → eksik. Eksik eğitim gerçek eğitim seviyesi değildir;
   modal eğitim atayıp dağılımı değiştirmeyiz.
4. **contact:** `unknown` → eksik. Büyük eksiklik oranında satır silmek örneklemi
   değiştirebilir; kanal oranları yalnız bilinenler için veya bilinmeyen ayrı
   gösterilerek yorumlanmalıdır. Bu EDA'da doldurulmaz.
5. **pdays:** -1, daha önce temas edilmemiş anlamındadır; ortalama/medyana gerçek
   gün gibi katılmaz. Orijinal alan korunur, `prior_contact` ve yalnız temas
   edilmişlerde gün sayısı içeren `pdays_since_prior` türetilir.
6. **poutcome:** Orijinal `unknown` kodu korunur. `prior_outcome` alanında bilinmeyen
   sonuç boş bırakılır; neden, `prior_outcome_missing_reason` ile temas yokluğu
   (yapısal uygulanamazlık) ve temas olmasına rağmen bilinmezlik olarak ayrılır.
7. **age, balance, day, duration, campaign, previous:** Sonlu tamsayı ve alan
   kuralları kontrol edilir. Hatalı değer görülürse süreç durur; sayısal eksik
   yaratılıp ortalamayla kapatılmaz. Negatif bakiye otomatik geçersiz değildir.
8. **Diğer kategoriler:** Kaynak sözlüğüyle doğrulanır; beklenmeyen kategori hata
   üretir. Yes/no etiketleri korunur; oran için `subscribed` 0/1 türetilir.
9. **Aykırılar:** IQR çitleri işaretleme içindir. Kırpma (clipping), winsorization,
   silme veya log dönüşümüyle temiz değer değiştirme yapılmaz. Görsellerdeki
   asinh/symlog dönüşümü negatifleri ve uçları görünür kılar.
10. **İzlenebilirlik:** `source_row` ham CSV sırasını izler, müşteri kimliği
    değildir. Ham dosya hash'i analiz öncesi/sonrası doğrulanır.

## Eksiklik mekanizması

`unknown` bilgisinin neden eksik olduğu veriyle kesinleşmez. Tamamen rastgele
eksiklik (MCAR), gözlenenlere bağlı eksiklik (MAR) veya gözlenmeyene bağlı eksiklik
(MNAR) varsayımı yapmıyoruz. Birlikte eksiklik örüntüleri betimsel ipuçlarıdır.

UCI üst verisinin “eksik yok” beyanı ile analiz çelişmez: dosyada literal boş/NA
değer olmaması, `unknown` ile belirtilmiş bilgi eksikliğinin bulunmaması demek değildir.

## Sürüm seçimi

Bu kararlar `bank-full.csv` eski sürümü içindir; `bank-additional-full.csv` için
alan adları, kategoriler ve pdays kodu farklıdır. Dosyalar birbirinin yerine kullanılmaz.
