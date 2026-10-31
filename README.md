# Time Series Analysis and Visualization of Metro Interstate Traffic Volume (2012–2018)

## Deskripsi Proyek

Proyek analisis deret waktu (time series) atas volume lalu lintas per jam di Interstate 94 arah barat
(Minneapolis–St. Paul, Minnesota) selama Oktober 2012 – September 2018. Proyek mencakup:

1. **Validasi data**: dimensi, tipe data, missing value, duplikasi baris/timestamp, celah waktu, kelengkapan
   observasi harian, outlier, dan nilai sentinel sensor.
2. **Preprocessing** berbasis temuan: deduplikasi hanya bila `traffic_volume` identik, flag data tidak valid,
   fitur kalender — tanpa imputasi dan tanpa penghapusan outlier yang tidak terverifikasi.
3. **EDA**: statistik deskriptif, distribusi, rata-rata per jam/hari/bulan, weekday vs weekend, kelengkapan.
4. **Empat visualisasi wajib**: line plot, area plot, multiple time series (direct labeling), seasonal heatmap.
5. **Analisis tren**: moving average 7 & 30 hari dengan `min_periods = window` + pembanding linear fit.
6. **Insight dan kesimpulan** yang seluruhnya bersumber dari output eksekusi dataset asli.

## Dataset dan Sumber

| Atribut | Nilai |
|---|---|
| Nama | Metro Interstate Traffic Volume |
| Sumber | UCI Machine Learning Repository, dataset ID **492** |
| URL | <https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume> |
| Cara unduh | `ucimlrepo.fetch_ucirepo(id=492)` → `features` (48.204 × 8) + `targets` (48.204 × 1) |
| Granularitas waktu | per jam (`date_time`) |
| Periode | 2012-10-02 09:00 – 2018-09-30 23:00 |
| Observasi | 48.204 baris × 9 kolom |
| Target | `traffic_volume` (kendaraan/jam) |
| Pendukung | `holiday`, `temp`, `rain_1h`, `snow_1h`, `clouds_all`, `weather_main`, `weather_description` |

Data mentah disimpan apa adanya di `data/raw/`; tidak ada dataset dummy atau sumber pengganti.

## Teknologi yang Digunakan

| Teknologi | Versi | Kegunaan |
|---|---|---|
| Python | 3.12 | bahasa utama |
| pandas | 3.1.0 | pemuatan, validasi, `rolling`, `resample` |
| numpy | 2.5.4 | komputasi numerik, `polyfit` |
| matplotlib | 3.11.2 | semua grafik, format tanggal (`mdates`) |
| seaborn | 0.13.2 | histogram, boxplot, KDE |
| scipy | ≥ 1.18 | KDE (`gaussian_kde`) untuk EDA |
| ucimlrepo | 0.0.7 | unduh dataset UCI id 492 |
| Jupyter (notebook, ipykernel, nbformat, nbconvert) | lihat `requirements.txt` | menjalankan notebook end-to-end |

Manajemen dependensi juga tersedia melalui `pyproject.toml` + `uv.lock` (proyek dikelola dengan `uv`).

## Struktur Project

```text
.
├── data/
│   ├── raw/
│   │   └── metro_interstate_traffic_volume.csv      # snapshot UCI apa adanya (48.204 × 9)
│   └── processed/
│       └── metro_interstate_traffic_model.csv       # 40.575 × 24, hasil preprocessing
├── notebooks/
│   ├── metro_interstate_traffic_analysis.ipynb          # versi lengkap: kode + pembahasan & interpretasi
│   └── metro_interstate_traffic_submission_colab.ipynb  # versi submission: point headings murni, native Google Colab
├── reports/
│   ├── quality_report.txt                           # laporan pemeriksaan kualitas data
│   ├── duplicate_timestamp_review.csv               # seluruh baris bertimestamp ganda
│   ├── timestamp_gaps.csv                           # 2.588 celah waktu + panjangnya
│   ├── daily_completeness.csv                       # observasi per tanggal
│   └── figures/
│       ├── 01_line_plot.png                         # line plot
│       ├── 02_area_plot.png                         # area plot
│       ├── 03_multiple_time_series.png              # weekday vs weekend (direct labeling)
│       ├── 04_seasonal_heatmap.png                  # heatmap hari × jam
│       └── 05_moving_average.png                    # MA 7 & 30 hari
├── scripts/
│   ├── download_data.py                             # unduh UCI → data/raw/
│   ├── preprocess.py                                # pemeriksaan + preprocessing → data/processed/ + reports/
│   └── build_notebook.py                            # opsional: generator ulang notebook dari kode Python
├── README.md
├── AI_USAGE_DECLARATION.md                         # deklarasi penggunaan AI (formulir)
├── requirements.txt
└── .gitignore
```

