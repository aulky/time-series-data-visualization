# Deklarasi Penggunaan AI Generatif

**Proyek:** Time Series Analysis and Visualization of Metro Interstate Traffic Volume (2012–2018)
**Repository:** `cak4xbb3-time-series-visualization`
**Menulis:** Claude Code (agen AI) pada sesi kerja yang sama dengan pembuatan proyek ini
**Format:** Lembar Deklarasi Penggunaan AI, halaman 4 `Midterm Project.pdf`

> Saya, **[Nama Lengkap] / [NIM]**, menyatakan bahwa saya **[menggunakan / tidak menggunakan]** alat AI
> generatif dalam pengerjaan tugas ini. Seluruh interpretasi, insight, dan kesimpulan yang disampaikan
> merupakan hasil pemahaman saya sendiri.

> **Wajib diisi oleh mahasiswa.** Identitas dan pilihan **menggunakan / tidak menggunakan** di atas sengaja
> dibiarkan sebagai placeholder. Kolom "Pemverifikasi (mahasiswa)" pada tabel di bawah juga masih kosong:
> setiap baris bantuan AI harus saya tinjau dan saya konfirmasi kebenarannya sebelum deklarasi dinyatakan final.

## Tabel Penggunaan AI

Bantuan pada sesi ini diberikan melalui **Claude Code** (agen AI berbasis terminal yang dijalankan atas model
Claude, dengan akses baca/tulis ke repository). Karena seluruh pekerjaan berlangsung dalam satu sesi, rincian
dipisah per bagian pekerjaan, bukan per tool berbeda.

| No | Nama Tools AI | Bagian yang Dibantu | Bentuk Bantuan / Tujuan Prompt | Tingkat Ketergantungan | Pemverifikasi (mahasiswa) |
|---|---|---|---|---|---|
| 1 | Claude Code | Pengaturan proyek, `scripts/download_data.py` | Instruksi meminta implementasi langsung: membuat struktur folder, mengunduh dataset UCI id 492 via `ucimlrepo`, menyimpan snapshot mentah ke `data/raw/` | Tinggi | ☐ sudah diverifikasi |
| 2 | Claude Code | `scripts/preprocess.py` (§5–§6) | Prompt meminta pemeriksaan kualitas (duplikasi timestamp, celah waktu, kelengkapan harian) dan preprocessing tanpa imputasi; AI menulis skrip beserta aturan berhenti bila ada konflik nilai | Tinggi | ☐ sudah diverifikasi |
| 3 | Claude Code | EDA dan empat visualisasi wajib (§7–§11) | Prompt meminta line plot, area plot, multiple time series dengan direct labeling, dan seasonal heatmap sesuai `Midterm Project.pdf` | Tinggi | ☐ sudah diverifikasi |
| 4 | Claude Code | Moving average (§12) | Prompt meminta MA 7 & 30 hari dengan `rolling` + `min_periods` sesuai window, tanpa mengisi tanggal kosong | Sedang | ☐ sudah diverifikasi |
| 5 | Claude Code | Perbaikan error eksekusi | Iterasi debugging sel notebook yang gagal (mis. unpacking `np.polyval`, agregasi `groupby` pandas 3, nama variabel hilang) sampai Run All bersih | Sedang | ☐ sudah diverifikasi |
| 6 | Claude Code | Final audit (§ semua) | Prompt meminta audit dan perbaikan langsung; AI menemukan dan memperbaiki folder tujuan yang belum ada, grafik yang tersimpan kosong, dan path absolut pada output | Sedang | ☐ sudah diverifikasi |
| 7 | Claude Code | README dan dokumen deklarasi | Prompt meminta README (deskripsi, sumber data, teknologi, instalasi, cara menjalankan, struktur) serta berkas deklarasi ini | Rendah | ☐ sudah diverifikasi |
| 8 | Claude Code | Interpretasi dan insight (§13) | AI menulis narasi interpretasi; angka diambil dari output eksekusi sel kode (dicetak di notebook), bukan dikarang | Sedang | ☐ sudah diverifikasi |

**Catatan tingkat ketergantungan:** "Tinggi" berarti sebagian besar kode pada bagian tersebut dihasilkan AI
dan mahasiswa perlu memahaminya baris per baris; "Sedang" berarti AI menghasilkan kode/narasi yang kemudian
disunting dan diverifikasi ulang terhadap output; "Rendah" berarti materi non-teknis (dokumentasi).

## Yang Dikerjakan AI vs yang Tetap Wajib Dikerjakan Mahasiswa

| AI membantu | Mahasiswa wajib memastikan |
|---|---|
| Menulis hampir seluruh kode analisis dan grafik | Mampu menjelaskan alur kode dan alasan tiap keputusan (deduplikasi, `min_periods`, pemisahan hari parsial) |
| Menyusun draft interpretasi dan insight | Memeriksa setiap angka pada narasi terhadap output sel notebook; menyunting klaim yang tidak didukung |
| Membuat README dan deklarasi ini | Mengisi identitas, memilih "menggunakan / tidak menggunakan", dan memverifikasi tabel |
| Menjalankan Run All dan audit otomatis | Menjalankan ulang notebook sendiri di lingkungan bersih sebelum mengumpulkan |

## Data, Angka, dan Kebenaran Isi

- Seluruh angka pada notebook berasal dari eksekusi dataset asli UCI (48.204 baris), bukan data dummy.
- File mentah tidak diubah; SHA-256-nya diverifikasi di §4 notebook:
  `312cb379ec73b71dc4d95c136e542c753690e943f43b49044d4ed80640fa2d76`.
- AI **tidak** menambahkan identitas mahasiswa, angka contoh, atau bukti screenshot apa pun. Tidak ada klaim
  sebab-akibat yang ditulis tanpa data; hubungan yang tidak dapat diuji dinyatakan sebagai asosiasi.

## Lampiran Screenshot Prompting

Pada sesi ini, screenshot percakapan **belum dilampirkan** karena berkas gambar tidak dibuat otomatis oleh AI.
Mahasiswa wajib menambahkannya dengan salah satu cara berikut, lalu menyebutkan pilihannya di sini:

- (a) disisipkan sebagai gambar pada sel markdown paling akhir notebook, **atau**
- (b) dikumpulkan terpisah dalam berkas `Screenshot_AI_[NIM].pdf` / kumpulan gambar.

Cara yang dipilih: **[isi (a) atau (b)]**

Setiap screenshot minimal menunjukkan: nama platform AI (**Claude Code**), prompt yang diajukan, dan respons
yang diberikan.

## Ringkasan Prompt Sesi Ini

| Urutan | Ringkasan permintaan mahasiswa |
|---|---|
| 1 | Implementasi proyek: struktur folder, unduh dataset UCI 492, validasi data, preprocessing, README, requirements, notebook awal |
| 2 | EDA dan empat visualisasi wajib beserta interpretasi di notebook utama |
| 3 | Analisis tren moving average 7 & 30 hari, lima insight, struktur notebook final, deklarasi AI, README |
| 4 | Audit menyeluruh dan perbaikan masalah yang ditemukan (dikerjakan langsung, bukan hanya dilaporkan) |
| 5 | Membuat berkas deklarasi penggunaan AI (berkas ini) |

> Berkas ini mendokumentasikan bantuan AI secara jujur dan terperinci. Harap verifikasi ulang isinya sebelum melampirkan deklarasi ini pada pengumpulan tugas.
