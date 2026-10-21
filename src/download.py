"""UCI anlık görüntüsünü edin; kaynak arşivini ve ham CSV'yi değiştirme."""
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
URL = "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip"


def digest(content):
    return hashlib.sha256(content).hexdigest()


def ensure_raw():
    folder = ROOT / "data/raw"
    folder.mkdir(parents=True, exist_ok=True)
    raw = folder / "bank-full.csv"
    archive = folder / "uci-bank-marketing.zip"
    metadata_path = ROOT / "data/source_metadata.json"
    if raw.exists():
        if not metadata_path.exists() or not archive.exists():
            raise ValueError("Anlık görüntünün kaynak kaydı/arşivi eksik; sessizce yeniden indirilmez.")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if digest(raw.read_bytes()) != metadata["csv_sha256"]:
            raise ValueError("Ham CSV değişmiş; SHA-256 uyuşmuyor.")
        if digest(archive.read_bytes()) != metadata["archive_sha256"]:
            raise ValueError("Kaynak arşivi değişmiş; SHA-256 uyuşmuyor.")
        return raw, metadata
    request = Request(URL, headers={"User-Agent": "bank-marketing-eda educational project"})
    with urlopen(request, timeout=60) as response:
        content = response.read()
    outer = ZipFile(io.BytesIO(content))
    if "bank.zip" in outer.namelist():
        bank = ZipFile(io.BytesIO(outer.read("bank.zip")))
    else:
        bank = outer
    # Yalnız bilinen dosyaları bellekte oku; arşiv yollarıyla extractall yapma.
    def member(name):
        matches = [n for n in bank.namelist() if n.split("/")[-1] == name]
        if len(matches) != 1:
            raise ValueError(f"Arşivde tek {name} bekleniyordu.")
        return bank.read(matches[0])
    csv = member("bank-full.csv")
    names = member("bank-names.txt")
    if not csv.startswith(b'"age";'):
        raise ValueError("Beklenmeyen UCI CSV şeması.")
    archive.write_bytes(content)
    raw.write_bytes(csv)
    (folder / "bank-names.txt").write_bytes(names)
    metadata = {
        "dataset": "Bank Marketing", "variant": "bank-full.csv (older version)",
        "source_page": "https://archive.ics.uci.edu/dataset/222/bank+marketing",
        "download_url": URL, "doi": "10.24432/C5K306", "license": "CC BY 4.0",
        "attribution": "Moro, S., Rita, P., & Cortez, P. (2014). Bank Marketing. UCI Machine Learning Repository.",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_sha256": digest(content), "csv_sha256": digest(csv),
        "notes": "Older bank-full variant with balance in EUR; no synthetic records or missingness added."
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return raw, metadata


if __name__ == "__main__":
    path, metadata = ensure_raw()
    print(f"Ham veri hazır: {path.name}; SHA-256: {metadata['csv_sha256']}")