## Instalasi Dependency

Butuh Python ≥ 3.12.

```bash
# opsi A — dengan uv (dipakai saat proyek ini dibuat)
uv sync

# opsi B — dengan venv + pip
python -m venv .venv
source .venv/bin/activate          # Windows Git Bash: source .venv/Scripts/activate
                                   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Pilihan Notebook

Repository ini menyediakan dua varian notebook sesuai kebutuhan:

1. **`metro_interstate_traffic_analysis.ipynb` (Versi Analisis Lengkap)**
   - Berisi seluruh kode, output eksekusi, serta teks pembahasan naratif dan interpretasi detail di bawah setiap visualisasi.
   - Digunakan untuk membaca laporan analisis mendalam.

2. **`metro_interstate_traffic_submission_colab.ipynb` (Versi Pengumpulan / Google Colab Native)**
   - Khusus pengumpulan tugas: teks pembahasan naratif ditiadakan, diganti murni **point heading** (mis. `## 8. Line Plot`, `## 12. Trend Analysis`, dst.).
   - Dilengkapi tombol **Open in Colab** di awal notebook.
   - Mengunduh dataset otomatis jika dijalankan di Google Colab tanpa clone repository.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aulky/time-series-data-visualization/blob/main/notebooks/metro_interstate_traffic_submission_colab.ipynb)

## Cara Menjalankan Notebook

```bash
# 1. unduh dataset UCI (butuh internet) -> data/raw/
python scripts/download_data.py

# 2. validasi + preprocessing -> data/processed/ dan reports/
python scripts/preprocess.py

# 3. buka notebook (disarankan jalankan dari awal: Kernel > Restart & Run All)
jupyter notebook notebooks/metro_interstate_traffic_analysis.ipynb

# atau jalankan headless dan simpan output
jupyter nbconvert --execute --inplace notebooks/metro_interstate_traffic_analysis.ipynb
```

`data/raw/` dan `data/processed/` sudah disertakan, sehingga langkah 1–2 boleh dilewati untuk sekadar
menjalankan notebook.

`scripts/preprocess.py` berhenti dengan error dan meminta review manual apabila menemukan timestamp ganda
dengan nilai `traffic_volume` berbeda — data tidak pernah dihapus secara diam-diam.

## Kondisi Dataset

### Data mentah (`data/raw/`, tidak diubah)

| Item | Nilai |
|---|---|
| Baris × kolom | 48.204 × 9 |
| Missing value | 0 pada 8 kolom; `holiday` kosong pada 48.143 baris (label hanya ada pada 61 baris) |
| Duplicate rows (9 kolom identik) | 17 |
| Duplicate timestamps | 7.629 nilai `date_time` berulang → 5.445 timestamp unik yang ganda, melibatkan 13.074 baris |
| Timestamp unik | 40.575 |
| Jam yang hilang vs indeks jam penuh (52.551 jam) | 11.976 (22,79%) |
| Celah kontigu | 2.588 celah; terbesar **7.386 jam (≈10 bulan)**, 2014-08-08 02:00 → 2015-06-11 19:00 |
| Hari kalender | 1.860 hari berdata dari 2.190 hari dalam rentang; 1.214 hari lengkap 24 jam |
| Nilai ekstrem `traffic_volume` | 0–7.280; tidak ada outlier IQR (batas atas IQR 10.507 > maksimum 7.280) |

### Data processed (`data/processed/`)

