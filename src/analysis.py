"""Yeniden çalıştırılabilir EDA; hiçbir gözlemi veya aykırı değeri otomatik silmez."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .download import ROOT, digest

NUMERIC = ["age", "balance", "day", "duration", "campaign", "pdays", "previous"]
MISSING = ["job", "education", "contact"]
CATEGORIES = {
    "job": ["admin.", "unknown", "unemployed", "management", "housemaid", "entrepreneur", "student", "blue-collar", "self-employed", "retired", "technician", "services"],
    "marital": ["married", "divorced", "single"],
    "education": ["unknown", "secondary", "primary", "tertiary"],
    "default": ["yes", "no"], "housing": ["yes", "no"], "loan": ["yes", "no"],
    "contact": ["unknown", "telephone", "cellular"],
    "month": ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
    "poutcome": ["unknown", "other", "failure", "success"], "y": ["yes", "no"]
}
EXPECTED = ["age", "job", "marital", "education", "default", "balance", "housing", "loan", "contact", "day", "month", "duration", "campaign", "pdays", "previous", "poutcome", "y"]
QUESTIONS = [
    "Eksik müşteri ve temas bilgileri hangi sütunlarda, hangi birlikte eksiklik örüntülerinde yoğunlaşıyor?",
    "Yıllık ortalama bakiye nasıl dağılıyor; IQR ile işaretlenen gözlemler ve negatif bakiyeler nasıl yorumlanmalı?",
    "Gözlenen vadeli mevduat abonelik oranları eğitim düzeyi ve kampanya temas sayısı gruplarında nasıl farklılaşıyor?"
]


def load_raw(path):
    return pd.read_csv(path, sep=";", dtype=str, keep_default_na=False)


def audit_raw(raw):
    return {
        "rows": int(len(raw)), "columns": int(raw.shape[1]),
        "blank_cells": int(raw.eq("").sum().sum()),
        "literal_null_cells": int(raw.isna().sum().sum()),
        "exact_duplicate_rows": int(raw.duplicated().sum()),
        "unknown_by_column": {c: int(raw[c].eq("unknown").sum()) for c in raw},
        "loaded_dtypes": {c: str(raw[c].dtype) for c in raw}
    }


def clean_data(raw):
    if list(raw.columns) != EXPECTED:
        raise ValueError("Beklenen bank-full.csv sütunları ve sırası bulunamadı.")
    if raw.empty:
        raise ValueError("Veri boş.")
    clean = raw.copy(deep=True)
    for col in NUMERIC:
        values = pd.to_numeric(clean[col], errors="raise")
        if values.isna().any() or not np.isfinite(values).all() or not values.eq(np.floor(values)).all():
            raise ValueError(f"{col}: sonlu, eksiksiz tamsayı gerekli.")
        clean[col] = values.astype("int64")
    valid = (clean.age.gt(0) & clean.day.between(1, 31) & clean.duration.ge(0)
             & clean.campaign.ge(1) & clean.pdays.ge(-1) & clean.previous.ge(0))
    if not valid.all():
        raise ValueError("Alan kuralını ihlal eden değer var; otomatik silme yapılmadı.")
    for col, allowed in CATEGORIES.items():
        unexpected = set(clean[col]) - set(allowed)
        if unexpected:
            raise ValueError(f"{col}: belgelenmemiş kategori {unexpected}")
        clean[col] = clean[col].astype("string")
    for col in MISSING:
        # Kaynaktaki gerçek unknown kodu; yapay eksiklik eklenmez.
        clean[col] = clean[col].mask(clean[col].eq("unknown"), pd.NA)
    clean.insert(0, "source_row", np.arange(1, len(clean) + 1))
    clean["subscribed"] = clean.y.eq("yes").astype("int64")
    clean["prior_contact"] = clean.pdays.ne(-1)
    clean["pdays_since_prior"] = clean.pdays.astype("Int64").mask(~clean.prior_contact)
    clean["prior_outcome"] = clean.poutcome.mask(clean.poutcome.eq("unknown"), pd.NA)
    clean["prior_outcome_missing_reason"] = np.select(
        [clean.poutcome.eq("unknown") & ~clean.prior_contact,
         clean.poutcome.eq("unknown") & clean.prior_contact],
        ["not_applicable_no_prior_contact", "unknown_despite_prior_contact"], default="observed")
    assert len(clean) == len(raw) and clean.source_row.is_unique
    return clean


def iqr_profile(clean):
    rows = []
    # pdays=-1 yapısal kod; yalnız geçerli önceki temas günleri için IQR hesapla.
    for col in ["age", "balance", "duration", "campaign", "previous", "pdays_since_prior"]:
        values = clean[col].dropna().astype(float)
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        flagged = (values.lt(low) | values.gt(high))
        rows.append({"variable": col, "observed_n": len(values), "q1": q1, "q3": q3,
                     "iqr": iqr, "lower_fence": low, "upper_fence": high,
                     "flagged_n": int(flagged.sum()), "flagged_pct": 100 * flagged.mean()})
    return pd.DataFrame(rows).set_index("variable")


def group_rates(clean, column):
    labels = clean[column].astype("string").fillna("Bilinmiyor")
    rates = clean.assign(group=labels).groupby("group", sort=True).subscribed.agg(n="size", yes_n="sum", rate="mean")
    rates["rate_pct"] = 100 * rates.rate
    return rates


def build_tables(raw, clean):
    missing = pd.DataFrame({"raw_unknown_n": [int(raw[c].eq("unknown").sum()) for c in MISSING],
                            "clean_missing_n": clean[MISSING].isna().sum()})
    missing["missing_pct"] = 100 * missing.clean_missing_n / len(clean)
    mask = clean[MISSING].isna()
    patterns = mask.apply(lambda row: " + ".join(row.index[row].tolist()) if row.any() else "Eksik yok", axis=1).value_counts().rename_axis("pattern").to_frame("n")
    patterns["pct"] = 100 * patterns.n / len(clean)
    selected = ["age", "balance", "duration", "campaign", "previous", "pdays_since_prior"]
    descriptive = clean[selected].describe(percentiles=[0.25, 0.5, 0.75, 0.95, 0.99]).T
    descriptive["missing_n"] = clean[selected].isna().sum()
    descriptive["unit"] = ["yıl", "EUR", "saniye", "temas sayısı", "temas sayısı", "gün"]
    categories = []
    for col in CATEGORIES:
        counts = clean[col].fillna("Bilinmiyor").value_counts(dropna=False)
        categories.extend({"variable": col, "category": str(k), "n": int(v), "pct": 100 * v / len(clean)} for k, v in counts.items())
    grouped = clean.copy()
    grouped["campaign_group"] = pd.cut(clean.campaign, bins=[0, 1, 2, 3, 4, 5, 10, np.inf], labels=["1", "2", "3", "4", "5", "6–10", "11+"])
    return {
        "missing_profile": missing,
        "missing_patterns": patterns,
        "descriptive_statistics": descriptive,
        "category_counts": pd.DataFrame(categories),
        "outlier_profile": iqr_profile(clean),
        "education_rates": group_rates(clean, "education"),
        "campaign_rates": group_rates(grouped, "campaign_group").reindex(["1", "2", "3", "4", "5", "6–10", "11+"]),
        # Seçilen sütunlar eksiksiz. Ortalama bağlı sıraların Pearson korelasyonu
        # Spearman katsayısını verir; ek scipy bağımlılığı gerekmez.
        "spearman": clean[["age", "balance", "duration", "campaign", "previous"]].rank(method="average").corr()
    }


def plot_all(clean, tables, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.dpi": 135,
                         "axes.spines.top": False, "axes.spines.right": False})
    specs = []
    def save(fig, filename, title, finding, limitation):
        fig.tight_layout()
        fig.savefig(folder / filename, bbox_inches="tight")
        plt.close(fig)
        specs.append({"filename": filename, "title": title, "finding": finding, "limitation": limitation})
    blue, orange = "#16758c", "#cc7542"
    missing = tables["missing_profile"].sort_values("missing_pct")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(missing.index, missing.missing_pct, color=blue)
    for i, (_, row) in enumerate(missing.iterrows()):
        ax.text(row.missing_pct + 0.3, i, f"%{row.missing_pct:.2f} (n={int(row.clean_missing_n):,})", va="center")
    ax.set(xlim=(0, max(missing.missing_pct.max() * 1.4, 1)), xlabel="Eksik bilgi oranı (%)", title="1 · Kaynakta unknown ile kodlanan eksik bilgiler")
    top = missing.iloc[-1]
    save(fig, "01_missing.png", "Eksik bilgi hangi alanlarda yoğunlaşıyor?",
         f"En yüksek eksik bilgi oranı {missing.index[-1]} alanında: %{top.missing_pct:.2f} (n={int(top.clean_missing_n):,}).",
         "UCI üst verisi boş/NA değer olmadığını bildirir; burada ölçülen, gerçek unknown kodlarının anlamsal eksikliğidir. Eksiklik mekanizması kanıtlanmaz.")
    patterns = tables["missing_patterns"]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ordered = patterns.sort_values("n")
    ax.barh(ordered.index, ordered.pct, color=blue)
    ax.set(xlabel="Tüm kayıtların oranı (%)", title="2 · Job, education ve contact birlikte eksiklik örüntüleri")
    for i, (_, row) in enumerate(ordered.iterrows()):
        ax.text(row.pct + 0.25, i, f"%{row.pct:.2f}", va="center", fontsize=9)
    ax.set_xlim(0, ordered.pct.max() * 1.15)
    complete = int(patterns.loc["Eksik yok", "n"]) if "Eksik yok" in patterns.index else 0
    save(fig, "02_missing_patterns.png", "Eksik bilgiler birlikte mi görülüyor?",
         f"Üç alanda da bilgi bulunan {complete:,} kayıt var; en az bir eksik alanı olan {len(clean)-complete:,} kayıt korunuyor.",
         "Örüntüler yalnız bu üç alanı kapsar; MCAR, MAR veya MNAR sınıflaması için tek başına yeterli değildir.")
    bal = clean.balance
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].hist(np.arcsinh(bal / 1000), bins=65, color=blue)
    axes[0].set(xlabel="asinh(bakiye / 1000 EUR)", ylabel="Kayıt sayısı", title="İşaret koruyan dönüşümle dağılım")
    axes[1].boxplot(bal, orientation="horizontal", flierprops={"markersize": 2, "alpha": 0.25})
    axes[1].set_xscale("symlog", linthresh=1000)
    axes[1].set_xticks([-1000, 0, 1000, 10000, 100000], ["−1.000", "0", "1.000", "10.000", "100.000"])
    axes[1].set(xlabel="Yıllık ortalama bakiye (EUR; symlog ölçek)", yticks=[], title="Ham değerlerden kutu grafiği")
    fig.suptitle("3 · Negatif ve yüksek bakiyeler silinmeden dağılım", y=1.04)
    out = tables["outlier_profile"].loc["balance"]
    save(fig, "03_balance_distribution.png", "Bakiye dağılımı ve aykırı gözlemler",
         f"Ortalama {bal.mean():.2f} EUR, medyan {bal.median():.2f} EUR; negatif bakiyeli {int(bal.lt(0).sum()):,} kayıt var. IQR kuralı {int(out.flagged_n):,} bakiyeyi işaretliyor (%{out.flagged_pct:.2f}).",
         "IQR etiketi veri hatası değildir; negatif bakiye de otomatik hata sayılmaz. asinh ve symlog yalnız görselleştirme içindir; temiz bakiye değerleri değiştirilmez.")
    edu = tables["education_rates"].sort_values("rate_pct")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.barh(edu.index, edu.rate_pct, color=blue)
    for i, (_, row) in enumerate(edu.iterrows()):
        ax.text(row.rate_pct + 0.15, i, f"%{row.rate_pct:.2f} | n={int(row.n):,}", va="center")
    ax.set(xlim=(0, edu.rate_pct.max() * 1.45), xlabel="Gözlenen abonelik oranı (%)", title="4 · Eğitim düzeyine göre vadeli mevduat aboneliği")
    save(fig, "04_education_subscription.png", "Eğitim gruplarında gözlenen oranlar nasıl?",
         f"En yüksek oran {edu.index[-1]} grubunda %{edu.rate_pct.iloc[-1]:.2f}; en düşük {edu.index[0]} grubunda %{edu.rate_pct.iloc[0]:.2f}. Paydalar grafikte gösteriliyor; eksik eğitim ayrı grupta tutuldu.",
         "Bunlar örneklem içi betimsel oranlardır; eğitim etkisi veya nedensel fark değildir. Yaş, gelir, seçim ve kampanya bileşimi kontrol edilmedi; güven aralığı veya hipotez testi yapılmadı.")
    rates = tables["campaign_rates"]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    bars = ax.bar(rates.index, rates.rate_pct, color=blue)
    for bar, (_, row) in zip(bars, rates.iterrows()):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.15, f"%{row.rate_pct:.2f}\nn={int(row.n):,}", ha="center", fontsize=9)
    ax.set(ylim=(0, rates.rate_pct.max()*1.3), xlabel="Mevcut kampanyadaki temas sayısı (son temas dahil)", ylabel="Gözlenen abonelik oranı (%)", title="5 · Temas sayısı grupları ve abonelik oranı")
    save(fig, "05_campaign_subscription.png", "Temas sayısı grupları nasıl farklılaşıyor?",
         f"Tek temas grubunda oran %{rates.loc['1', 'rate_pct']:.2f} (n={int(rates.loc['1','n']):,}); 11+ temas grubunda %{rates.loc['11+', 'rate_pct']:.2f} (n={int(rates.loc['11+','n']):,}).",
         "Temas sayısı rastgele atanmadı; zor ikna edilen kayıtlarda daha fazla temas olabilir. Bu sonuçtan arama sayısını azaltmanın aboneliği artıracağı çıkarılamaz.")
    fig, ax = plt.subplots(figsize=(9, 4))
    groups = [clean.loc[clean.y.eq(label), "balance"] for label in ["no", "yes"]]
    ax.boxplot(groups, tick_labels=[f"Hayır (n={len(groups[0]):,})", f"Evet (n={len(groups[1]):,})"], orientation="horizontal", flierprops={"markersize": 2, "alpha": 0.2})
    ax.set_xscale("symlog", linthresh=1000)
    ax.set_xticks([-1000, 0, 1000, 10000, 100000], ["−1.000", "0", "1.000", "10.000", "100.000"])
    ax.set(xlabel="Yıllık ortalama bakiye (EUR; symlog ölçek)", title="6 · Abonelik durumuna göre bakiye dağılımı")
    save(fig, "06_balance_by_subscription.png", "Abone olan ve olmayan kayıtlarda bakiye nasıl?",
         f"Medyan bakiye: abone olmayanlarda {groups[0].median():.2f} EUR; olanlarda {groups[1].median():.2f} EUR. Her iki grupta da uç değerler korundu.",
         "Gruplar eş büyüklükte değil; bakiye farkı aboneliğe neden olan bir etki veya müşteri geliri ölçümü değildir. Tek bir ortalama/medyan tüm dağılımı anlatmaz.")
    corr = tables["spearman"]
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(corr)), corr.columns, rotation=35, ha="right")
    ax.set_yticks(range(len(corr)), corr.index)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i,j]:.2f}", ha="center", va="center", color="white" if abs(corr.iloc[i,j])>.6 else "black")
    fig.colorbar(im, ax=ax, label="Spearman sıra korelasyonu")
    ax.set_title("7 · Seçili sayısal değişkenlerin ilişkileri")
    pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
    pair = pairs.abs().idxmax()
    save(fig, "07_spearman.png", "Sayısal değişkenler arasında sıralı ilişki var mı?",
         f"Gösterilen çiftlerde mutlak değeri en büyük Spearman katsayısı {pair[0]}–{pair[1]} için {pairs.loc[pair]:.3f}.",
         "Seçili ilişkiler betimseldir; sıfıra yakın katsayı tüm bağımlılıkları dışlamaz. pdays=-1 yapısal kodu korelasyona alınmadı. duration görüşme sonrası bilinir; önceden hedefleme özelliği gibi kullanılamaz.")
    return specs


def export_results(raw, clean, tables, figures, metadata):
    reports = ROOT / "reports"
    table_dir = reports / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / "data/processed").mkdir(exist_ok=True)
    clean.to_csv(ROOT / "data/processed/bank_clean.csv", index=False)
    for name, table in tables.items():
        table.to_csv(table_dir / f"{name}.csv", index=(name != "category_counts"))
    raw_audit = audit_raw(raw)
    before_after = pd.DataFrame([
        {"stage": "raw", "rows": len(raw), "columns": raw.shape[1], "deleted_rows": 0},
        {"stage": "clean", "rows": len(clean), "columns": clean.shape[1], "deleted_rows": 0}
    ])
    before_after.to_csv(table_dir / "before_after.csv", index=False)
    checks = {
        "same_row_count": len(raw) == len(clean),
        "balance_unchanged": bool(np.array_equal(pd.to_numeric(raw.balance).values, clean.balance.values)),
        "original_outcome_unchanged": raw.y.tolist() == clean.y.tolist(),
        "missing_codes_exactly_mapped": all(int(raw[c].eq('unknown').sum()) == int(clean[c].isna().sum()) for c in MISSING),
        "all_source_rows_unique_and_retained": clean.source_row.tolist() == list(range(1, len(raw)+1)),
        "pdays_sentinel_preserved": int(pd.to_numeric(raw.pdays).eq(-1).sum()) == int(clean.pdays.eq(-1).sum()),
        "structural_days_missing_correctly": clean.pdays_since_prior.isna().tolist() == (~clean.prior_contact).tolist(),
        "missing_pattern_counts_sum_to_rows": int(tables['missing_patterns'].n.sum()) == len(clean),
        "education_group_counts_sum_to_rows": int(tables['education_rates'].n.sum()) == len(clean),
        "campaign_group_counts_sum_to_rows": int(tables['campaign_rates'].n.sum()) == len(clean),
        "seven_figures": len(figures) == 7,
        "raw_hash_unchanged": digest((ROOT / 'data/raw/bank-full.csv').read_bytes()) == metadata['csv_sha256']
    }
    if not all(checks.values()):
        raise AssertionError(f"Başarısız bütünlük kontrolü: {checks}")
    audit = {"raw": raw_audit, "clean_rows": len(clean), "clean_columns": clean.shape[1],
             "negative_balance_rows": int(clean.balance.lt(0).sum()),
             "prior_contact_consistency_mismatches": int((clean.prior_contact != clean.previous.gt(0)).sum()),
             "prior_outcome_missing_reasons": {str(k): int(v) for k,v in clean.prior_outcome_missing_reason.value_counts().items()},
             "missing_any_of_three_rows": int(clean[MISSING].isna().any(axis=1).sum()),
             "overall_subscription_pct": 100*float(clean.subscribed.mean()), "checks": checks}
    (reports / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    (reports / "figure_notes.json").write_text(json.dumps(figures, ensure_ascii=False, indent=2), encoding="utf-8")
    text = ["# Bulgular ve Sınırlamalar", "", "## Araştırma soruları", ""]
    text += [f"{i}. {q}" for i,q in enumerate(QUESTIONS, 1)]
    text += ["", "## Veri ve temizleme", "",
             f"Ham ve temiz veri: {len(raw):,} kayıt. Satır silinmedi, değer doldurulmadı; ham dosya hash'i değişmedi.",
             f"Birebir aynı özellikli tekrar sayısı: {raw_audit['exact_duplicate_rows']}. Müşteri kimliği olmadığından tekrar olsaydı dahi otomatik silinmeyecekti.",
             f"Üç alandan en az biri eksik {audit['missing_any_of_three_rows']:,} kayıt var. Bu gözlemler tutuldu.",
             f"Önceki temas gün kodu ile previous>0 tutarsızlığı: {audit['prior_contact_consistency_mismatches']} kayıt.",
             f"Önceki sonuç durumu: {audit['prior_outcome_missing_reasons']}.",
             "UCI'nin 'eksik yok' açıklaması literal eksiklik içindir; unknown bilgi belirsizliğini ayrı analiz ettik.",
             "", "## Grafikler ve yorumlar", ""]
    for spec in figures:
        text += [f"### {spec['title']}", "", f"![{spec['title']}](figures/{spec['filename']})", "",
                 f"**Bulgu:** {spec['finding']}", "", f"**Sınırlama:** {spec['limitation']}", ""]
    text += ["## Temsil edilebilirlik", "",
             "Veri, Portekiz'de tek bir bankanın 2008–2010 dönemi telefon kampanyası kayıtlarıdır. Tüm banka müşterilerini, güncel Türkiye piyasasını veya rastgele bir nüfus örneklemini temsil ettiği varsayılmaz.",
             "Müşteri kimliği ve tam tarih yoktur. Satırların benzersiz müşteri olduğunu kanıtlayamayız; bağımsızlık varsayımıyla hipotez testi yapmadık.",
             "Abonelik oranları yalnız kayıtların gözlenen dağılımını tanımlar. Nedensellik, p değeri veya model başarısı iddiası yoktur.",
             "", "## Betimsel istatistikleri okuma", "",
             "Ortalama ve medyan bakiye farkı sağ kuyruğun etkisini gösterir; standart sapma uç değerlere duyarlıdır. Çeyrekler dağılımın orta bölümünü özetler.",
             "previous alanında IQR sıfır olabileceğinden, nadir fakat geçerli önceki temaslar da işaretlenebilir. Bu kural bir silme talimatı değildir.",
             "Ayrıntılı sayılar reports/tables CSV'lerinde; alan bazında kararlar docs/cleaning_decisions.md dosyasında."]
    (reports / "findings.md").write_text("\n".join(text), encoding="utf-8")
    return audit
