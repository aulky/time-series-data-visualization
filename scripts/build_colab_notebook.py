"""Generator for Colab-native submission notebook with pure point headings (no prose/discussion).

Produces: notebooks/metro_interstate_traffic_submission_colab.ipynb
- Contains only clean point headings: e.g. '# 1. Project Overview', '## 8. Line Plot', etc.
- No prose explanations, no interpretation paragraphs, no discussion text.
- Fully runnable native in Google Colab (with Open in Colab badge, automatic pip install & data download).
"""

from pathlib import Path
import re
import nbformat as nbf

SOURCE_NB = Path("notebooks/metro_interstate_traffic_analysis.ipynb")
TARGET_NB = Path("notebooks/metro_interstate_traffic_submission_colab.ipynb")

src = nbf.read(SOURCE_NB, as_version=4)

COLAB_HEADER = (
    '<a href="https://colab.research.google.com/github/aulky/time-series-data-visualization/blob/main/notebooks/metro_interstate_traffic_submission_colab.ipynb" target="_parent">\n'
    '  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>\n'
    '</a>\n\n'
    '# Time Series Analysis and Visualization of Metro Interstate Traffic Volume (2012–2018)\n\n'
    '---\n'
    '### Identitas Kelompok\n'
    '- **Nama Anggota / NIM**:\n'
    '  1. [Nama Lengkap] / [NIM]\n'
    '  2. [Nama Lengkap] / [NIM]\n'
    '  3. [Nama Lengkap] / [NIM]\n'
    '  4. [Nama Lengkap] / [NIM]\n'
    '- **Kelas**: [Kelas]\n'
    '- **Dataset**: Metro Interstate Traffic Volume (UCI Machine Learning Repository ID: 492)'
)

COLAB_SETUP_CODE = '''# 3. Setup & Library Imports (Kompatibel Google Colab & Lokal)
import os
import sys
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules

if IN_COLAB:
    print("[Colab] Menginstal dependensi...")
    !pip install -q ucimlrepo

    raw_dest = Path("data/raw/metro_interstate_traffic_volume.csv")
    if not raw_dest.exists():
        raw_dest.parent.mkdir(parents=True, exist_ok=True)
        import urllib.request
        url = "https://raw.githubusercontent.com/aulky/time-series-data-visualization/main/data/raw/metro_interstate_traffic_volume.csv"
        try:
            print("[Colab] Mengunduh raw dataset...")
            urllib.request.urlretrieve(url, raw_dest)
            print("[Colab] Dataset berhasil diunduh.")
        except Exception as e:
            print("[Colab] Fallback ke ucimlrepo...", e)
            from ucimlrepo import fetch_ucirepo
            import pandas as pd
            ds = fetch_ucirepo(id=492)
            pd.concat([ds.data.features, ds.data.targets], axis=1).to_csv(
                raw_dest, index=False, lineterminator="\\n"
            )
    ROOT = Path.cwd()
else:
    ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()

RAW_PATH = ROOT / "data" / "raw" / "metro_interstate_traffic_volume.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "metro_interstate_traffic_model.csv"
FIG_DIR = ROOT / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
'''

def extract_heading_only(text: str) -> str | None:
    """Extract ONLY clean point headings without prose or discussion."""
    stripped = text.strip()
    
    # AI Declaration template
    if "## 15. AI Usage Declaration" in text:
        return (
            "## 15. AI Usage Declaration\n\n"
            "> Saya menyatakan bahwa saya **menggunakan** alat AI generatif (Claude Code) "
            "sebagai asisten implementasi kode dan visualisasi. Seluruh hasil dan interpretasi diverifikasi sendiri.\n\n"
            "| No | Nama Tools AI | Bagian yang Dibantu | Bentuk Bantuan / Tujuan Prompt | Tingkat Ketergantungan |\n"
            "|---|---|---|---|---|\n"
            "| 1 | Claude Code | Pipeline data, EDA, 4 visualisasi wajib, Moving Average | Menghasilkan kode analisis dan visualisasi time series | Tinggi |\n"
        )
    
    # References point
    if "## 16. References" in text:
        return (
            "## 16. References\n\n"
            "1. UCI Machine Learning Repository: Metro Interstate Traffic Volume (ID: 492)\n"
            "2. Dokumentasi Python, pandas, numpy, matplotlib, seaborn, scipy"
        )

    # Filter out discussion paragraphs that don't start with '#'
    if not stripped.startswith("#"):
        return None

    # Get only the heading lines
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith("#")]
    
    # Filter out headings that are purely for narrative text (like '### 13.2 Lima insight utama' or '### Keterbatasan')
    clean_lines = []
    for l in lines:
        if any(skip in l for skip in ["Lima insight", "Keterbatasan", "Struktur Notebook", "Variabel", "Sumber dan Pengambilan"]):
            continue
        clean_lines.append(l)

    if clean_lines:
        return "\n\n".join(clean_lines)
    return None

new_cells = []

# 1. Header with Colab badge
new_cells.append(nbf.v4.new_markdown_cell(COLAB_HEADER))

# 2. Section 1 & 2 Point Headings
new_cells.append(nbf.v4.new_markdown_cell(
    "# 1. Project Overview\n\n"
    "## 2. Dataset Description & Source\n\n"
    "- **Sumber**: UCI Machine Learning Repository (ID: 492)\n"
    "- **URL**: https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume\n"
    "- **Variabel Utama**: `date_time`, `traffic_volume`"
))

# 3. Section 3 Setup code
new_cells.append(nbf.v4.new_code_cell(COLAB_SETUP_CODE))

seen_headings = set()

# Process rest of cells from source
for cell in src.cells:
    if cell.cell_type == "markdown":
        # Skip section 1 & 2 as they were added in clean point format above
        if any(h in cell.source for h in ["# 1. Project Overview", "## 2. Dataset Description", "## 3. Library Imports"]):
            continue
        heading = extract_heading_only(cell.source)
        if heading and heading not in seen_headings:
            seen_headings.add(heading)
            new_cells.append(nbf.v4.new_markdown_cell(heading))
    elif cell.cell_type == "code":
        code = cell.source
        # Replace duplicate setup definitions if any
        if "ROOT = Path.cwd().parent" in code:
            code = code.replace(
                'ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()\n'
                'RAW_PATH = ROOT / "data" / "raw" / "metro_interstate_traffic_volume.csv"\n'
                'PROCESSED_PATH = ROOT / "data" / "processed" / "metro_interstate_traffic_model.csv"\n'
                'FIG_DIR = ROOT / "reports" / "figures"\n'
                'FIG_DIR.mkdir(parents=True, exist_ok=True)\n',
                '# Konfigurasi path telah aktif pada sel setup\n'
            )
        new_cells.append(nbf.v4.new_code_cell(code))

colab_nb = nbf.v4.new_notebook(cells=new_cells)
colab_nb.metadata = src.metadata

nbf.write(colab_nb, TARGET_NB)
print(f"Generated {TARGET_NB} with {len(new_cells)} cells (pure point headings only).")
