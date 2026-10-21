"""Analiz defterini üret ve aynı Python ortamının çekirdeğiyle baştan sona çalıştır."""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Yerel çekirdek ve önbellekler proje içinde kalır; kullanıcı dizinine kayıt yok.
for key, subfolder in {"MPLCONFIGDIR":".mpl-cache", "IPYTHONDIR":".ipython",
                       "JUPYTER_DATA_DIR":".runtime/data", "JUPYTER_RUNTIME_DIR":".runtime/run",
                       "JUPYTER_CONFIG_DIR":".runtime/config"}.items():
    os.environ[key] = str(ROOT / subfolder)
    (ROOT / subfolder).mkdir(parents=True, exist_ok=True)

import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def main():
    cells = []
    def md(text):
        cells.append(nbf.v4.new_markdown_cell(text))
    def code(text):
        cells.append(nbf.v4.new_code_cell(text))
    md("""# Banka Kampanyalarında Keşifsel Veri Analizi

**Proje:** bank-marketing-eda · **Düzey:** İstatistik lisans · **Kapsam:** EDA, model yok.

Amaç eksik bilgiyi, finansal dağılımları ve kampanya kayıtlarının örüntülerini
gerçek veriyle incelemektir. Her grafik bir soru, ölçülmüş bulgu ve sınırlama içerir.

## Üç araştırma sorusu
1. Eksik müşteri/temas bilgisi nerede ve hangi birlikte eksiklik örüntülerinde yoğunlaşıyor?
2. Bakiye dağılımında çarpıklık ve IQR ile işaretlenen gözlemler nasıl yorumlanmalı?
3. Eğitim ve temas sayısı gruplarında gözlenen abonelik oranları nasıl farklılaşıyor?

## Kaynak ve lisans
[UCI Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing),
**bank-full.csv** eski sürümü (balance alanı EUR). CC BY 4.0; atıf zorunludur.
bank-additional-full.csv ile karıştırılmamalıdır. Atıflar `docs/sources_and_license.md` içindedir.

UCI 'eksik yok' der; dosyada boş/NA yerine bazı alanlarda `unknown` vardır.
Bu anlamsal bilinmeyenleri (semantic missingness) inceliyoruz; yapay eksik üretmiyoruz.
`pdays=-1` ise önceki temasın olmaması anlamındadır: yapısal uygulanamazlık (not applicable).
""")
    code("""from pathlib import Path
import sys
import json
import platform
from importlib.metadata import version
import numpy as np
import pandas as pd
from IPython.display import display, Markdown, Image

ROOT = Path.cwd()
if ROOT.name == 'notebooks':
    ROOT = ROOT.parent
assert (ROOT / 'src' / 'analysis.py').exists(), 'Çalışma dizini proje klasörü olmalı.'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.download import ensure_raw, digest
from src.analysis import load_raw, audit_raw, clean_data, build_tables, plot_all, export_results
pd.set_option('display.max_columns', 24)
pd.set_option('display.float_format', lambda value: f'{value:,.3f}')
""")
    md("""## 1. Ham veri ve kaynak kaydı
Ham dosyaya yazmıyoruz. İlk çalıştırma UCI arşivini indirir; sonraki çalıştırma
aynı anlık görüntünün hash'ini doğrular. Veri güncellenirse eski bulguların aynı
kalacağı varsayılmaz. Kaynağın boş değer kodlarını otomatik dönüştürmemek için
CSV önce metin olarak okunur; sayısal dönüşüm kontrollü yapılır.""")
    code("""raw_path, metadata = ensure_raw()
raw_hash_before = digest(raw_path.read_bytes())
raw = load_raw(raw_path)
display(pd.Series({
    'kaynak': metadata['source_page'], 'sürüm': metadata['variant'],
    'indirme_UTC': metadata['retrieved_at_utc'], 'lisans': metadata['license'],
    'ham_satır': len(raw), 'ham_sütun': raw.shape[1], 'sha256': raw_hash_before
}).to_frame('değer'))
display(raw.head())""")
    md("""## 2. Veri tipleri, alan kuralları ve tekrarlar
Yaş yıl, bakiye EUR, görüşme süresi saniye; campaign/previous temas sayısıdır.
CSV önce metin yüklendiği için başlangıçtaki metin tipleri kaynağın gerçek
ölçüm düzeyi değildir. Temizlemede sonlu tamsayılar ve belgelenmiş kategoriler doğrulanır.

Negatif bakiye otomatik hata değildir. Tam yıl/tarih ve müşteri kimliği yoktur;
aynı özelliklere sahip iki satır kesinlikle aynı müşteri sayılmaz. Birebir
tekrarlar sayılır ama kimlik kanıtı olmadan silinmez.""")
    code("""raw_audit = audit_raw(raw)
display(pd.Series({k:v for k,v in raw_audit.items() if not isinstance(v,dict)}).to_frame('değer'))
display(pd.Series(raw_audit['unknown_by_column'], name='unknown_sayısı').to_frame())
clean = clean_data(raw)
display(clean.dtypes.astype(str).to_frame('temiz_veri_tipi'))
display(pd.DataFrame({'aşama':['ham','temiz'], 'satır':[len(raw),len(clean)],
                      'sütun':[raw.shape[1],clean.shape[1]], 'silinen_satır':[0,0]}))""")
    md("""## 3. Sütun bazında eksik bilgi kararı
- **job, education, contact:** kaynak `unknown` kodları `pd.NA` olarak tutulur.
  Mod veya ortalamayla doldurulmaz; kategorik grafiklerde bilinmeyen grup gösterilir.
- **pdays:** ham -1 kodu korunur; türetilmiş `pdays_since_prior` alanında bu
  satırlar yapısal boş olarak tutulur. Ortalama alınırken -1 gerçek gün sayılmaz.
- **poutcome:** ham unknown korunur. Türetilmiş önceki sonuçta, temas olmamasına
  bağlı uygulanamazlık ile temas olmasına rağmen bilinmeyen sonuç ayrılır.
- **Diğer alanlar:** beklenmeyen değer veya eksik bulunursa otomatik silinmez;
  doğrulama hata üretir. Mevcut veri üzerinde bulgu neyse o raporlanır.

Tam-vaka silme (complete-case deletion), eksikliği yüksek alanlarda örneklemi
küçültebilir ve bileşimini değiştirebilir. Bu EDA'da satırlar korunur. Eksiklik
mekanizmasının MCAR/MAR/MNAR olduğu kanıtlanmış değildir.""")
    code("""tables = build_tables(raw, clean)
display(tables['missing_profile'])
display(tables['missing_patterns'])
display(clean.prior_outcome_missing_reason.value_counts().to_frame('n'))""")
    md("""## 4. Betimsel istatistikler ve aykırı gözlemler
Ortalama uç değerlerden etkilenir; medyan sıralamaya dayanır. Standart sapma
yayılımı, çeyrekler dağılımın orta kısmını özetler. Para, saniye ve sayı
ölçeklerini birbirine karıştırmadan yorumlarız.

**IQR = Q3 − Q1**; alt/üst çitler Q1 − 1,5×IQR ve Q3 + 1,5×IQR.
Çit dışı olmak hata veya dolandırıcılık kanıtı değildir. IQR=0 ise ender fakat
geçerli değerler de işaretlenebilir. Hiçbir aykırı değer silinmez/kırpılmaz.
""")
    code("""display(tables['descriptive_statistics'])
display(tables['outlier_profile'])
display(tables['category_counts'])
balance_profile = tables['outlier_profile'].loc['balance']
balance_flags = clean.balance.lt(balance_profile.lower_fence) | clean.balance.gt(balance_profile.upper_fence)
assert int(balance_flags.sum()) == int(balance_profile.flagged_n)
display(clean.loc[balance_flags, ['source_row','balance','age','y']].head(10))""")
    md("""## 5. Yedi grafik: soru → bulgu → sınırlama
İşaret koruyan asinh ve symlog, negatif ve yüksek bakiyeleri birlikte görünür
kılar. Bunlar yalnız görüntüleme dönüşümüdür, para değerlerini değiştirmez.
Oranların paydaları gösterilir. Bu çalışma hipotez testi veya nedensel analiz değildir.""")
    code("""figures = plot_all(clean, tables, ROOT / 'reports' / 'figures')
print(f'{len(figures)} grafik üretildi. Ham gözlemlerden hiçbiri çıkarılmadı.')""")
    for i in range(7):
        code(f"""note = figures[{i}]
display(Markdown('### ' + note['title']))
display(Image(filename=str(ROOT / 'reports' / 'figures' / note['filename'])))
display(Markdown('**Bulgu:** ' + note['finding'] + '\\n\\n**Sınırlama:** ' + note['limitation']))""")
    md("""## 6. Araştırma sorularının sayısal özeti
Abonelik (`y`) yalnız betimsel grup karşılaştırmasında kullanıldı; tahmin modeli
eğitilmedi. `duration` son görüşme bitince bilinir; ileride bir hedefleme modeli
kurulursa önceden bilinebilen değişkenmiş gibi kullanılması sızıntı riski taşır.""")
    code("""display(tables['education_rates'])
display(tables['campaign_rates'])
display(tables['spearman'])
display(Markdown(f'Genel gözlenen abonelik oranı: **%{100*clean.subscribed.mean():.2f}**. '
                 'Bu oran yalnız mevcut kampanya kayıtlarını betimler.'))""")
    md("""## 7. Bütünlük kontrolleri ve dosyaların dışa aktarımı
Gözlem sayısı, bakiye, sonuç etiketi, kaynak sıra kimliği, eksiklik dönüşümü,
grup paydaları ve ham dosyanın hash'i kontrol edilir. Temiz veri ayrı dosyadır.
Testler model başarısını değil veri işlemlerinin doğruluğunu sınar.""")
    code("""audit = export_results(raw, clean, tables, figures, metadata)
assert digest(raw_path.read_bytes()) == raw_hash_before
display(pd.Series(audit['checks']).to_frame('geçti'))
environment = {'python':platform.python_version(), 'packages':{
    name:version(name) for name in ['pandas','numpy','matplotlib','nbformat','nbclient','ipykernel']}}
(ROOT / 'reports' / 'environment.json').write_text(json.dumps(environment,indent=2),encoding='utf-8')
print('Temiz veri, tablo CSV dosyaları, grafikler ve bulgu raporu kaydedildi.')""")
    md("""## 8. Sonuçların sınırı ve öğrenme
- Tek bankanın tarihsel kampanya örneklemi güncel Türkiye müşteri kitlesi değildir.
- Örneklem seçimi, eksik bilgi ve müşteri kimliğinin olmaması yorumu sınırlar.
- Grup farkı ve korelasyon nedensellik değildir; güven aralığı veya p değeri üretmedik.
- Eksik bilgileri korumak bir analiz kararıdır; gelecekteki model için her durumda
  doğru doldurma yöntemi olduğunu iddia etmiyoruz.

**Kendine sor:** Negatif bakiye neden silinmedi? IQR=0 ne demek?
`pdays=-1` ile `education=unknown` neden aynı tür eksiklik değil?
Temas sayısı–abonelik farkı neden arama sayısı politikası önerisine yetmez?

Mülakat cevapları ve gerçek çıktılara dayanan CV açıklaması için
`docs/interview_and_cv.md`; kaynak ve lisans için `docs/sources_and_license.md`.
""")
    nb = nbf.v4.new_notebook(cells=cells, metadata={
        "kernelspec": {"name":"python3", "display_name":"Python 3", "language":"python"},
        "language_info": {"name":"python", "version":sys.version.split()[0]}
    })
    out = ROOT / "notebooks/01_bank_marketing_eda.ipynb"
    out.parent.mkdir(parents=True, exist_ok=True)
    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="eda-kernel-", dir=runtime) as tmp:
        spec_dir = Path(tmp) / "python3"
        spec_dir.mkdir()
        (spec_dir / "kernel.json").write_text(json.dumps({
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "EDA local Python", "language": "python"
        }), encoding="utf-8")
        km = KernelManager(kernel_name="python3", kernel_spec_manager=KernelSpecManager(kernel_dirs=[tmp]),
                           connection_file=str(Path(tmp)/"connection.json"))
        client = NotebookClient(nb, km=km, timeout=180, startup_timeout=60,
                                resources={"metadata":{"path":str(out.parent)}},
                                on_cell_start=lambda cell, cell_index: print(f"Hücre {cell_index+1}/{len(nb.cells)}", flush=True))
        try:
            client.execute()
        finally:
            if km.has_kernel:
                km.shutdown_kernel(now=True)
    nbf.validate(nb)
    errors = [output for cell in nb.cells if cell.cell_type == "code" for output in cell.outputs if output.output_type == "error"]
    assert not errors
    nbf.write(nb, out)
    print(f"Defter çalıştırıldı ve doğrulandı: {len(nb.cells)} hücre; hata çıktısı yok.")


if __name__ == "__main__":
    main()
