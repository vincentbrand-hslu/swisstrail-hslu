"""Optional one-time official dataset import running on Railway volume.

Enabled only with SWISSTRAIL_AUTO_IMPORT=1. It does not replace the service,
keeps downloaded source in a temporary folder, and atomically publishes trails.db.
"""
import logging
import os
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path

from trail_data import DEFAULT_TRAILS_DB

LOG = logging.getLogger("swisstrail.import")
OFFICIAL_SOURCE = (
    "https://data.geo.admin.ch/ch.swisstopo.swisstlm3d-wanderwege/"
    "swisstlm3d-wanderwege/swisstlm3d-wanderwege_2056_5728.gpkg.zip"
)
MAX_ARCHIVE_BYTES = 700 * 1024 * 1024
MAX_GPKG_BYTES = 2 * 1024 * 1024 * 1024

def import_official_dataset():
    from scripts.import_trails import import_data
    if DEFAULT_TRAILS_DB.is_file() and DEFAULT_TRAILS_DB.stat().st_size > 4096:
        LOG.info("Official trails are already installed: %s", DEFAULT_TRAILS_DB)
        return
    DEFAULT_TRAILS_DB.parent.mkdir(parents=True, exist_ok=True)
    # /tmp is ephemeral; do not download the uncompressed GPKG into the 500MB volume.
    with tempfile.TemporaryDirectory(prefix="swisstrail-import-") as tmp:
        tmpdir = Path(tmp)
        archive = tmpdir / "official.zip"
        request = urllib.request.Request(OFFICIAL_SOURCE,headers={
            "User-Agent": "SwissTrail-HSLU-Student-Project/3.0",
        })
        LOG.info("Downloading swisstopo data to temporary storage")
        total = 0
        with urllib.request.urlopen(request,timeout=90) as response, archive.open("wb") as dst:
            while chunk := response.read(1024*1024):
                total += len(chunk)
                if total > MAX_ARCHIVE_BYTES:
                    raise RuntimeError("Download exceeds 700MB safety limit")
                dst.write(chunk)
        with zipfile.ZipFile(archive) as z:
            files = [entry for entry in z.infolist()
                     if entry.filename.lower().endswith(".gpkg") and not entry.is_dir()]
            if len(files) != 1:
                raise RuntimeError("Expected one GeoPackage in official ZIP")
            entry = files[0]
            if entry.file_size > MAX_GPKG_BYTES:
                raise RuntimeError("GeoPackage exceeds 2GB safety limit")
            gpkg = tmpdir / "source.gpkg"
            LOG.info("Extracting GeoPackage (%s bytes)", entry.file_size)
            with z.open(entry) as src, gpkg.open("wb") as dst:
                copied = 0
                while chunk := src.read(1024*1024):
                    copied += len(chunk)
                    if copied > MAX_GPKG_BYTES:
                        raise RuntimeError("GeoPackage extraction exceeded limit")
                    dst.write(chunk)
        pending = DEFAULT_TRAILS_DB.with_suffix(".pending.db")
        try:
            pending.unlink(missing_ok=True)
            import_data(gpkg, pending)
            if pending.stat().st_size <= 4096:
                raise RuntimeError("Imported trails DB is empty")
            os.replace(pending, DEFAULT_TRAILS_DB)
            LOG.info("Official trails imported: %s", DEFAULT_TRAILS_DB)
        finally:
            pending.unlink(missing_ok=True)

def start_import_background():
    if os.getenv("SWISSTRAIL_AUTO_IMPORT") != "1":
        return
    def run():
        try:
            import_official_dataset()
        except Exception:
            LOG.exception("Official trail import failed; app remains usable")
    threading.Thread(target=run,daemon=True,name="swisstrail-import").start()