40.575 × 24 — satu baris per timestamp unik, tambahan kolom kalender/flag. Dua baris `traffic_volume = 0`
dan 10 baris `temp = 0 K` **dipertahankan** dengan flag `is_sensor_zero` / `is_temp_error`. Tidak ada
imputasi dan tidak ada baris yang diekstrapolasi ke jam yang hilang.

## Masalah Kualitas Data yang Ditemukan

| # | Temuan | Bukti | Penanganan |
|---|---|---|---|
| 1 | **Duplicate timestamps** | 5.445 timestamp ganda. `traffic_volume` **identik pada semua grup**; 15 grup identik di semua kolom, 5.430 grup berbeda pada kolom pendukung | `keep="first"` (aman untuk target); detail di `reports/duplicate_timestamp_review.csv` |
| 2 | **Label cuaca sinonim tidak seragam** | 5.386 grup duplikat: `Rain`/`light rain` vs `Drizzle`/`light intensity drizzle`; label `SQUALLS`, `Sky is Clear` beda kapitalisasi (1.730 baris) | `weather_description` di-lowercase; perbedaan sinonim didokumentasikan |
| 3 | **Dua pembacaan cuaca digabung pada jam yang sama** | 78 grup berbeda suhu, selisih ekstrem 20,43 K (mis. 2014-01-17 06:00: 276,79 K vs 256,36 K pada volume 5.441) | Dipertahankan; dicatat bahwa kolom cuaca pada baris itu bersifat perkiraan (nilai yang tersimpan bergantung pada urutan berkas sumber) |
| 4 | **Tidak ada missing value, tetapi 22,79% jam tidak ada** | 11.976 jam hilang, 2.588 celah | Tidak diisi; `gap_hours` dicatat, analisis eksekusi satu-per-segmen, rolling rata-rata tidak melintasi celah |
| 5 | **Pemadaman rekaman ±10 bulan** | 7.386 jam berturut-turut (61,7% dari seluruh jam hilang), 2014-08-08 → 2015-06-11 | Ditandai pada grafik; tahun 2014/2015 ditandai `complete_year=False` |
| 6 | **Hari parsial** | 646 hari (di luar 2 hari batas) memiliki < 24 jam; 330 tanggal sama sekali tanpa rekaman; 2012-10-02 hanya 15 jam (mulai 09:00) | Hari parsial tidak dipakai untuk dekomposisi musiman; rerata harian hanya dari hari 24 jam |
| 7 | **Label `holiday` hanya pada baris 00:00** | 61 baris berlabel teks, seluruhnya jam 00:00, mencakup 53 tanggal | `is_holiday` (tingkat baris) + `holiday_date` (tingkat hari); perbandingan dilakukan pada tingkat tanggal |
| 8 | **`temp` mustahil** | 10 baris `temp = 0 K` (2014-01-31, 2014-02-02) | Flag `is_temp_error`; `temp_c_clean` = NaN pada baris tersebut (tanpa imputasi) |
| 9 | **`rain_1h` sentinel** | 1 baris 9.831,3 mm/jam (2016-07-11 17:00); nilai normal < 56 mm | Flag `is_rain_error` |
| 10 | **Volume nol** | 2 baris (2016-07-23 18:00 dan 23:00) dengan suhu/awan normal | Flag `is_sensor_zero`; dugaan downtime alat, bukan dihapus |
| 11 | **17 baris identik penuh** | Duplikasi sempurna seluruh 9 kolom | Terhapus oleh deduplikasi timestamp |
| 12 | **Kategori jarang** | `Squall` = 1 baris (volume 420), `Smoke` = 15 baris | Tidak dihapus; dicatat agar tidak ditafsirkan |

Outlier `traffic_volume`: **tidak ada** menurut IQR, sehingga tidak ada yang dihapus — puncak 7.280 kendaraan/jam
adalah jam sibuk yang wajar.

## Visualisasi dan Analisis Tren (sesuai `Midterm Project.pdf` Bagian 2)

