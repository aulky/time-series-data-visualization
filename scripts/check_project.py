"""Acceptance checks for the final notebook / repository (run after a full Run All)."""

import hashlib
import pathlib
import re
import sys

import nbformat
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
NB = ROOT / "notebooks" / "metro_interstate_traffic_analysis.ipynb"
checks: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, bool(ok), detail))


nb = nbformat.read(NB, as_version=4)
cells = nb.cells
codes = [c for c in cells if c.cell_type == "code"]

# --- 1. execution
errs = [o for c in codes for o in c.outputs if o.output_type == "error"]
stderr = [o.text for c in codes for o in c.outputs if o.output_type == "stream" and o.name == "stderr"]
check("run all: no cell error", not errs, str([(e.ename, e.evalue[:60]) for e in errs])[:200])
check("run all: no stderr output", not stderr, str(stderr)[:200])
out_text = []
for c in codes:
    for o in c.outputs:
        if o.output_type == "stream":
            out_text.append(o.text)
        elif o.output_type in ("execute_result", "display_data") and "text/plain" in o.data:
            out_text.append(o.data["text/plain"])
blob = "\n".join(out_text)
src_blob = "\n".join(c.source for c in codes)
check("no absolute paths in code", not re.search(r"[A-Za-z]:\\\\|[A-Za-z]:/", src_blob))
check("no absolute paths in outputs", "D:\\\\" not in blob and "C:\\\\" not in blob)
check("relative paths used", "ROOT = Path.cwd()" in src_blob and 'RAW_PATH = ROOT / "data" / "raw"' in src_blob)

# --- 2. visualisation
required = {
    "01_line_plot.png": "line plot",
    "02_area_plot.png": "area plot",
    "03_multiple_time_series.png": "multiple time series",
    "04_seasonal_heatmap.png": "seasonal heatmap",
    "05_moving_average.png": "moving average",
}
for fname, label in required.items():
    p = ROOT / "reports" / "figures" / fname
    check(f"figure saved: {label}", p.exists() and p.stat().st_size > 10_000, fname)

mts = next(c.source for c in codes if "03_multiple_time_series.png" in c.source)
check("direct labeling on multi-series (no legend used for lines)", "ax.annotate(f\"Weekday" in mts and "ax.legend(" not in mts)
ma = next(c.source for c in codes if "05_moving_average.png" in c.source)
check("rolling window 7 & 30 with min_periods", "rolling(window=7, min_periods=7)" in src_blob
      and "rolling(window=30, min_periods=30)" in src_blob)
check("MA plot overlays raw + MA7 + MA30", all(k in ma for k in ["Daily average (raw)", "Moving average 7 days", "Moving average 30 days"]))

missing_interp = []
for i, c in enumerate(cells):   # i = notebook cell index
    if c.cell_type == "code" and any(o.output_type == "display_data" and "image/png" in o.data for o in c.outputs):
        nxt = next((cells[j] for j in range(i + 1, len(cells)) if cells[j].cell_type == "markdown"), None)
        if nxt is None or "Interpretasi" not in nxt.source:
            missing_interp.append(i)
check("every figure followed by an interpretation", not missing_interp, str(missing_interp))

# blank-canvas guard: every non-white pixel share must be visible
try:
    from matplotlib import image as mpimg
except Exception:
    mpimg = None
for fname, _ in required.items():
    pass
for png in sorted((ROOT / "reports" / "figures").glob("*.png")):
    if mpimg is not None:
        img = mpimg.imread(png)
        nonwhite = float((img[..., :3].min(axis=-1) < 0.95).mean())
        check(f"figure not blank: {png.name}", nonwhite > 0.01, f"non-white share {nonwhite:.4f}")

# --- 3. data
raw = ROOT / "data" / "raw" / "metro_interstate_traffic_volume.csv"
sha = hashlib.sha256(raw.read_bytes()).hexdigest()
check("raw untouched (sha256 == UCI snapshot written by download_data.py)",
      sha == "312cb379ec73b71dc4d95c136e542c753690e943f43b49044d4ed80640fa2d76", sha[:16])
