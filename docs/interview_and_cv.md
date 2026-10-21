# Mülakat Hazırlığı ve CV Açıklaması

Bu cevaplar aynı paketteki gerçek analiz sonuçlarına dayanır. Kodları inceleyip
kararları kendi cümlelerinle açıklayabildiğinde kullan. Yapmadığın modeli,
hipotez testini veya iş etkisini varmış gibi anlatma.

## 1. Veri setini neden seçtin? Gerçekten eksik değer var mı?

“Bankacılık bağlamında sayısal ve kategorik alanları birlikte incelemek istedim.
45.211 kampanya kaydı ve 17 kaynak alanı var. Literal boş/NA yok; fakat job,
education ve contact alanlarında unknown ile kodlanmış eksik bilgi var.
Örneğin contact 13.020 kayıtta bilinmiyor. Kaynağa yapay eksik eklemedim.”

Takip sorusu: `pd.read_csv(..., keep_default_na=False)` ile kaynak kodlarını
önce koruduğumuzu, sonrasında sütun bazında dönüştürdüğümüzü gösterebilirsin.

## 2. Neden eksikleri silmedin veya modla doldurmadın?

“Üç alandan en az biri bilinmeyen 14.304 kayıt vardı. Tam-vaka silme, mevcut
verinin yaklaşık üçte birini çıkaracaktı ve örneklemin bileşimini değiştirebilirdi.
Modla doldurma da bilinmeyen grubu en sık gruba taşırdı. EDA için eksikleri
korudum; grup oranlarında bilinmeyenleri ayrı gösterdim. Eksiklik mekanizmasının
MCAR/MAR/MNAR olduğunu bu veriden kanıtladığımı iddia etmiyorum.”

## 3. IQR kuralına göre aykırı bakiyeleri neden silmedin?

“1,5×IQR çitleri 4.729 bakiyeyi, yani yaklaşık %10,46'yı işaretledi.
Bu istatistiksel etikettir, hata kanıtı değildir. 3.766 negatif bakiye de
otomatik hata sayılmaz. Ortalama bakiye 1.362,27 EUR, medyan 448 EUR;
sağ kuyruğun ortalamaya etkisini birlikte yorumladım. Uçları koruyup asinh ve
symlog ölçekleriyle gösterdim; ham/temiz bakiye değerleri aynı kaldı.”

## 4. pdays=-1 ve poutcome=unknown değerlerini nasıl ele aldın?

“pdays=-1, önceki kampanyada temas edilmemesi anlamında. Orijinal alanı koruyup
yalnız önceki temas varsa gün sayısı içeren yeni bir alan oluşturdum.
poutcome=unknown olan 36.959 kaydın 36.954'ünde önceki temas yok; 5'inde ise
temas olmasına rağmen sonuç bilinmiyor. Yapısal uygulanamazlık ile eksik bilgiyi
ayırdım; -1'i ortalama gün hesabına katmadım.”

## 5. Daha çok temas aboneliği azaltıyor diyebilir misin? Analizi nasıl doğruladın?

“Hayır. Tek temas grubunda gözlenen abonelik %14,60; 11+ temas grubunda %3,93.
Aramalar rastgele atanmadı; ikna edilmesi zor kayıtlarda daha fazla temas
olabilir. Sonucu nedensel etki veya politika önerisi olarak yorumlamadım.
Ham hash, 45.211 satırın korunması, bakiye/sonuç etiketleri, eksiklik eşlemesi
ve grup paydaları için 12 bütünlük kontrolü çalıştı. Ek olarak 10 birim testi
geçti ve defter baştan sona hata çıktısı olmadan yürütüldü.”

## CV için iki cümle

Python (pandas, NumPy, matplotlib) ile UCI Bank Marketing veri setindeki
45.211 kampanya kaydında eksik bilgi, betimsel istatistikler ve IQR tabanlı
aykırı gözlem analizi gerçekleştirdim. Yedi açıklamalı görselleştirme içeren
çalıştırılmış Jupyter Notebook hazırladım; veri dönüşümlerini 12 bütünlük
kontrolü ve 10 birim testiyle doğruladım.

## 30 saniyelik proje anlatımı

“Projemde model kurmadan önce veri kalitesini ve dağılımları anlamaya odaklandım.
Kaynakta boş değer görünmese bile unknown kodlarının eksik bilgi taşıdığını,
önceki temas yokluğunun ise yapısal olarak farklı olduğunu gösterdim. Eksikleri
doldurmadan ve uç değerleri silmeden grupları paydalarıyla karşılaştırdım.
Çıktılarım tekrar çalıştırılabilir bir defter, yedi grafik ve karar raporu.”