| # | Jenis (wajib) | File | Isi |
|---|---|---|---|
| 1 | Line plot | `reports/figures/01_line_plot.png` | rata-rata `traffic_volume` harian 2013–2018, tanggal diformat, celah pemadaman ditandai |
| 2 | Area plot | `reports/figures/02_area_plot.png` | total `traffic_volume` per tanggal; hari lengkap (hijau) vs hari parsial (oranye) dibedakan + catatan undercount |
| 3 | Multiple time series | `reports/figures/03_multiple_time_series.png` | weekday vs weekend, rata-rata per minggu, **direct labeling** di ujung garis (jarak label 1.518 kendaraan/jam, tidak bertabrakan) |
| 4 | Seasonal heatmap | `reports/figures/04_seasonal_heatmap.png` | Senin–Minggu × 00–23, mean volume, label kronologis + colorbar |
| 5 | Moving average (analisis tren wajib) | `reports/figures/05_moving_average.png` | data asli + MA 7 hari + MA 30 hari, `min_periods = window`, celah data ditandai |

Notebook §7 memuat EDA (statistik deskriptif, distribusi/ECDF, rata-rata per jam/hari/bulan, weekday vs
weekend, kelengkapan temporal). Setiap gambar diikuti penjelasan variabel, interpretasi, dan insight dari
output aktual. §12 membahas perbedaan MA 7 vs MA 30, pengaruh ukuran window terhadap kehalusan, alasan NaN
di awal periode, dan trade-off smoothing vs kehilangan observasi; ada juga pembanding linear fit
(`numpy.polyfit`) pada periode bebas pemadaman.

## Temuan Analisis Singkat

- **Pola harian**: jam weekday 16:00 (6.239) > 07:00 (6.064) > 17:00 (5.826); akhir pekan memuncak siang
  (13:00, 4.408) dan paginya jauh lebih sepi (jam 06:00–09:00: 2.383 vs 5.250).
- **Distribusi**: bimodal (jam malam vs jam sibuk), median 3.427, mean 3.291, kurtosis −1,30.
- **Weekday vs weekend**: 3.557 vs 2.624 kendaraan/jam (+36%); median 4.159 vs 2.771.
- **Pola mingguan/bulanan**: rerata terendah Minggu (2.426), tertinggi Jumat (3.675); per bulan terendah
  Desember (3.040) dan Januari (3.060), tertinggi Agustus (3.430) — rentang antar-bulan hanya ±6%.
- **Pola mingguan time series**: rata-rata per minggu weekday 3.559 vs weekend 2.636, bergerak searah.
- **Tren**: MA 7/30 hari menurunkan simpangan baku harian 604 → 230 → 167 (rentang 4.986 → 1.650 → 843);
  linear fit 2015-06→2018-09 hanya **+42 kendaraan/jam per tahun** (R² = 0,005), sehingga tidak ada tren
  jangka panjang yang bermakna.
- **Periode tinggi/rendah**: hari lengkap tersibuk 31 Agustus 2017 (97.332 kendaraan/hari); tersepi 23 Juli
  2016 (6.654; hari dengan dua jam volume 0 yang sudah ditandai).

Lima insight lengkap beserta bukti numerik ada di §13 notebook.

## Keterbatasan

- Dataset hanya satu arah (westbound) pada satu koridor; hasil tidak dapat digeneralisasi.
- Analisis tahunan 2012, 2014, 2015, 2018 tidak sebanding karena rekaman tidak lengkap.
- Kolom cuaca pada 78 timestamp ganda berasal dari penggabungan dua pembacaan; nilainya perkiraan.
- Tidak ada atribut kejadian (kecelakaan, konstruksi) untuk menjelaskan lonjakan tertentu; semua hubungan
  dilaporkan sebagai asosiasi.

## Deklarasi Penggunaan AI

Berkas `AI_USAGE_DECLARATION.md` mendokumentasikan penggunaan AI pada sesi kerja proyek ini (nama tools,
bagian yang dibantu, tingkat ketergantungan, dan ringkasan prompt). Format yang sama tersedia di §15 notebook
sebagai formulir. Identitas (nama/NIM), kolom verifikasi mahasiswa, dan lampiran screenshot **sengaja
dibiarkan kosong** dan wajib dilengkapi oleh mahasiswa.