raw_df = pd.read_csv(raw)
check("raw row count 48.204", len(raw_df) == 48204, str(len(raw_df)))
md = "\n".join(c.source for c in cells if c.cell_type == "markdown")
check("data source URL cited", "archive.ics.uci.edu/dataset/492" in md)
check("ucimlrepo id 492 cited", "fetch_ucirepo(id=492)" in md)

proc = pd.read_csv(ROOT / "data" / "processed" / "metro_interstate_traffic_model.csv", parse_dates=["date_time"])
check("processed: unique timestamps", not proc["date_time"].duplicated().any(), str(len(proc)))
check("processed: 40.575 rows", len(proc) == 40575, str(len(proc)))
check("processed: no fabricated hours (all timestamps exist in raw)",
      set(proc["date_time"]) <= set(pd.to_datetime(raw_df["date_time"], format="%Y-%m-%d %H:%M:%S")))
raww = pd.read_csv(raw).drop_duplicates("date_time")
check("processed: sum traffic_volume preserved",
      int(proc["traffic_volume"].sum()) == int(raww["traffic_volume"].sum()))
check("missing timestamps examined", "11,976" in blob or "11976" in blob)
check("daily aggregation splits complete vs partial days",
      "Complete day (24 h)" in src_blob and "Partial day" in src_blob)
check("no imputation (no fillna of volumes)",
      "traffic_volume" not in "".join(re.findall(r"fillna\([^)]*\)", src_blob)))

# --- 4. repository
for rel in ["data/raw", "data/processed", "notebooks/metro_interstate_traffic_analysis.ipynb",
            "reports/figures", "README.md", "requirements.txt", ".gitignore"]:
    check(f"exists: {rel}", (ROOT / rel).exists())
req = (ROOT / "requirements.txt").read_text()
check("requirements lists core libs", all(x in req for x in ["pandas", "numpy", "matplotlib", "seaborn", "ucimlrepo"]))
gi = (ROOT / ".gitignore").read_text()
check(".gitignore does not exclude data/reports", "data/" not in gi.splitlines() and "reports/" not in gi.splitlines())
readme = (ROOT / "README.md").read_text(encoding="utf-8")
for topic in ["Deskripsi Proyek", "Dataset dan Sumber", "Teknologi", "Instalasi", "Cara Menjalankan", "Struktur"]:
    check(f"README section: {topic}", topic in readme)

# --- 5. structure
order = ["Project Overview", "Dataset Description & Source", "Library Imports", "Data Loading",
         "Data Validation", "Data Preprocessing", "Exploratory Data Analysis", "Line Plot", "Area Plot",
         "Multiple Time Series", "Seasonal Heatmap", "Trend Analysis", "Key Findings & Insights",
         "Conclusion", "AI Usage Declaration", "References"]
heads = [l for c in cells if c.cell_type == "markdown" for l in c.source.splitlines() if re.match(r"^#{1,3} \d+\.", l) or l.startswith("# 1.")]
positions = []
for name in order:
    hits = [i for i, l in enumerate(heads) if name in l]
    positions.append(hits[0] if hits else -1)
check("16 sections present in required order", all(p >= 0 for p in positions) and positions == sorted(positions), str(list(zip(order, positions))))
ai = next(c.source for c in cells
          if c.cell_type == "markdown" and c.source.lstrip().startswith("## 15. AI Usage Declaration"))
check("AI declaration template has no fabricated identity",
      "[Nama Lengkap]" in ai and "[NIM]" in ai and "Tidak menggunakan AI" in ai)

failed = [c for c in checks if not c[1]]
for name, ok, detail in checks:
    print(("PASS " if ok else "FAIL ") + name + (f"  -> {detail}" if detail and not ok else ""))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
