"""Generate notebooks/metro_interstate_traffic_analysis.ipynb.

The notebook is authored as code here so it stays reproducible and reviewable.
Run `python scripts/build_notebook.py`, then execute with
`jupyter nbconvert --execute --inplace notebooks/metro_interstate_traffic_analysis.ipynb`.
"""

from pathlib import Path

import nbformat as nbf

OUT = Path("notebooks/metro_interstate_traffic_analysis.ipynb")

CELLS: list[tuple[str, str]] = [
    ("markdown", """# 1. Project Overview

**Judul:** Time Series Analysis and Visualization of Metro Interstate Traffic Volume (2012–2018).

**Topik.** Data deret waktu nyata beresolusi jam mengenai jumlah kendaraan per jam di Interstate 94 arah
barat (Minneapolis–St. Paul, Minnesota) selama Oktober 2012 – September 2018, beserta kondisi cuaca per jam.

**Mengapa topik ini dipilih.** Lalu lintas perkotaan adalah deret waktu yang menggabungkan beberapa siklus
sekaligus (jam, hari kerja vs akhir pekan, bulan) sehingga cocok untuk melatih pembacaan pola, kualitas
data, dan tren. Dataset ini juga memuat celah rekaman dan duplikasi nyata, sehingga keterampilan validasi
data dapat diuji, bukan hanya pembuatan grafik.

**Pertanyaan analisis.**

1. Bagaimana kondisi kualitas data (missing value, duplikasi, celah waktu) dan apa implikasinya pada agregasi?
2. Bagaimana pola volume kendaraan menurut jam, hari, dan bulan?
3. Seberapa berbeda weekday dan weekend, baik besaran maupun bentuk polanya?
4. Apakah ada tren naik/turun jangka panjang, dan bagaimana moving average 7 & 30 hari membantu membacanya?

**Lingkup.** Analisis eksploratif deskriptif, empat jenis visualisasi time series wajib, dan analisis tren
dengan moving average. Model prediktif, deployment, dan dashboard interaktif berada di luar lingkup.

## 2. Dataset Description & Source

**Nama dataset:** Metro Interstate Traffic Volume (UCI Machine Learning Repository).
**Sumber:** <https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume> (dataset ID 492).

| Atribut | Nilai |
|---|---|
| Lokasi | Interstate 94 arah barat, Minneapolis–St. Paul, Minnesota, USA |
| Granularitas waktu | per jam (`date_time`) |
| Rentang | 2012-10-02 09:00 – 2018-09-30 23:00 |
| Observasi | 48.204 baris × 9 kolom |
| Variabel utama | `date_time` (waktu), `traffic_volume` (kendaraan/jam) |
| Variabel pendukung | `holiday`, `temp`, `rain_1h`, `snow_1h`, `clouds_all`, `weather_main`, `weather_description` |

### Variabel

| Kolom | Tipe | Deskripsi |
|---|---|---|
| `holiday` | kategori | Nama hari libur AS; kosong pada baris biasa dan hanya terisi pada rekaman 00:00 hari libur |
| `temp` | numerik (K) | Suhu udara rata-rata per jam |
| `rain_1h` | numerik (mm) | Curah hujan 1 jam terakhir |
| `snow_1h` | numerik (mm) | Curah salju 1 jam terakhir |
| `clouds_all` | numerik (%) | Tutupan awan |
| `weather_main` | kategori | Kondisi cuaca utama |
| `weather_description` | kategori | Deskripsi cuaca rinci |
| `date_time` | datetime | Waktu observasi (resolusi jam) |
| `traffic_volume` | numerik (**target**) | Jumlah kendaraan per jam |

### Sumber dan Pengambilan Data

```python
from ucimlrepo import fetch_ucirepo
dataset = fetch_ucirepo(id=492)   # features (48.204 x 8) + targets (48.204 x 1)
```

Snapshot mentah disimpan **tanpa perubahan** di `data/raw/metro_interstate_traffic_volume.csv` oleh
`scripts/download_data.py`. Seluruh transformasi terjadi pada salinan di memori.

## Struktur Notebook

| § | Bagian |
|---|---|
| 1 | Project Overview |
| 2 | Dataset Description & Source |
| 3 | Library Imports |
| 4 | Data Loading |
| 5 | Data Validation |
| 6 | Data Preprocessing |
| 7 | Exploratory Data Analysis |
| 8 | Line Plot |
| 9 | Area Plot |
| 10 | Multiple Time Series |
| 11 | Seasonal Heatmap |
| 12 | Trend Analysis (Moving Average) |
| 13 | Key Findings & Insights |
| 14 | Conclusion |
| 15 | AI Usage Declaration |
| 16 | References |"""),
    ("markdown", """## 3. Library Imports

Semua pustaka yang dipakai diimpor sekali di sini; notebook dijalankan dari atas ke bawah (Run All) tanpa
variabel atau file dari sesi sebelumnya. `ROOT` dideteksi dari lokasi kerja sehingga path tetap **relatif**:
`Path.cwd().parent` bila kernel dibuka di dalam `notebooks/`, selain itu `Path.cwd()`."""),
    ("code", """import warnings
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import gaussian_kde

warnings.filterwarnings("ignore")

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 160,
    "savefig.bbox": "tight",
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
})

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
RAW_PATH = ROOT / "data" / "raw" / "metro_interstate_traffic_volume.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "metro_interstate_traffic_model.csv"
FIG_DIR = ROOT / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

print("pandas", pd.__version__, "| numpy", np.__version__, "| matplotlib", plt.matplotlib.__version__, "| seaborn", sns.__version__)"""),
    ("markdown", """## 4. Data Loading

`data/raw/` tidak pernah dimodifikasi selama analisis. Notebook bekerja pada salinan DataFrame di memori;
hanya `data/processed/` dan `reports/` yang ditulis.

Migrasi ke mesin lain cukup mengubah posisi root: semua path dibentuk **relatif** terhadap `ROOT`
(`Path.cwd()` / folder induk bila dijalankan dari `notebooks/`), tidak ada path absolut yang di-hardcode.
Sebelum dimuat, file mentah diperiksa hash SHA-256-nya agar dapat dibuktikan identik dengan hasil
`ucimlrepo.fetch_ucirepo(id=492)` yang ditulis `scripts/download_data.py`."""),
    ("code", """from hashlib import sha256

RAW_SHA256 = "312cb379ec73b71dc4d95c136e542c753690e943f43b49044d4ed80640fa2d76"
raw_bytes = RAW_PATH.read_bytes()
actual_sha = sha256(raw_bytes).hexdigest()

print("notebook root (relative to cwd):", ROOT.name, "| cwd:", Path.cwd().name)
print("raw file                 :", RAW_PATH.relative_to(ROOT))
print("sha256 actual            :", actual_sha)
print("sha256 expected          :", RAW_SHA256)
print("raw file unmodified      :", actual_sha == RAW_SHA256)
if actual_sha != RAW_SHA256:
    raise RuntimeError(
        "data/raw/metro_interstate_traffic_volume.csv does not match the expected UCI snapshot. "
        "Re-run `python scripts/download_data.py` before analysing."
    )

raw = pd.read_csv(RAW_PATH)
print("shape:", raw.shape)
raw.head()"""),
    ("code", """raw.tail(3)"""),
    ("markdown", """## 5. Data Validation

### 5.1 Dimensi, tipe data, missing value"""),
    ("code", """pd.DataFrame({
    "dtype": raw.dtypes.astype(str),
    "n_non_null": raw.notna().sum(),
    "n_missing": raw.isna().sum(),
    "pct_missing": (raw.isna().mean() * 100).round(3),
    "n_unique": raw.nunique(),
})"""),
    ("code", """raw.describe().T"""),
    ("markdown", """### 5.2 Konversi `date_time` dan urutan waktu"""),
    ("code", """df = raw.copy()
df["date_time"] = pd.to_datetime(df["date_time"], format="%Y-%m-%d %H:%M:%S")
print("dtype:", df["date_time"].dtype)
print("monotonic increasing:", df["date_time"].is_monotonic_increasing)"""),
    ("markdown", """### 5.3 Duplicate rows dan duplicate timestamps

`holiday` tepat pada 61 baris (= 53 tanggal libur) dan semuanya jam **00:00**, sementara cuaca dan volume
bervariasi sepanjang jam di tanggal yang sama. Artinya label libur adalah penanda tingkat-hari yang hanya
ditempelkan pada rekaman 00:00 — bukan bukti bahwa baris lain hari itu bukan libur."""),
    ("code", """print("fully duplicated rows (all 9 columns identical):", raw.duplicated().sum())
print("duplicated date_time values:", df["date_time"].duplicated().sum())
print("rows sharing a duplicated timestamp:", df["date_time"].duplicated(keep=False).sum())
print("holiday-labelled rows:", df["holiday"].notna().sum(),
      "| distinct dates:", df.loc[df["holiday"].notna(), "date_time"].dt.date.nunique())
print("hour-of-day of holiday-labelled rows:", df.loc[df["holiday"].notna(), "date_time"].dt.hour.unique())"""),
    ("markdown", """### 5.4 Timestamp ganda — periksa `traffic_volume` sebelum memutuskan

Timestamp ganda **tidak** dihapus secara membabi buta. Setiap grup dibandingkan dulu: bila
`traffic_volume` berbeda, penghapusan akan membuang informasi nyata dan harus direview manual."""),
    ("code", """dup = df[df["date_time"].duplicated(keep=False)].sort_values(["date_time", "traffic_volume"])
groups = dup.groupby("date_time")["traffic_volume"].agg(n="size", vmin="min", vmax="max")
groups["spread"] = groups["vmax"] - groups["vmin"]

print("rows involved           :", len(dup))
print("duplicated timestamps   :", len(groups))
print("groups of size >2       :", int((groups["n"] > 2).sum()))
print("groups with spread == 0 :", int((groups["spread"] == 0).sum()))
print("groups with CONFLICTING traffic_volume:", int((groups["spread"] > 0).sum()))
print("date range:", dup["date_time"].min(), "->", dup["date_time"].max())

support = ["holiday", "temp", "rain_1h", "snow_1h", "clouds_all", "weather_main", "weather_description"]
diff = dup.groupby("date_time")[support].nunique(dropna=False)
print("\\ngroups where every support column is identical:", int((diff.max(axis=1) == 1).sum()))
for col in ["temp", "rain_1h", "clouds_all", "weather_main", "weather_description", "holiday"]:
    print(f"  groups where {col:<20} differs:", int((diff[col] > 1).sum()))
num = dup.groupby("date_time")[["temp", "rain_1h", "snow_1h", "clouds_all"]]
print("max numeric spread inside a group:", (num.max() - num.min()).max().round(2).to_dict())
print("\\nhour-of-day distribution of duplicated timestamps:")
print(groups.index.hour.value_counts().sort_index().to_string())"""),
    ("markdown", """Kesimpulan: **`traffic_volume` identik pada seluruh 5.445 timestamp ganda** — tidak ada konflik penukaran
volume, sehingga duplikasi tidak mengubah target. Kolom pendukung tidak selalu identik, dan ini penting:

- 5.386 grup berbeda pada label cuaca yang sebagian besar sinonim (`Rain`/`light rain` vs
  `Drizzle`/`light intensity drizzle`) — dampak kecil.
- 79 grup berbeda pada suhu/awan, dengan selisih ekstrem 20,43 K (mis. 276,79 K vs 256,36 K pada jam yang
  sama). Ini **bukan noise**: satu jam yang sama muncul pada lebih dari satu berkas sumber cuaca, lalu
  digabungkan. Setelah `keep="first"` hanya satu pembacaan cuaca yang bertahan, sehingga kolom cuaca pada
  baris tersebut bersifat perkiraan.

`keep="first"` tetap aman untuk analisis volume karena target konsisten; analisis cuaca tingkat jam perlu
menyadari keterbatasan ini. Baris lengkap tersedia di `reports/duplicate_timestamp_review.csv`.

Bila suatu saat data sumber berubah dan ditemukan timestamps dengan volume berbeda, sel ini
menghasilkan selisih; proses di `scripts/preprocess.py` juga akan berhenti dengan error, bukan
menghapus data secara diam-diam."""),
    ("code", """dup.drop_duplicates().to_csv(ROOT / "reports" / "duplicate_timestamp_review.csv", index=False)
print("total residual duplicate rows after keep-first:", int(groups["n"].sub(1).sum()))"""),
    ("markdown", """### 5.8 Rentang tanggal, celah waktu, dan kelengkapan harian

#### Rentang tanggal"""),
    ("code", """print("min:", df["date_time"].min())
print("max:", df["date_time"].max())
print("span:", df["date_time"].max() - df["date_time"].min())
df.groupby(df["date_time"].dt.year).size().rename("rows").to_frame().assign(
    distinct_timestamps=df.drop_duplicates("date_time").groupby(
        df.drop_duplicates("date_time")["date_time"].dt.year).size())"""),
    ("markdown", """### 5.5 Timestamp gaps

Tidak ada NaN pada kolom nilai **tidak berarti** tidak ada jam yang hilang. Data dibandingkan terhadap
indeks jam lengkap 2012-10-02 09:00 – 2018-09-30 23:00 (52.543 jam)."""),
    ("code", """full_index = pd.date_range("2012-10-02 09:00", "2018-09-30 23:00", freq="h")
observed = pd.DatetimeIndex(df["date_time"].drop_duplicates().sort_values())
missing = full_index.difference(observed)

print(f"expected hours : {len(full_index):,}")
print(f"observed hours : {len(observed):,}")
print(f"missing hours  : {len(missing):,} ({len(missing)/len(full_index)*100:.2f}%)")

steps = pd.Series(observed).diff().dropna().dt.total_seconds() / 3600
print("\\nstep sizes between consecutive observations (hours -> count):")
print(steps.value_counts().sort_index().head(10))"""),
    ("code", """miss = pd.Series(1, index=missing)
blocks = (miss.index.to_series().diff() != pd.Timedelta(hours=1)).cumsum()
gaps = miss.groupby(blocks).agg(
    gap_start=lambda s: s.index[0],
    gap_end=lambda s: s.index[-1],
    n_missing_hours="size",
).sort_values("n_missing_hours", ascending=False)
gaps.to_csv(ROOT / "reports" / "timestamp_gaps.csv", index=False)

print("contiguous gaps:", len(gaps))
print("\\ntop 10 gaps:")
display(gaps.head(10).reset_index(drop=True))
print("\\ngap length distribution (hours -> #gaps):")
print(gaps["n_missing_hours"].value_counts().sort_index().to_string())
print("\\nshare of all missing hours inside the single largest gap:",
      f"{gaps['n_missing_hours'].iloc[0] / gaps['n_missing_hours'].sum() * 100:.1f}%")"""),
    ("markdown", """**Temuan utama:** celah terbesar adalah pemadaman rekaman selama **±10 bulan** (2014-08-08 → 2015-06-12,
7.386 jam). Ini bukan noise acak; analisis tren harus memperhitungkannya, dan bagian periode itu tidak boleh
diisi dengan interpolasi.

#### Kelengkapan observasi setiap hari

Hari lengkap = 24 observasi. Hari 2012-10-02 hanya berisi 15 jam karena dataset dimulai pukul 09:00."""),
    ("code", """dedup = df.drop_duplicates(subset="date_time", keep="first").copy()
daily = (dedup.assign(date=dedup["date_time"].dt.date)
              .groupby("date")
              .agg(n_obs=("date_time", "nunique"), mean_volume=("traffic_volume", "mean"))
              .reset_index())
daily["date"] = pd.to_datetime(daily["date"])
daily["is_boundary_day"] = daily["date"].isin(["2012-10-02", "2018-09-30"])
daily.to_csv(ROOT / "reports" / "daily_completeness.csv", index=False)

inner = daily.loc[~daily["is_boundary_day"]]
print("calendar days covered        :", len(daily))
print("complete 24h days            :", int((inner["n_obs"] == 24).sum()))
print("incomplete inner days        :", int((inner["n_obs"] < 24).sum()))
span_days = (daily["date"].max() - daily["date"].min()).days + 1
print("calendar days in span:", span_days, "| days present in index:", len(daily),
      "| days with zero recorded hours:", span_days - len(daily))
display(daily.loc[daily["is_boundary_day"]])
print("\\nobservation-count distribution:")
print(daily["n_obs"].value_counts().sort_index().to_string())"""),
    ("code", """fig, ax = plt.subplots(figsize=(13, 4))
ax.hist(daily["n_obs"], bins=np.arange(0.5, 25.5, 1), color="steelblue", edgecolor="white")
ax.set(title="Distribution of completed hourly observations per calendar day",
       xlabel="Hourly observations in the day", ylabel="Number of days")
ax.set_xticks(range(0, 25, 3))
plt.tight_layout()
plt.savefig(FIG_DIR / "10_validation_daily_completeness.png")
plt.show()"""),
    ("code", """fig, ax = plt.subplots(figsize=(14, 3.4))
ax.scatter(daily["date"], daily["n_obs"], s=5, alpha=0.45, color="crimson")
ax.set(title="Observation count per day (24 = complete day)", ylabel="Hours observed", ylim=(0, 26))
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
plt.tight_layout()
plt.show()"""),
    ("markdown", """**Interpretasi.** Histogram menunjukkan mayoritas hari berdata lengkap 24 jam (1.214 hari, nilai tertinggi di
sumbu-x), tetapi 646 hari berisi 1–23 jam dan tersebar di seluruh rentang jam (bukan hanya sedikit hari).
Grafik pencar harian memperlihatkan bahwa hari-hari setengah-penuh bukan satu blok berurutan: rekaman hilang
menyebar sepanjang 2012–2018 dan bertumpuk di celah besar 2014–2015. Konsekuensinya, rata-rata harian dan
total harian tidak boleh dibandingkan mentah-mentah antar tanggal tanpa membedakan hari lengkap dan parsial
(pembedaannya dilakukan di area plot, §9)."""),
    ("markdown", """### 5.9 Outlier `traffic_volume` dan nilai sentinel

#### Outlier `traffic_volume`

IQR diperiksa tetapi **tidak ada yang dihapus**: batas atas IQR berada di atas nilai maksimum observasi,
sehingga data tidak mengandung outlier IQR; bentuk distribusi kanan-condong berasal dari jam sibuk."""),
    ("code", """q1, q3 = dedup["traffic_volume"].quantile([0.25, 0.75])
iqr = q3 - q1
low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
flag = dedup["traffic_volume"].lt(low) | dedup["traffic_volume"].gt(high)
print(f"Q1={q1:.0f}  Q3={q3:.0f}  IQR={iqr:.0f}  fences=({low:.0f}, {high:.0f})")
print(f"IQR outliers: {flag.sum()} rows ({flag.mean()*100:.2f}%)")
print("observed max:", dedup["traffic_volume"].max())
dedup.nlargest(5, "traffic_volume")[["date_time", "traffic_volume", "weather_main"]]"""),
    ("code", """fig, ax = plt.subplots(figsize=(11, 3.6))
sns.boxplot(x=dedup["traffic_volume"], ax=ax, color="lightsteelblue", width=0.4)
ax.axvline(high, color="firebrick", ls="--", lw=1, label=f"upper fence {high:.0f} (above max)")
ax.set(title="traffic_volume distribution and IQR fence", xlabel="Vehicles per hour")
ax.legend()
plt.tight_layout()
plt.savefig(FIG_DIR / "09_validation_volume_boxplot.png")
plt.show()"""),
    ("markdown", """**Interpretasi.** Garis putus-putus menandai batas atas IQR (1,5 x IQR). Seluruh data berada di kiri batas
itu, sehingga tidak ada observasi yang dikategorikan outlier dan tidak ada baris yang dihapus karena outlier.
Ekor panjang ke kanan (sampai 7.280 kendaraan/jam) adalah jam sibuk, bukan kesalahan pencatatan; lima nilai
tertinggi dicetak pada sel sebelumnya dan semua jatuh pada jam sibuk pagi/sore hari kerja."""),

    ("markdown", """### 5.6 Volume nol

Volume 0 kendaraan/jam di jalan raya antarkota khas kegagalan alat pencatatan, bukan lalu lintas nyata.
Nilai dipertahankan, diberi flag."""),
    ("code", """zeros = dedup[dedup["traffic_volume"] == 0]
print(f"zero-volume rows: {len(zeros)}")
print(zeros[["date_time", "traffic_volume", "temp", "clouds_all", "weather_main"]].to_string(index=False))"""),
    ("markdown", """**Interpretasi.** Hanya ada dua rekaman bernilai 0 kendaraan/jam, keduanya pada 23 Juli 2016 (pukul 18:00
dan 23:00) ketika pembacaan cuaca tetap wajar (suhu di atas 20 C, ada curah hujan/haze). Volume 0 pada jalan
raya antarkota dengan kondisi normal lebih konsisten dengan sensor yang tidak mengirim data daripada jalan
yang benar-benar kosong — tetapi dataset tidak memuat log sensor, jadi interpretasi ini **dugaan**, bukan
bukti. Nilainya dipertahankan dan diberi flag `is_sensor_zero`; tidak diganti dengan nilai buatan."""),
    ("markdown", """### 5.7 Nilai fisik mustahil dan label tidak konsisten"""),
    ("code", """zero_k = dedup[dedup["temp"] <= 0]
rain_sentinel = dedup[dedup["rain_1h"] > 200]
case_variants = dedup.loc[dedup["weather_description"].ne(dedup["weather_description"].str.lower()),
                          "weather_description"].unique()

print("temp <= 0 K rows:", len(zero_k), "| dates:", sorted(zero_k["date_time"].dt.date.unique()))
print("rain_1h > 200 mm/h rows:", len(rain_sentinel))
display(rain_sentinel[["date_time", "rain_1h", "weather_main"]])
print("weather_description labels differing only by capitalisation:", case_variants)"""),
    ("markdown", """## 6. Data Preprocessing

| Langkah | Alasan |
|---|---|
| Hapus 7.629 baris timestamp duplikat (`keep="first"`) | `traffic_volume` identik di semua grup (bukti §3.4); label cuaca pada 5.386 grup hanya sinonim, 79 grup cuaca bentrok antar berkas sumber |
| `temp_c` (dan `temp_c_clean` = NaN pada nilai mustahil) | Interpretasi dalam °C; NaN eksplisit, bukan imputasi |
| Flag `is_temp_error`, `is_rain_error`, `is_sensor_zero` | Menandai rekaman tidak valid tanpa mengubah nilai |
| `weather_description` → huruf kecil | `SQUALLS`, `Sky is Clear` hanya variasi kapitalisasi |
| Fitur kalender + `is_holiday` + `holiday_date` | Label libur hanya menempel di jam 00:00 |
| `gap_hours` | Jarak jam sejak observasi sebelumnya (1 = kontigu) |
| **Tidak** ada imputasi jam hilang | Celah 22,79% tidak boleh diciptakan ulang dengan nilai buatan |
| **Tidak** ada penghapusan outlier | Tidak ada outlier IQR; puncak adalah fenomena nyata |

Langkah-langkah ini identik dengan `scripts/preprocess.py`."""),
    ("code", """proc = dedup.copy()
proc = proc.drop_duplicates(subset="date_time", keep="first")

proc["temp_c"] = proc["temp"] - 273.15
proc = proc.rename(columns={"temp": "temp_k"})
proc["is_temp_error"] = proc["temp_k"].le(0)
proc["is_rain_error"] = proc["rain_1h"].gt(200)
proc["temp_c_clean"] = proc["temp_c"].where(~proc["is_temp_error"])
proc["weather_description"] = proc["weather_description"].str.lower()

proc = proc.sort_values("date_time").reset_index(drop=True)
proc["holiday"] = proc["holiday"].astype(object).where(proc["holiday"].notna(), "None")
proc["date"] = proc["date_time"].dt.date
proc["hour"] = proc["date_time"].dt.hour
proc["day_of_week"] = proc["date_time"].dt.day_name()
proc["day_of_week_num"] = proc["date_time"].dt.day_of_week
proc["is_weekend"] = proc["day_of_week_num"] >= 5
proc["month"] = proc["date_time"].dt.month
proc["year"] = proc["date_time"].dt.year
proc["is_holiday"] = proc["holiday"].ne("None")
holiday_dates = set(proc.loc[proc["is_holiday"], "date"])
proc["holiday_date"] = proc["date"].where(proc["date"].isin(holiday_dates))
proc["is_sensor_zero"] = proc["traffic_volume"].eq(0)
proc["gap_hours"] = proc["date_time"].diff().dt.total_seconds().div(3600).fillna(0).astype(int)

print("shape:", proc.shape)
print("distribution of gap_hours >= 2 (hours missing before the row):")
print(proc.loc[proc["gap_hours"] >= 2, "gap_hours"].describe().round(2))
proc.head()"""),
    ("markdown", """### 6.1 Simpan / verifikasi dataset processed"""),
    ("code", """if PROCESSED_PATH.exists():
    existing = pd.read_csv(PROCESSED_PATH, parse_dates=["date_time"])
    assert list(existing.columns) == list(proc.columns), "column set differs from preprocessing script"
    same = True
    def as_text(s):
        # pandas' nullable "str" dtype reports NaN as the literal string "None"; treat both as <NA>
        return s.astype(object).map(lambda v: None if pd.isna(v) or v == "None" else str(v))

    for col in proc.columns:
        left = proc[col].reset_index(drop=True)
        right = existing[col]
        if pd.api.types.is_numeric_dtype(left) and pd.api.types.is_numeric_dtype(right):
            same &= bool(np.allclose(left, right, equal_nan=True))
        else:
            same &= as_text(left).equals(as_text(right))
    print("rows x cols:", proc.shape, "| processed file identical to notebook pipeline:", same)
else:
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)   # works on a clean checkout
    proc.to_csv(PROCESSED_PATH, index=False)
    print("wrote", PROCESSED_PATH.relative_to(ROOT), proc.shape)"""),
]
CELLS = CELLS + [
    ("markdown", """## 7. Exploratory Data Analysis

Fitur turunan waktu (`hour`, `day_of_week`, `day_of_week_num`, `is_weekend`, `month`, `year`, `week`) dibuat
dari `date_time` pada **salinan** data (`proc`); `data/raw/` tidak pernah diubah. Ringkasan ringkas di bawah
ini menjadi dasar pembacaan keempat visualisasi wajib pada §8–§11.

### 7.1 Statistik deskriptif `traffic_volume`"""),
    ("code", """tv = proc["traffic_volume"]
desc = tv.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).round(1)
desc["skewness"] = round(tv.skew(), 2)
desc["kurtosis"] = round(tv.kurt(), 2)
desc["n_zero_hours"] = int(tv.eq(0).sum())
desc.to_frame("traffic_volume (vehicles/hour)")"""),
    ("markdown", """### 7.2 Distribusi volume kendaraan

**Variabel:** `traffic_volume` per jam (semua observasi, n = 40.575). Histogram + KDE (kiri) dan ECDF
(kanan) — ECDF dipakai karena lebih jujur untuk kemampuan baca sumbu-Y."""),
    ("code", """fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))

sns.histplot(tv, bins=60, stat="density", color="steelblue", ax=axes[0])
kde_x = np.linspace(tv.min(), tv.max(), 400)
kde = gaussian_kde(tv, bw_method=0.05)
axes[0].plot(kde_x, kde(kde_x), color="navy", lw=1.2)
axes[0].axvline(tv.median(), color="firebrick", ls="--", lw=1,
                label=f"median {tv.median():,.0f}")
axes[0].axvline(tv.mean(), color="darkorange", ls="--", lw=1,
                label=f"mean {tv.mean():,.0f}")
axes[0].set(title="Distribution of hourly traffic volume", xlabel="Vehicles per hour",
            ylabel="Density")
axes[0].legend()

sorted_tv = np.sort(tv.values)
ecdf = np.arange(1, len(sorted_tv) + 1) / len(sorted_tv)
axes[1].plot(sorted_tv, ecdf, color="navy", lw=1.6)
for q in (0.25, 0.5, 0.75):
    value = tv.quantile(q)
    axes[1].plot([value, value], [0, q], color="gray", ls=":", lw=0.9)
    axes[1].plot([0, value], [q, q], color="gray", ls=":", lw=0.9)
    axes[1].annotate(f"Q{int(q*100)} = {value:,.0f}", xy=(value, q), xytext=(value + 120, q - 0.08),
                     fontsize=9, color="dimgray")
axes[1].set(title="Cumulative distribution (ECDF)", xlabel="Vehicles per hour",
            ylabel="Share of observations ≤ x", ylim=(0, 1.02))

plt.tight_layout()
plt.savefig(FIG_DIR / "06_eda_distribution.png")   # save before show(), otherwise the canvas is already blank
plt.show()

print(f"share of hours below 1,000 vehicles/h : {tv.lt(1000).mean()*100:.1f}%")
print(f"share of hours above 5,000 vehicles/h : {tv.gt(5000).mean()*100:.1f}%")"""),
    ("markdown", """**Interpretasi.** Distribusi **bimodal**: satu mode di sekitar 300–1.500 kendaraan/jam (malam dan dini
hari) dan satu mode di sekitar 4.500–6.000 kendaraan/jam (jam sibuk). Median (3.427) sedikit di atas mean
(3.291) dan skewness −0,11 (praktis simetris), tetapi kurtosis −1,30 (lebih datar dari distribusi normal) —
kedua angka itu adalah tanda distribusi dua puncak. Bentuk ini bukan derau: yang menentukan adalah jam.
Sekitar 22% jam berada di bawah 1.000 kendaraan/jam, dan 24% di atas 5.000. Dua observasi bernilai
0 kendaraan (1 jam = 0,005% data) adalah rekaman sensor mati yang sudah ditandai `is_sensor_zero`, bukan lalu lintas
nyata; jumlahnya terlalu kecil untuk menggeser bentuk distribusi."""),

    ("markdown", """### 7.3 Rata-rata volume berdasarkan jam

**Variabel:** `hour` (0–23) × `traffic_volume`. Garis = rata-rata, pita = ±1 SD."""),
    ("code", """hourly_mean = proc.groupby("hour")["traffic_volume"].agg(mean="mean", sd="std", n="size")
print("lowest hours :", hourly_mean["mean"].nsmallest(3).round(0).to_dict())
print("highest hours:", hourly_mean["mean"].nlargest(3).round(0).to_dict())
for label, mask in [("weekday", ~proc["is_weekend"]), ("weekend", proc["is_weekend"])]:
    peaks = proc.loc[mask].groupby("hour")["traffic_volume"].mean().nlargest(4).round(0)
    print(f"{label} peak hours: {peaks.to_dict()}")

fig, ax = plt.subplots(figsize=(11, 4.4))
ax.plot(hourly_mean.index, hourly_mean["mean"], marker="o", ms=4, lw=2, color="navy")
ax.fill_between(hourly_mean.index, hourly_mean["mean"] - hourly_mean["sd"],
                hourly_mean["mean"] + hourly_mean["sd"], color="navy", alpha=0.12, label="±1 SD")
for h in hourly_mean["mean"].nlargest(3).index:
    ax.annotate(f"{h:02d}:00\\n{hourly_mean['mean'][h]:,.0f}", xy=(h, hourly_mean["mean"][h]),
                xytext=(h, hourly_mean["mean"][h] + 700), ha="center", fontsize=8.5, color="navy")
ax.set(title="Average traffic volume by hour of day — all days",
       xlabel="Hour of day", ylabel="Mean vehicles per hour", xticks=range(24))
ax.legend(loc="upper left")
plt.tight_layout()
plt.show()"""),
    ("markdown", """**Interpretasi.** Minimum ada di 03:00 (373), maksimum di 16:00 (5.709), lalu 17:00 (5.351) dan 15:00
(5.272), dengan 07:00 (4.770) sebagai puncak pagi — kurva U terbalik dengan dua puncak. Puncak pagi terlihat
lebih rendah daripada puncak sore karena di agregat semua hari rata-rata akhir pekan ikut bercampur; bila
dipisah per jenis hari (di bawah), puncak pagi hari kerja 07:00 mencapai 6.061 kendaraan/jam, hampir setara
puncak sore 16:00 (6.241). Bila dibatasi weekday saja, urutan puncaknya 16:00 > 07:00 > 17:00 > 15:00;
akhir pekan memuncak siang: 13:00 (4.408), 12:00 (4.403), 14:00 (4.393)."""),

    ("markdown", """### 7.4 Rata-rata volume berdasarkan hari"""),
    ("code", """week_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
daily_dim = (proc.groupby("day_of_week")["traffic_volume"]
             .agg(mean="mean", median="median", n="size").reindex(week_order))
daily_dim.round(0)"""),
    ("code", """fig, ax = plt.subplots(figsize=(11, 4.2))
sns.boxplot(data=proc, x="day_of_week", y="traffic_volume", order=week_order,
            color="lightsteelblue", width=0.55, showfliers=False, ax=ax)
ax.plot(range(7), daily_dim["mean"], marker="D", ms=6, color="firebrick", lw=1.2, label="Mean")
ax.set(title="Hourly traffic volume distribution by day of week",
       xlabel="", ylabel="Vehicles per hour", ylim=(0, 7300))
ax.legend(loc="upper right")
plt.tight_layout()
plt.show()"""),
    ("markdown", """**Interpretasi.** Rata-rata per hari berbentuk "bukit" Senin→Jumat lalu turun tajam pada Sabtu–Minggu:
Jumat tertinggi (3.675), Minggu terendah (2.426). Kotak hari kerja lebih tinggi dan lebih panjang ke atas
karena puncak jam sibuk, sedangkan akhir pekan lebih pendek. Pola Senin unik: rata-rata Senin (3.314) dan
median (3.615) adalah yang **terendah** di antara hari kerja — Senin punya lebih banyak jam bernilai rendah
(nilai Q3 tidak ditampilkan, tetapi terlihat dari kotak Senin yang lebih pendek ke atas)."""),

    ("markdown", """### 7.5 Weekday dibandingkan weekend

**Definisi:** `is_weekend = day_of_week_num >= 5` (Sabtu–Minggu); sisanya hari kerja (Senin–Jumat)."""),
    ("code", """wd = proc.loc[~proc["is_weekend"], "traffic_volume"]
we = proc.loc[proc["is_weekend"], "traffic_volume"]
cmp_ = pd.DataFrame({
    "n_hours": [len(wd), len(we)],
    "mean": [wd.mean(), we.mean()],
    "median": [wd.median(), we.median()],
    "% hours < 1,000": [wd.lt(1000).mean() * 100, we.lt(1000).mean() * 100],
}, index=["Weekday (Mon–Fri)", "Weekend (Sat–Sun)"]).round(1)
print(f"mean difference: {wd.mean() - we.mean():,.0f} vehicles/h "
      f"({(wd.mean() / we.mean() - 1) * 100:.0f}% higher on weekdays)")
cmp_"""),
    ("code", """fig, ax = plt.subplots(figsize=(11, 4.4))
for label, series, color in [("Weekday (Mon–Fri)", wd, "navy"), ("Weekend (Sat–Sun)", we, "darkorange")]:
    sns.histplot(series, bins=60, stat="density", element="step", fill=False, lw=1.8,
                 color=color, label=label, ax=ax)
ax.axvline(wd.mean(), color="navy", ls="--", lw=1)
ax.axvline(we.mean(), color="darkorange", ls="--", lw=1)
ax.annotate(f"weekday mean {wd.mean():,.0f}", xy=(wd.mean(), ax.get_ylim()[1] * 0.99),
            xytext=(wd.mean() - 1600, ax.get_ylim()[1] * 0.94), fontsize=9, color="navy")
ax.annotate(f"weekend mean {we.mean():,.0f}", xy=(we.mean(), ax.get_ylim()[1] * 0.86),
            xytext=(we.mean() - 150, ax.get_ylim()[1] * 0.80), fontsize=9, color="darkorange")
ax.set(title="Weekday vs weekend: distribution of hourly traffic volume",
       xlabel="Vehicles per hour", ylabel="Density")
ax.legend(loc="upper left")
plt.tight_layout()
plt.savefig(FIG_DIR / "07_eda_weekday_vs_weekend.png")
plt.show()"""),
    ("markdown", """**Interpretasi.** Weekday rata-rata 3.557 kendaraan/jam vs weekend 2.624 — selisih **934 kendaraan/jam
(+36%)**. Median berbeda lebih jauh (4.159 vs 2.771), artinya pada jam "tipikal" jarak weekday–weekend
bahkan lebih besar daripada rata-ratanya. Anehnya, persentase jam bernilai < 1.000 hampir sama (21,7% hari kerja vs
23,7% akhir pekan): yang hilang pada akhir pekan bukan jam malam, melainkan **jam sibuk** — weekend tidak punya puncak
pagi/sore yang menarik distribusinya ke 5.000+."""),

    ("markdown", """### 7.6 Rata-rata volume berdasarkan bulan"""),
    ("code", """month_mean = proc.groupby("month")["traffic_volume"].agg(mean="mean", n="size")
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
month_mean.index = month_names
print(month_mean["mean"].round(0).to_dict())

fig, ax = plt.subplots(figsize=(11, 4.2))
bars = ax.bar(month_mean.index, month_mean["mean"], color=sns.color_palette("crest", 12))
ax.bar_label(bars, labels=[f"{v:,.0f}" for v in month_mean["mean"]], fontsize=8.5, padding=2)
ax.set(title="Average traffic volume by month", xlabel="Month", ylabel="Mean vehicles per hour",
       ylim=(0, month_mean["mean"].max() * 1.12))
plt.tight_layout()
plt.show()"""),
    ("markdown", """**Interpretasi.** Bulan terendah Desember (3.040) dan Januari (3.060); tertinggi Agustus (3.430).
Rentang antar-bulan hanya ±6%, jauh lebih kecil dari rentang antar-jam (§7.3, nilai dicetak di atas) atau
weekday/weekend (+36%). Ini petunjuk bahwa **jam dan jenis hari lebih menentukan** daripada bulan. Pola bulanan
tidak monoton: Juli (3.238) justru lebih rendah dari Juni (3.422) dan Agustus (3.430); sebagian selisih ini
bisa berasal dari tidak seimbangnya jumlah observasi per bulan (rekaman 2014–2015 hilang)."""),

    ("markdown", """### 7.7 Pemeriksaan kelengkapan data temporal

Sebelum agregasi harian/mingguan di §8–§12, kelengkapan diuji lagi pada tingkat yang akan dipakai:
jam yang hilang, hari dengan < 24 jam, dan hari tanpa catatan sama sekali. `gap` menunjuk celah terpanjang
(hasil §4.2) yang akan ditandai pada setiap grafik berikutnya."""),
    ("code", """gap = gaps.iloc[0]
print("largest gap:", gap["gap_start"], "->", gap["gap_end"], f"({gap['n_missing_hours']:,} hours)")"""),
    ("code", """completeness = pd.DataFrame({
    "calendar days in span": [ (full_index[-1].normalize() - full_index[0].normalize()).days + 1 ],
    "days with any record": [proc["date"].nunique()],
    "days with 0 records": [int(((full_index[-1].normalize() - full_index[0].normalize()).days + 1)
                               - proc["date"].nunique())],
    "days with 24 records": [int((daily["n_obs"] == 24).sum())],
    "days with 1–23 records": [int(((daily["n_obs"] >= 1) & (daily["n_obs"] < 24)).sum())],
    "expected hours": [len(full_index)],
    "observed hours": [len(proc)],
    "missing hours": [len(missing)],
}, index=["value"]).T
completeness["share_of_expected"] = (completeness["value"] / len(full_index)).round(3)
completeness"""),
    ("code", """fig, ax = plt.subplots(figsize=(14, 3.6))
daily_plot = daily.copy()
daily_plot.loc[daily_plot["is_boundary_day"], "n_obs"] = daily_plot.loc[daily_plot["is_boundary_day"], "n_obs"]
ax.plot(daily_plot["date"], daily_plot["n_obs"], color="crimson", lw=0.9)
ax.axhline(24, color="navy", ls="--", lw=1, label="24 hours = complete day")
ax.axvspan(gap["gap_start"], gap["gap_end"], color="firebrick", alpha=0.10)
ax.annotate("no records\\n(308 days)", xy=(pd.Timestamp(gap["gap_start"].normalize()), 5),
            xytext=(pd.Timestamp(gap["gap_start"].normalize()), 8), ha="center", fontsize=8.5,
            color="firebrick")
ax.set(title="Temporal completeness: hourly observations per calendar day",
       xlabel="", ylabel="Hours recorded", ylim=(0, 26))
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.legend(loc="lower left")
plt.tight_layout()
plt.savefig(FIG_DIR / "08_eda_temporal_completeness.png")
plt.show()"""),
    ("markdown", """**Interpretasi — implikasi untuk bagian visualisasi.** Dari 52.551 jam yang seharusnya ada, hanya 40.575 tercatat (77,2%);
hanya 1.214 dari 1.860 hari berdata (65,3%; 34,7% hari parsial) yang lengkap 24 jam, dan 330 hari tidak punya catatan sama sekali
(2014-08-08 → 2015-06-11, 308 hari di antaranya). Hari parsial tersebar merata: 35,3% hari kerja dan 33,3%
hari akhir pekan tidak lengkap — jadi kelengkapan **tidak** condong ke salah satu kelompok, tetapi tetap
memengaruhi besaran rata-rata. Karena itu:

- **Line plot (§8)** tidak menggambar garis rata-rata harian melintasi celah dan menandai pemadaman.
- **Area plot (§9)** wajib memisahkan hari lengkap dan hari parsial — total hari parsial tidak sebanding.
- **Multiple time series (§10)** memakai hanya minggu yang lengkap (120 jam weekday / 48 jam weekend).
- **Heatmap (§11)** aman karena rata-rata per (hari, jam) hanya butuh satu sel, tetapi jumlah observasi per
  sel tetap dilaporkan."""),

    ("markdown", """## 8. Line Plot — Daily Average Traffic Volume 2012–2018

**Variabel:** `date` (x) dan rata-rata `traffic_volume` per tanggal (y). Deret dibuat pada indeks kalender
harian **tanpa imputasi**: tanggal tanpa catatan bernilai `NaN`, dan matplotlib memutus garis di titik itu.

**Periode yang digambar: 2013-01-01 – 2018-09-30.** Alasan: Kuartal IV 2012 (2.103 baris) a) dimulai
pertengahan hari dan banyak harinya parsial sehingga rata-rata hariannya berfluktuasi kuat, dan b) 4.809 dari
5.445 timestamp ganda berasal dari periode 2012, jadi bagian itu paling rapuh. Seluruh dataset tetap
dianalisis dan dilaporkan; hanya jendela gambar yang dipersempit dan hal itu ditulis pada judul grafik."""),
    ("code", """daily_avg = (proc.set_index("date_time")["traffic_volume"]
             .resample("D").mean())            # missing days -> NaN (no interpolation, no fillna)
plot_start, plot_end = pd.Timestamp("2013-01-01"), pd.Timestamp("2018-09-30")
line_data = daily_avg.loc[plot_start:plot_end]
print(f"line window: {plot_start.date()} .. {plot_end.date()} | "
      f"{line_data.notna().sum()} days with data / {len(line_data)} days")
print(f"daily average: min {line_data.min():,.0f}, median {line_data.median():,.0f}, "
      f"max {line_data.max():,.0f}")

fig, ax = plt.subplots(figsize=(14, 4.8))
ax.plot(line_data.index, line_data.values, color="#1f5c8b", lw=0.9, label="Daily average")
ax.axhline(line_data.mean(), color="dimgray", ls=":", lw=1,
           label=f"mean of plotted days {line_data.mean():,.0f}")
ax.axvspan(gap["gap_start"], gap["gap_end"], color="firebrick", alpha=0.10)
ax.annotate("no records\\n2014-08-08 → 2015-06-11\\n(7,386 h)", xy=(pd.Timestamp(gap["gap_start"]), 6800),
            xytext=(pd.Timestamp(gap["gap_start"]), 6950), color="firebrick", fontsize=8.5, ha="center")
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator())
ax.set(title="Daily Average Traffic Volume on I-94 (Minneapolis–St. Paul), Jan 2013 – Sep 2018",
       xlabel="Date", ylabel="Average traffic volume (vehicles/hour)", ylim=(0, 7300))
ax.grid(axis="x", which="minor", alpha=0.15)
ax.legend(loc="lower left")
plt.tight_layout()
plt.savefig(FIG_DIR / "01_line_plot.png")
plt.show()"""),
    ("markdown", """**Interpretasi.** Garis menunjukkan osilasi mingguan yang rapat (hari kerja tinggi, akhir pekan rendah)
dengan **amplitudo yang stabil** di seluruh tahun tanpa tren naik/turun yang meyakinkan: rata-rata seluruh
hari dalam jendela tahun 2013–2018 adalah 3.284 kendaraan/jam (median 3.483, rentang 277–5.263;
nilai dicetak di atas). Oscilasi
tajamnya adalah siklus mingguan (weekday tinggi, weekend rendah), bukan tren. Pemutusan garis selama ±10
bulan (area merah) sengaja tidak disambung: tanpa perlakuan ini kurva harian akan menghubungkan 2014 ke
2015 dan menipu pembaca. Turunnya nilai di sekitar Desember–Januari terlihat pada setiap tahun, tetapi
amplitudo per hari sangat bervariasi sehingga tren musiman halus tidak boleh dibaca dari garis ini — lihat
§12."""),
    ("markdown", """## 9. Area Plot — Daily Traffic Volume (total per tanggal)

**Variabel:** `date` (x) dan **jumlah** `traffic_volume` seluruh observasi pada tanggal itu (y).

**Kelengkapan diperiksa lebih dulu:** hanya hari dengan 24 observasi yang totalnya utuh. Hari parsial
digambar sebagai pita terpisah yang lebih rendah/putus dengan catatan; nilai aslinya tetap ditampilkan
(sehingga pembaca bisa melihat magnitudo kekurangannya)."""),
    ("code", """daily_total = (proc.groupby("date")["traffic_volume"]
               .agg(["sum", "size"]).rename(columns={"sum": "total", "size": "n_obs"}).reset_index())
daily_total["date"] = pd.to_datetime(daily_total["date"])
daily_total["complete"] = daily_total["n_obs"].eq(24)
full_days_total = daily_total.loc[daily_total["complete"]]
partial_days_total = daily_total.loc[~daily_total["complete"]]

print(f"complete days (24 h)          : {len(full_days_total)}")
print(f"partial days (<24 h)          : {len(partial_days_total)}")
print(f"total on complete days        : min {full_days_total['total'].min():,}, "
      f"median {full_days_total['total'].median():,.0f}, max {full_days_total['total'].max():,} "
      f"({full_days_total.loc[full_days_total['total'].idxmax(), 'date'].date()})")
print(f"median total, partial days    : {partial_days_total['total'].median():,.0f} "
      f"({partial_days_total['total'].median() / full_days_total['total'].median() * 100:.0f}% of a complete day)")"""),
    ("code", """fig, ax = plt.subplots(figsize=(14, 4.8))

full_plot = full_days_total.set_index("date")["total"].reindex(
    pd.date_range(plot_start, plot_end, freq="D"))
partial_plot = partial_days_total.set_index("date")["total"].reindex(
    pd.date_range(plot_start, plot_end, freq="D"))

ax.fill_between(full_plot.index, full_plot.values, color="#2f7d5d", alpha=0.75,
                linewidth=0, label="Complete day (24 h) — sum of 24 hours")
ax.fill_between(partial_plot.index, partial_plot.values, color="#d9822b", alpha=0.75,
                linewidth=0, label="Partial day (<24 h) — total undercounts the real day")

ax.axvspan(gap["gap_start"], gap["gap_end"], color="firebrick", alpha=0.10)
ax.annotate("no records\\n(308 days)", xy=(pd.Timestamp(gap["gap_start"].normalize()), 90000),
            xytext=(pd.Timestamp(gap["gap_start"].normalize()), 92000), color="firebrick", fontsize=8.5,
            ha="center")
ax.set(title="Daily Traffic Volume on I-94 — total vehicles per day, 2013–2018",
       xlabel="Date", ylabel="Vehicles per day (sum of recorded hours)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v/1000:,.0f}k"))
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator())
ax.set_ylim(0, 105000)
ax.grid(axis="x", which="minor", alpha=0.15)
ax.legend(loc="upper right", fontsize=8.5)
plt.tight_layout()
plt.savefig(FIG_DIR / "02_area_plot.png")
plt.show()"""),
    ("markdown", """**Catatan kelengkapan (wajib dibaca bersama grafik).** Warna oranye adalah hari dengan kurang dari 24 jam
tercatat, tingginya **bukan** volume harian sebenarnya, melainkan penjumlahan jam yang ada saja (median
58.317 vs 84.068 pada hari lengkap, yaitu 69%). Karena 34,7% hari berdata adalah hari parsial, lembah
oranye tersebar di sepanjang periode. Puncak normal hari lengkap adalah 97.332 kendaraan pada 31 Agustus
2017; hari parsial terendah hanya 434 kendaraan karena berisi satu jam. Karena itu total harian tidak
boleh dipakai mentah-mentah sebagai deret harian; hanya hari lengkap yang dianalisis.

**Interpretasi.** Dibandingkan line plot (rata-rata), area plot menonjolkan **akumulasi**: pada hari kerja
lengkap totalnya puluhan ribu kendaraan dengan puncak 97.332, dan pada akhir pekan turun jelas. Pola
mingguan memang berulang sangat teratur; yang tidak teratur justru **rekaman datanya** — hilangnya satu
hari (atau sebagian hari) tampak sebagai lembah tajam, bukan sebagai perubahan lalu lintas. Karena itu
grafik ini dipakai sebagai kontrol kualitas visual: pita oranye adalah peringatan bahwa agregasi harian
tidak boleh dibandingkan mentah-mentah antar tanggal."""),

    ("markdown", """## 10. Multiple Time Series — Weekday vs Weekend (rata-rata per minggu pengamatan)

**Variabel:** sumbu x = awal minggu pengamatan (Senin, periode ISO W-SUN); dua garis = rata-rata
`traffic_volume` per jam untuk semua rekaman weekday dalam minggu itu dan semua rekaman weekend dalam
minggu itu.

**Kontrol kelengkapan:** sebuah minggu hanya ditampilkan jika kelompoknya lengkap — 120 jam (5 hari × 24)
untuk weekday dan 48 jam (2 hari × 24) untuk weekend. Alasannya: tanpa filter, minggu yang hanya berisi
2 jam malam akan tampak "turun" padahal yang kurang adalah datanya.

**Direct labeling:** label "Weekday" dan "Weekend" ditulis di ujung garis; posisi vertikalnya dipisah dan
dicek jaraknya agar tidak bertabrakan."""),
    ("code", """week = proc.assign(week=proc["date_time"].dt.to_period("W-SUN").dt.start_time)
weekly = (week.groupby(["week", "is_weekend"])["traffic_volume"]
          .agg(mean="mean", n_hours="size")
          .reset_index())
required = {False: 120, True: 48}
weekly["expected"] = weekly["is_weekend"].map(required)
weekly["complete"] = weekly["n_hours"].eq(weekly["expected"])
print(f"weeks total            : {weekly['week'].nunique()}")
print(f"weekday weeks complete : {weekly.loc[~weekly['is_weekend'], 'complete'].sum():,} / "
      f"{(~weekly['is_weekend']).sum():,}")
print(f"weekend weeks complete : {weekly.loc[weekly['is_weekend'], 'complete'].sum():,} / "
      f"{weekly['is_weekend'].sum():,}")
print(f"complete weeks with BOTH groups complete: {weekly[weekly['complete']].groupby('week').size().eq(2).sum():,}")"""),
    ("code", """wd_week = (weekly.loc[(~weekly["is_weekend"]) & weekly["complete"]]
           .set_index("week")["mean"].sort_index())
we_week = (weekly.loc[(weekly["is_weekend"]) & weekly["complete"]]
           .set_index("week")["mean"].sort_index())
wd_week = wd_week.loc[wd_week.index >= plot_start]
we_week = we_week.loc[we_week.index >= plot_start]
MAX_WEEK_GAP = pd.Timedelta(weeks=3)   # a longer run of incomplete weeks is shown as a break, not a line

print(f"weekday weekly mean: {wd_week.mean():,.0f} (min {wd_week.min():,.0f}, max {wd_week.max():,.0f}), "
      f"{len(wd_week)} weeks")
print(f"weekend weekly mean: {we_week.mean():,.0f} (min {we_week.min():,.0f}, max {we_week.max():,.0f}), "
      f"{len(we_week)} weeks")

def segmented(series):
    # split where consecutive complete weeks are further apart than MAX_WEEK_GAP
    breaks = series.index.to_series().diff().gt(MAX_WEEK_GAP).cumsum()
    return [seg for _, seg in series.groupby(breaks.values)]

weekday_segments, weekend_segments = segmented(wd_week), segmented(we_week)
print("line segments — weekday:", len(weekday_segments), "| weekend:", len(weekend_segments))

fig, ax = plt.subplots(figsize=(14, 5.0))
for seg in weekday_segments:
    ax.plot(seg.index, seg.values, color="#1f5c8b", lw=1.3, marker="o", ms=2.6)
for seg in weekend_segments:
    ax.plot(seg.index, seg.values, color="#c0502d", lw=1.3, marker="o", ms=2.6)
ax.plot([], [], color="#1f5c8b", lw=1.3, marker="o", ms=2.6, label="Weekday")
ax.plot([], [], color="#c0502d", lw=1.3, marker="o", ms=2.6, label="Weekend")
ax.axvspan(gap["gap_start"], gap["gap_end"], color="firebrick", alpha=0.10)

# direct labels at the right end of each line, vertically separated
end_x = max(wd_week.index[-1], we_week.index[-1])
end_wd, end_we = wd_week.iloc[-1], we_week.iloc[-1]
ax.scatter([end_x], [end_wd], s=45, color="#1f5c8b", zorder=5, clip_on=False)
ax.scatter([end_x], [end_we], s=45, color="#c0502d", zorder=5, clip_on=False)
ax.annotate(f"Weekday\\n{end_wd:,.0f} veh/h", xy=(end_x, end_wd),
            xytext=(end_x + pd.Timedelta(days=70), end_wd + 320), color="#1f5c8b",
            fontsize=10.5, fontweight="bold", ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color="#1f5c8b", lw=0.8))
ax.annotate(f"Weekend\\n{end_we:,.0f} veh/h", xy=(end_x, end_we),
            xytext=(end_x + pd.Timedelta(days=70), end_we - 320), color="#c0502d",
            fontsize=10.5, fontweight="bold", ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color="#c0502d", lw=0.8))
print(f"vertical gap between labels: {abs((end_wd + 320) - (end_we - 320)):,.0f} vehicles/h")

ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator())
ax.set_xlim(plot_start, end_x + pd.Timedelta(days=430))
ax.set(title="Weekly mean traffic volume: Weekday vs Weekend (complete weeks only, 2013–2018)",
       xlabel="Week (Monday that starts the ISO week)", ylabel="Mean vehicles per hour in the week")
ax.grid(axis="x", which="minor", alpha=0.15)
plt.tight_layout()
plt.savefig(FIG_DIR / "03_multiple_time_series.png")
plt.show()"""),
    ("markdown", """**Interpretasi.** Rata-rata mingguan 3.559 (weekday) vs 2.636 (weekend) kendaraan/jam; rentang weekend jauh
lebih lebar (603–3.221) karena minggu libur besar sangat sepi. Kedua garis **bergerak searah**:
minggu yang ramai untuk commuter juga relatif ramai untuk lalu lintas akhir pekan — mengarah pada faktor
bersama seperti musim/cuaca. Jarak antar garis relatif stabil, artinya keunggulan weekday bersifat
struktural (perjalanan kerja), bukan kejadian sesaat. Keterputusan garis, termasuk 2014–2015 dan 2016, adalah
konsekuensi filter kelengkapan: minggu itu memang tidak punya cukup observasi, bukan lalu lintas yang turun
ke nol. Weekday lolos filter hanya pada 111 dari 269 minggu karena hampir 35% hari kerja parsial."""),

    ("markdown", """## 11. Seasonal Heatmap — hari × jam

**Variabel:** baris = hari dalam seminggu (Senin→Minggu), kolom = jam (00–23), nilai = rata-rata
`traffic_volume`. Hari dan jam diurutkan kronologis; `imshow` dipakai agar sumbu-x dan sumbu-y berurutan
alami, dengan colorbar eksplisit.

**Kelengkapan per sel:** jumlah observasi per (hari, jam) diperiksa dan dilaporkan, agar sel yang hanya
berisi beberapa rekaman tidak dibaca sebagai pola kuat."""),
    ("code", """heat = (proc.pivot_table(index="day_of_week", columns="hour", values="traffic_volume",
                       aggfunc="mean").reindex(week_order))
heat_n = (proc.pivot_table(index="day_of_week", columns="hour", values="traffic_volume",
                           aggfunc="size").reindex(week_order))
print(f"cells: {heat.size} | min observations per cell: {heat_n.min().min()} "
      f"(at {heat_n.stack().idxmin()}) | max: {heat_n.max().max()}")
print(f"value range: {heat.min().min():,.0f} .. {heat.max().max():,.0f}")
print("busiest cell :", f"{heat.stack().idxmax()[0]} {heat.stack().idxmax()[1]:02d}:00 -> "
      f"{heat.stack().max():,.0f}")
print("quietest cell:", f"{heat.stack().idxmin()[0]} {heat.stack().idxmin()[1]:02d}:00 -> "
      f"{heat.stack().min():,.0f}")"""),
    ("code", """fig, ax = plt.subplots(figsize=(15, 5.4))
im = ax.imshow(heat.values, aspect="auto", cmap="YlGnBu", vmin=0)
ax.set_xticks(range(24), [f"{h:02d}" for h in range(24)])
ax.set_yticks(range(7), week_order)
ax.set_xticks(np.arange(-0.5, 24, 1), minor=True)
ax.set_yticks(np.arange(-0.5, 7, 1), minor=True)
ax.grid(which="minor", color="white", lw=1.2)
ax.tick_params(which="minor", length=0)
ax.set_xlabel("Hour of day")
ax.set_ylabel("Day of week")
for (r, c), value in np.ndenumerate(heat.values):
    ax.text(c, r, f"{value/1000:.1f}" if value >= 1000 else f"{value:.0f}",
            ha="center", va="center", fontsize=8.5,
            color="white" if value > 4200 else "black")
ax.axhline(3.5, color="black", lw=1.4, ls="--")   # separates Fri (row 4) and Sat (row 5)
ax.text(23.9, 3.5, "weekend area ▼", ha="right", va="bottom", fontsize=8.5, color="black")
cbar = fig.colorbar(im, ax=ax, pad=0.012)
cbar.set_label("Mean traffic volume (vehicles/hour)")
cbar.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v/1000:,.0f}k" if v >= 1000 else f"{v:.0f}"))
ax.set_title("Seasonal / weekly heatmap: mean traffic volume by day of week and hour")
plt.tight_layout()
plt.savefig(FIG_DIR / "04_seasonal_heatmap.png")
plt.show()

day_core = heat.loc[week_order[:5]].mean()
print("weekday mean by hour, peak:", day_core.nlargest(3).round(0).to_dict())
print("weekday mean by hour, trough:", day_core.nsmallest(2).round(0).to_dict())
weekend_midday = heat.loc[["Saturday", "Sunday"], 12:16].values.mean()
weekday_midday = heat.loc[week_order[:5], 12:16].values.mean()
print(f"12:00-15:00 mean — weekend {weekend_midday:,.0f} vs weekday {weekday_midday:,.0f} "
      f"({weekend_midday / weekday_midday - 1:+.1%})")
print("weekend maximum cell:", f"{heat.loc[['Saturday','Sunday']].stack().idxmax()[0]} "
      f"{heat.loc[['Saturday','Sunday']].stack().idxmax()[1]:02d}:00 -> "
      f"{heat.loc[['Saturday','Sunday']].stack().max():,.0f}")
print("weekend 06:00-09:00 vs weekday 06:00-09:00:",
      round(heat.loc[["Saturday", "Sunday"], 6:10].values.mean(), 0), "vs",
      round(heat.loc[week_order[:5], 6:10].values.mean(), 0))"""),
    ("markdown", """**Interpretasi.** Heatmap memperlihatkan dua pola yang tidak terlihat pada grafik agregat:

1. **Dua puncak commuter hari kerja**: sel terpadat **Rabu 16:00**, diikuti sel 16:00–17:00 pada hari kerja
   lain. Rata-rata jam (Senin–Jumat): 16:00 > 07:00 > 17:00 — urutan dan nilainya dicetak di atas.
2. **Baris Sabtu–Minggu** (dipisah garis putus-putus) kehilangan puncak pagi: jam 06:00–09:00 akhir pekan
   jauh lebih rendah daripada hari kerja (angka tepat dicetak di atas), sedangkan pita siang 12:00–15:00
   menjadi bagian terpadat akhir pekan dan hanya ~18% lebih rendah daripada siang hari kerja.
3. **Malam dan dini hari** (00:00–03:00) paling pucat di semua hari; sel paling sunyi adalah **Selasa
   02:00 (277)**.
4. Setiap sel berisi ≥ 227 observasi (maksimum 256), jadi pola adalah fenomena nyata, bukan efek sel kosong."""),

    ("markdown", """## 12. Trend Analysis (Moving Average)

Metode: **moving average (MA)** pada *Daily Average Traffic Volume*. Definisi yang dipakai:

- `daily_avg` = rata-rata `traffic_volume` per tanggal, menggunakan indeks kalender harian
  (`resample("D")`). Tanggal tanpa satu pun rekaman menjadi `NaN` — **tidak diisi** dengan nilai buatan.
- `rolling(window, min_periods=window).mean()` pada **indeks kalender itu**, sehingga urutan tanggal
  dijamin kronologis (indeks sudah diurutkan dan unik).
- `min_periods = window`: nilai hanya dihitung bila ada tepat `window` observasi berurutan di dalam jendela.
  Akibatnya nilai awal periode adalah `NaN` sampai data cukup, dan jendela yang menyentuh hari hilang juga
  `NaN` (rata-rata tidak pernah memotong celah data).

Visualisasi wajib menampilkan **data asli** (`daily_avg`) dengan overlay **MA 7 hari** dan **MA 30 hari**."""),
    ("code", """daily = daily_avg.loc[plot_start:plot_end]            # tanggal berurutan, satu baris per hari
ma7 = daily.rolling(window=7, min_periods=7).mean()   # SMA 7 hari (siklus mingguan)
ma30 = daily.rolling(window=30, min_periods=30).mean() # SMA 30 hari (siklus bulanan kasar)

print(f"indeks harian          : {daily.index[0].date()} ... {daily.index[-1].date()} "
      f"({len(daily):,} baris, monoton naik: {daily.index.is_monotonic_increasing})")
print(f"hari dengan data       : {daily.notna().sum():,} | hari tanpa data (NaN, tidak diisi): {daily.isna().sum():,}")
print(f"titik valid MA7        : {ma7.notna().sum():,} | MA30: {ma30.notna().sum():,}")
print(f"NaN di awal periode    : MA7 {int(ma7.isna().iloc[:7].sum())} dari 7 | "
      f"MA30 {int(ma30.isna().iloc[:30].sum())} dari 30")
print(f"NaN lain (menyentuh hari kosong): MA7 {int(ma7.isna().sum()) - int(ma7.isna().iloc[:7].sum())}, "
      f"MA30 {int(ma30.isna().sum()) - int(ma30.isna().iloc[:30].sum())}")
print(f"standar deviasi harian : data asli {daily.std():,.0f} | MA7 {ma7.std():,.0f} | MA30 {ma30.std():,.0f}")
print(f"rentang harian         : data asli {daily.max() - daily.min():,.0f} | "
      f"MA7 {ma7.max() - ma7.min():,.0f} | MA30 {ma30.max() - ma30.min():,.0f}")

segment_id = (daily.notna() != daily.notna().shift()).cumsum()
longest_start, longest_end = daily.loc[segment_id == segment_id.mode().iloc[0]].index[[0, -1]]
print(f"segmen kontinu terpanjang: {longest_start.date()} ... {longest_end.date()}")"""),
    ("code", """fig, ax = plt.subplots(figsize=(14, 5.0))
ax.plot(daily.index, daily.values, color="lightsteelblue", lw=0.7, alpha=0.9, label="Daily average (raw)")
ax.plot(ma7.index, ma7.values, color="darkorange", lw=1.3, label="Moving average 7 days")
ax.plot(ma30.index, ma30.values, color="firebrick", lw=2.0, label="Moving average 30 days")
ax.axvspan(gap["gap_start"], gap["gap_end"], color="firebrick", alpha=0.10)
ax.annotate("no records: MA is undefined across the gap", xy=(pd.Timestamp(gap["gap_start"]), 7100),
            xytext=(pd.Timestamp(gap["gap_start"]), 7220), ha="center", fontsize=8.5, color="firebrick")
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.xaxis.set_minor_locator(mdates.MonthLocator())
ax.set(title="Daily Average Traffic Volume with 7-day and 30-day Moving Averages (2013-2018)",
       xlabel="Date", ylabel="Average traffic volume (vehicles/hour)", ylim=(0, 7500))
ax.grid(axis="x", which="minor", alpha=0.15)
ax.legend(loc="lower left", ncol=3, fontsize=8.5, framealpha=0.95)
plt.tight_layout()
plt.savefig(FIG_DIR / "05_moving_average.png")
plt.show()

print("saved:", (FIG_DIR / "05_moving_average.png").relative_to(ROOT))"""),
    ("code", """# Zoom on the longest continuous segment: does the 30-day window lose detail or react late?
zoom = daily.loc[longest_start:longest_end]
zoom_ma7 = ma7.loc[longest_start:longest_end]
zoom_ma30 = ma30.loc[longest_start:longest_end]

fig, ax = plt.subplots(figsize=(14, 4.4))
ax.plot(zoom.index, zoom.values, color="lightsteelblue", lw=1.1, label="Daily average (raw)")
ax.plot(zoom_ma7.index, zoom_ma7.values, color="darkorange", lw=1.6, label="MA 7 days")
ax.plot(zoom_ma30.index, zoom_ma30.values, color="firebrick", lw=2.2, label="MA 30 days")
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.set(title=f"Zoom: {longest_start.strftime('%b %Y')} - {longest_end.strftime('%b %Y')} "
             f"(longest continuous segment, {len(zoom):,} days)",
       xlabel="Date", ylabel="Average traffic volume (vehicles/hour)")
ax.legend(loc="lower left", ncol=3, fontsize=8.5)
plt.tight_layout()
plt.show()

# Local lag of each MA behind the raw series inside the segment
for name, series in [("MA7", zoom_ma7), ("MA30", zoom_ma30)]:
    best_lag, best_corr = None, -2
    for lag in range(0, 31):
        corr = series.corr(zoom.shift(lag))
        if corr > best_corr:
            best_lag, best_corr = lag, corr
    print(f"{name}: lag dengan korelasi tertinggi terhadap data asli = {best_lag} hari (r = {best_corr:.3f})")"""),
    ("markdown", """**Interpretasi.**

- **Perbedaan MA 7 dan MA 30.** MA 7 merata-ratakan tepat satu minggu (satu siklus mingguan penuh), sehingga pola harian di dalam minggu hilang tetapi riak dari minggu ke minggu tetap hidup (MA7
  masih naik-turun terlihat, standar deviasi 230 vs 604 pada data asli). MA 30 merata-ratakan sekitar satu
  bulan, sehingga riak mingguan ikut tergerus dan hanya perubahan lambat yang tersisa (standar deviasi 167;
  hanya 28% variasi harian tersisa).
- **Pengaruh ukuran window terhadap kehalusan.** Semakin besar window, semakin kecil amplitudo sisa:
  rentang (max − min) turun dari 4.986 (data asli) menjadi 1.650 (MA7) dan 843 (MA30) — nilai dicetak di sel kode. Kurva MA30 hampir
  horizontal di segmen kontinu, menandakan komponen tren jangka panjang memang sangat lemah.
- **Mengapa window lebih besar lebih halus?** Rata-rata adalah filter low-pass: titik hasil adalah
  penjumlahan `window` nilai dibagi `window`. Naik-turun harian di dalam jendela saling meniadakan
  (positif dan negatif saling menutup), dan pengaruh satu observasi ekstrem turun menjadi `1/window`
  (1/7 untuk MA7, 1/30 untuk MA30). Semakin panjang jendela, semakin banyak osilasi pendek yang masuk
  jendela dan saling menghapus.
- **Mengapa ada NaN di awal periode?** Karena `min_periods = window`, jendela 7 hari pertama MA7 berisi
  1-6 observasi (kurang dari 7) dan jendela 30 hari pertama MA30 berisi 1-29 observasi. Hasil cetakan:
  "NaN di awal periode: MA7 6 dari 7 | MA30 29 dari 30" -- satu nilai awal yang tersisa adalah hari
  pertama yang jendelanya sudah penuh. Ini bukan error, melainkan penanda bahwa data belum cukup untuk
  rata-rata yang sah.
- **Trade-off smoothing vs kehilangan observasi.** Window lebih besar memberi kurva lebih halus, tetapi
  (1) mengorbankan lebih banyak titik awal: MA7 menyisakan 1.726 titik, MA30 1.607 titik dari 1.769 hari
  berdata; (2) bereaksi lebih lambat terhadap perubahan: pada segmen kontinu, lag dengan korelasi tertinggi
  terhadap data asli adalah **3 hari (MA7)** dan **15 hari (MA30)**; (3) pada deret bolong, satu hari hilang
  meng-`NaN`-kan 30 titik MA30 tetapi hanya 7 titik MA7 (463 vs 367 titik `NaN` di luar awal periode).
  Untuk data ini -- pola mingguan menonjol dan tren jangka panjang tidak kuat -- MA7 lebih informatif untuk
  riak mingguan, MA30 lebih tepat untuk membaca arah jangka panjang.
"""),
    ("code", """x_ord = mdates.date2num(daily.index.to_pydatetime())
fit_mask = daily.notna().to_numpy() & daily.index.to_series().between("2015-06-12", "2018-09-30").to_numpy()
coef = np.polyfit(x_ord[fit_mask], daily.to_numpy()[fit_mask], 1)
trend = np.polyval(coef, x_ord[fit_mask])
slope_per_year = coef[0] * 365.25
r = np.corrcoef(x_ord[fit_mask], daily.to_numpy()[fit_mask])[0, 1]
print(f"linear fit 2015-06-12 .. 2018-09-30 ({fit_mask.sum():,} days): "
      f"slope {slope_per_year:+,.0f} vehicles/hour per year, r = {r:.3f}, R^2 = {r**2:.3f}")"""),
    ("code", """fig, ax = plt.subplots(figsize=(14, 4.6))
ax.plot(daily.index, daily.values, color="lightsteelblue", lw=0.7, label="Daily average (raw)")
ax.plot(ma30.index, ma30.values, color="firebrick", lw=1.8, label="MA 30 days")
ax.plot(daily.index[fit_mask], trend, color="black", lw=1.4, ls="--",
        label=f"Linear fit 2015-06 to 2018-09 ({slope_per_year:+,.0f} veh/h per year, R\\u00b2 = {r**2:.3f})")
ax.axvspan(gap["gap_start"], gap["gap_end"], color="firebrick", alpha=0.10)
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set(title="Robustness check: 30-day moving average and a linear fit on the gap-free period",
       xlabel="Date", ylabel="Average traffic volume (vehicles/hour)")
ax.legend(loc="lower left", ncol=3, fontsize=8.5)
plt.tight_layout()
plt.show()"""),
    ("markdown", """**Interpretasi pembanding.** Garis putus-putus adalah `numpy.polyfit` derajat 1 pada
2015-06-12 s.d. 2018-09-30 (periode terpanjang tanpa pemadaman), agar tidak mencampur level data sebelum dan
sesudah celah. Hasil cetakannya: kemiringan **+42 kendaraan/jam per tahun**, r = 0,072 dan **R^2 = 0,005**
pada 1.198 hari -- hampir tidak menjelaskan variasi apa pun (0,5%). Artinya **tidak ada tren naik/turun
jangka panjang** yang berarti; kesimpulan ini konsisten baik dengan MA 30 maupun dengan fit linear, sehingga
tidak bergantung pada satu metode saja."""),
    ("markdown", """## 13. Key Findings & Insights


Setiap insight menyertakan bukti numerik yang dicetak oleh notebook (sel kode di bagian terkait) atau
terlihat pada gambar yang dirujuk. Tidak ada klaim sebab-akibat yang tidak dapat diuji dari data.

### 13.1 Bukti pendukung"""),
    ("code", """hourly_all = proc.groupby("hour")["traffic_volume"].mean()
weekday_hourly = proc.loc[~proc["is_weekend"]].groupby("hour")["traffic_volume"].mean()
weekend_hourly = proc.loc[proc["is_weekend"]].groupby("hour")["traffic_volume"].mean()
evidence_rows = [
    ("overall daily mean (vehicles/hour)", f"{daily_avg.mean():,.0f}"),
    ("linear slope 2015-06..2018-09 (vehicles/hour per year)", f"{slope_per_year:+,.0f}"),
    ("linear fit R^2 (1,198 days)", f"{r ** 2:.4f}"),
    ("sd raw daily / MA7 / MA30", f"{daily.std():,.0f} / {ma7.std():,.0f} / {ma30.std():,.0f}"),
    ("valid MA7 / MA30 points (of 1,769 days with data)", f"{ma7.notna().sum():,} / {ma30.notna().sum():,}"),
    ("weekday mean / weekend mean", f"{wd.mean():,.0f} / {we.mean():,.0f}"),
    ("weekday-weekend gap", f"{wd.mean() - we.mean():,.0f}"),
    ("weekday peak hour / weekend peak hour",
     f"{weekday_hourly.idxmax():02d}:00 ({weekday_hourly.max():,.0f}) / "
     f"{weekend_hourly.idxmax():02d}:00 ({weekend_hourly.max():,.0f})"),
    ("lowest hour of day (all days)", f"{hourly_all.idxmin():02d}:00 ({hourly_all.min():,.0f})"),
    ("busiest complete day", f"{full_days_total.loc[full_days_total['total'].idxmax(), 'date'].date()} "
                             f"({full_days_total['total'].max():,} vehicles)"),
    ("quietest complete day", f"{full_days_total.loc[full_days_total['total'].idxmin(), 'date'].date()} "
                              f"({full_days_total['total'].min():,} vehicles)"),
    ("monthly mean: Jan / Aug (all days)",
     f"{month_mean.loc['Jan', 'mean']:,.0f} / {month_mean.loc['Aug', 'mean']:,.0f}"),
    ("monthly mean weekday: lowest / highest (month number)",
     f"{proc.loc[~proc['is_weekend']].groupby('month').traffic_volume.mean().idxmin()} / "
     f"{proc.loc[~proc['is_weekend']].groupby('month').traffic_volume.mean().idxmax()}"),
    ("missing hours", f"{len(missing):,} of {len(full_index):,} ({len(missing) / len(full_index):.1%})"),
]
evidence = pd.DataFrame(evidence_rows, columns=["metric", "value"])
evidence"""),
    ("markdown", """### 13.2 Lima insight utama
**1. Tren volume kendaraan: datar dalam jangka panjang.**
Rata-rata harian di jendela 2013-2018 adalah **3.281 kendaraan/jam** (median 3.483, nilai dicetak di atas).
Fit linear pada periode bebas pemadaman (2015-06 s.d. 2018-09, 1.198 hari) hanya memberi kemiringan
**+42 kendaraan/jam per tahun** dengan **R^2 = 0,005** (r = 0,072): model linear menjelaskan kurang dari
1% variasi harian, jauh di bawah simpangan baku harian (604). Bukti visual: `05_moving_average.png`
(garis MA30 mendatar) dan garis fit pada gambar pembanding di SS12. Tidak ada bukti naik/turun lalu lintas
yang berarti pada periode ini.

**2. Weekday vs weekend: weekday lebih tinggi dan berbentuk berbeda.**
Mean jam weekday **3.557** vs weekend **2.624** kendaraan/jam (selisih **934**, +36%); median 4.159 vs
2.771. Selisih terbesar bukan di malam hari (porsi jam < 1.000 hampir sama: 21,7% vs 23,7%), melainkan pada
jam pagi 06:00–09:00 (**5.250 vs 2.383**). Rata-rata mingguan (hanya minggu lengkap) **3.559 vs 2.636**
(`03_multiple_time_series.png`). Kedua garis bergerak searah, artinya keduanya dipengaruhi faktor waktu
yang sama; dataset tidak memuat bukti penyebabnya.

**3. Pola aktivitas per jam: dua puncak hari kerja, satu puncak siang akhir pekan.**
Weekday memuncak pada **16:00 (6.239)**, disusul **07:00 (6.064)** dan 17:00 (5.826). Weekend memuncak
**13:00 (4.408)**. Sel heatmap terpadat **Rabu 16:00 (6.414)**, tersepi **Selasa 02:00 (277)**
(`04_seasonal_heatmap.png`). Jam 03:00 adalah titik terendah semua-hari (373).

**4. Periode volume tinggi dan rendah.**
Tinggi: jam 15:00-18:00 pada hari kerja (rata-rata >= 5.272 di SS7.3) dan hari Jumat (3.675, tertinggi di
antara hari). Rendah: dini hari 00:00-04:00 (jam 03:00 = 373, terendah seluruh hari) dan Minggu (2.426).
Per bulan, Januari (3.060) dan Desember (3.040) terendah, Agustus (3.430) tertinggi, tetapi rentang
antar-bulan hanya sekitar 6%: jauh lebih kecil dari rentang antar-jam. Untuk hari kerja saja, Januari
(3.292) terendah dan Juni (3.705) tertinggi. Hari lengkap tersibuk: **31 Agustus 2017 (97.332
kendaraan/hari)**; hari lengkap tersepi: **23 Juli 2016 (6.654 kendaraan/hari, hari dengan dua jam volume 0
yang sudah ditandai `is_sensor_zero`)**. Semua angka dicetak pada tabel bukti di atas.

**5. Moving average: window besar = lebih halus, tetapi titik awal terbuang.**
Standar deviasi harian turun **604 -> 230 (MA7) -> 167 (MA30)** dan rentang turun **4.986 -> 1.650 -> 843**;
MA7 menyisakan 1.726 titik, MA30 1.607 titik dari 1.769 hari berdata. `min_periods = window` membuat 7 titik
pertama MA7 dan 30 titik pertama MA30 `NaN`, ditambah titik yang jendelanya menyentuh hari kosong. MA7
masih memperlihatkan riak mingguan (lag 3 hari terhadap data asli), MA30 hanya arah jangka panjang (lag 15
hari), dan arah itu datar (insight 1).

### Keterbatasan

- Dataset hanya satu arah (westbound) pada satu koridor; hasil tidak dapat digeneralisasi ke koridor lain.
- 22,79% jam hilang, termasuk pemadaman 7.386 jam (2014-08-08 → 2015-06-11); tahun 2014/2015 tidak lengkap.
- 34,7% hari berdata parsial; total harian pada hari parsial undercount (median 69% dari hari lengkap).
- `holiday` hanya dicatat pada baris 00:00 dan hanya untuk 53 tanggal; hari libur pada jam yang hilang tidak terwakili.
- Pada 79 timestamp ganda, dua pembacaan cuaca berbeda digabung; nilai cuaca pada baris itu perkiraan.
- Tidak ada atribut kejadian (kecelakaan, konstruksi, penutupan jalan) untuk menjelaskan lonjakan tertentu;
  karena itu semua hubungan dilaporkan sebagai asosiasi, bukan sebab-akibat."""),
    ("markdown", """## 14. Conclusion

1. Volume lalu lintas I-94 selama 2012-2018 **ditentukan oleh kalender**: jam dalam hari dan jenis hari
   (weekday/weekend) memberi perbedaan jauh lebih besar daripada bulan atau tahun (weekday vs weekend
   +934 kendaraan/jam; jam 03:00 = 373 berbanding jam sibuk weekday 16:00 di atas 6.200).
2. **Tidak ada tren jangka panjang yang berarti**: MA 30 datar, fit linear pada periode tanpa pemadaman
   +42 kendaraan/jam per tahun dengan R^2 = 0,005.
3. **Kualitas data adalah bagian dari hasil**: 5.445 timestamp duplikat (target identik), 22,79% jam
   hilang termasuk pemadaman 308 hari, serta sentinel sensor. Semua ditangani dengan flag dan penanda
   celah — tanpa imputasi dan tanpa menghapus outlier/label yang tidak terverifikasi.
4. **Moving average** dengan `min_periods = window` memberi pembacaan tren yang jujur: kehalusan bertambah
   dengan window, tetapi titik awal (dan titik di sekitar celah) hilang — trade-off yang harus dilaporkan,
   bukan disembunyikan.
5. Seluruh kode dapat dijalankan ulang (`scripts/download_data.py` → `scripts/preprocess.py` → notebook);
   semua angka pada notebook berasal dari eksekusi dataset asli UCI."""),
    ("markdown", """## 15. AI Usage Declaration

Sel ini disusun sesuai format Lembar Deklarasi Penggunaan AI pada halaman 4 `Midterm Project.pdf`.
Identitas dan tabel **belum diisi** — wajib dilengkapi oleh masing-masing anggota kelompok sesuai
penggunaan sebenarnya. Jangan menghapus tabel apa pun: jika tidak menggunakan AI, isi keterangan
"Tidak menggunakan AI" pada tabel.

> Saya, **[Nama Lengkap] / [NIM]**, menyatakan bahwa saya **[menggunakan / tidak menggunakan]** alat AI
> generatif dalam pengerjaan tugas ini. Seluruh interpretasi, insight, dan kesimpulan yang disampaikan
> merupakan hasil pemahaman saya sendiri.

| No | Nama Tools AI | Bagian yang Dibantu | Bentuk Bantuan / Tujuan Prompt | Tingkat Ketergantungan |
|---|---|---|---|---|
| 1 | [isi nama tools AI] | [mis. §7 EDA / §12 Moving Average] | [ringkasan prompt] | Rendah / Sedang / Tinggi |
| 2 | | | | |
| 3 | | | | |

**Lampiran screenshot prompting.** Untuk setiap penggunaan AI pada tabel, sertakan tangkapan layar yang
menunjukkan (a) nama platform AI, (b) prompt yang diajukan, dan (c) respons yang diberikan. Pilih salah
satu cara dan sebutkan di sini:

- (a) disisipkan langsung sebagai gambar pada sel markdown paling akhir notebook ini, **atau**
- (b) dikumpulkan terpisah dalam berkas `Screenshot_AI_[NIM].pdf` / kumpulan gambar.

Cara yang dipilih: **[isi (a) atau (b)]**.

> Catatan proyek: tidak ada identitas mahasiswa maupun bukti screenshot yang didaftarkan otomatis oleh notebook
> ini. Bagian ini sengaja dibiarkan sebagai formulir agar deklarasi tidak memuat klaim palsu."""),
    ("markdown", """## 16. References

1. UCI Machine Learning Repository. *Metro Interstate Traffic Volume Data Set* (ID 492).
   <https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume>
   (diakses melalui paket `ucimlrepo`, `fetch_ucirepo(id=492)`).
2. Hogue, J., & Dhingra, P. *A Description of the Metro Interstate Traffic Volume Dataset* (metadata dataset UCI).
3. pandas development team. *pandas: powerful Python data analysis toolkit*.
   <https://pandas.pydata.org/docs/>
4. Harris, C. R., et al. (2020). Array programming with NumPy. *Nature*, 585, 357–362.
   <https://doi.org/10.1038/s41586-020-2649-2>
5. Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering*, 9(3), 90–95.
6. Waskom, M. L. (2021). seaborn: statistical data visualization. *Journal of Open Source Software*, 6(60), 3021.
7. Ucimlrepo contributors. *ucimlrepo* (Python client for the UCI ML Repository).
   <https://pypi.org/project/ucimlrepo/>
8. Materi kuliah Minggu 6 – *Visualisasi Data Time Series* (moving average, fitting model tren)."""),
]

nb = nbf.v4.new_notebook(cells=[
    nbf.v4.new_markdown_cell(t) if k == "markdown" else nbf.v4.new_code_cell(t) for k, t in CELLS
])
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nb.metadata["language_info"] = {"name": "python"}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, OUT)
print(f"wrote {OUT} ({len(CELLS)} cells)")
