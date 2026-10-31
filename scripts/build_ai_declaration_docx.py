"""Build the AI usage declaration report (Lembar Deklarasi Penggunaan AI).

Output: "Deklarasi Penggunaan AI.docx" di root repo.

Isi mengikuti format halaman 4 Midterm Project.pdf:
- Pernyataan (nama/NIM diisi sesuai identitas kelompok di notebook)
- Tabel penggunaan AI (tools, bagian, bentuk bantuan, tingkat ketergantungan)
- Lampiran screenshot prompting dari folder screenshot/
"""

from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Deklarasi Penggunaan AI.docx"
SHOTS = ROOT / "screenshot"

STUDENT_NAME = "Muhammad Aulia Muzzaki Nugraha"
STUDENT_NIM = "2311102051"
GROUP = [
    ("Muhammad Aulia Muzzaki Nugraha", "2311102051"),
    ("Faqih Abdullah", "2311102048"),
    ("Muhamad Nasrulloh", "2311102044"),
    ("Raihan Ramadhan", "2311102040"),
    ("Bayu Kuncoro Adi", "2311102031"),
]
CLASS = "S1IF-11-GAB-02"
PROJECT = "Time Series Analysis and Visualization of Metro Interstate Traffic Volume (2012–2018)"
REPO = "https://github.com/aulky/time-series-data-visualization"


# ---------------------------------------------------------------- helpers
def shade(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def set_cell(cell, text: str, bold: bool = False, size: int = 9, center: bool = False) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "Calibri"
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def heading(doc, text: str, size: int = 13, space_before: int = 14) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(size)
    run.font.name = "Calibri"
    run.font.color.rgb = RGBColor(0x1F, 0x3B, 0x57)


def body(doc, text: str, size: int = 10, italic: bool = False, space_after: int = 6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.name = "Calibri"
    run.italic = italic
    return p


def wide_section(section) -> None:
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    section.left_margin = section.right_margin = Cm(2.0)
    section.top_margin = section.bottom_margin = Cm(1.8)


def table_borders(table) -> None:
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:color"), "9CA3AF")
        borders.append(el)
    tbl_pr.append(borders)


def repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


# ---------------------------------------------------------------- data
AI_ROWS = [
    (
        "Claude Code",
        "Analisis tren moving average, key insights, dan penyelesaian notebook",
        "\"Implementasikan MA 7 dan MA 30 hari dengan rolling + min_periods=window tanpa mengisi "
        "tanggal kosong, tulis lima insight dengan bukti numerik, susun urutan 16 bagian notebook\"",
        "Tinggi",
    ),
    (
        "Claude Code",
        "Setup proyek, unduh dataset UCI, validasi dan preprocessing data",
        "\"Implementasi proyek time series: struktur folder, unduh dataset UCI 492, "
        "periksa kualitas data (duplikasi timestamp, celah waktu), preprocessing tanpa imputasi\"",
        "Tinggi",
    ),
    (
        "Claude Code",
        "EDA, empat visualisasi wajib, dan slide/storytelling grafik",
        "\"Buat EDA statistik deskriptif, distribusi, rata-rata per jam/hari/bulan dan weekday "
        "vs weekend, lalu empat visualisasi wajib (line, area, multiple time series, heatmap)\"",
        "Tinggi",
    ),
    (
        "Claude Code",
        "Audit akhir: perbaikan error eksekusi, grafik kosong, path relatif, guard integritas data",
        "\"Lakukan final audit: Run All dari kernel baru, perbaiki langsung masalah yang ditemukan, "
        "jangan hanya melaporkan\"",
        "Sedang",
    ),
    (
        "Claude Code",
        "Penulisan interpretasi dan narasi insight pada notebook",
        "AI menulis draft narasi; angka diambil dari output eksekusi sel kode, bukan dikarang",
        "Sedang",
    ),
    (
        "Claude Code",
        "README, skrip audit otomatis, notebook submission Google Colab, dan deklarasi ini",
        "\"Perbaiki README (deskripsi, sumber, teknologi, instalasi, cara menjalankan, struktur)\" "
        "dan \"buat notebook submission khusus Colab tanpa narasi pembahasan\"",
        "Rendah",
    ),
]

SHOT_META = {
    "Screenshot 2026-10-30 232524.png": (
        "Implementasi notebook, visualisasi, dan analisis tren",
        "Respons AI atas instruksi implementasi: menyusun notebook analisis time series, empat visualisasi "
        "wajib, serta analisis tren (moving average 7 & 30 hari) pada dataset UCI Metro Interstate Traffic "
        "Volume. Screenshot ini menunjukkan alur pengerjaan kode yang kemudian diverifikasi lewat Run All.",
    ),
    "Screenshot 2026-10-31 062104.png": (
        "Notebook diperbarui dan dieksekusi ulang: EDA, empat visualisasi wajib, dan tren",
        "Respons menunjukkan notebook 83 sel (42 sel kode) dieksekusi tanpa error, 17 gambar "
        "tersimpan, tabel struktur §7–§10, empat grafik wajib beserta angka kunci hasil eksekusi.",
    ),
    "Screenshot 2026-10-31 062118.png": (
        "Ringkasan audit: masalah yang ditemukan dan perbaikannya",
        "Tabel delapan masalah kualitas data (timestamp duplikat, gap, sentinel sensor, dsb.) "
        "beserta bukti dan penanganannya, serta daftar grafik yang berhasil dibuat.",
    ),
    "Screenshot 2026-10-31 062209.png": (
        "Implementasi analisis tren moving average dan struktur notebook",
        "Prompt meminta MA 7 & 30 hari dengan rolling, min_periods sesuai window, indeks kalender "
        "harian, tanpa nilai buatan; respons menjelaskan grafik 05_moving_average.png dan penjelasan "
        "trade-off window.",
    ),
    "Screenshot 2026-10-31 062242.png": (
        "Verifikasi eksekusi: 0 error dan implementasi moving average",
        "Output eksekusi \u201ccode cells 42 errors 0 figures 17\u201d beserta tabel struktur notebook §7–§10 "
        "dan rincian empat grafik wajib.",
    ),
    "Screenshot 2026-10-31 062258.png": (
        "Permintaan analisis tren (MA 7 & 30 hari) dan key insights",
        "Prompt lengkap bagian A (mandatory trend analysis), B (lima key insights), dan C (struktur "
        "notebook final) yang menjadi acuan implementasi §12\u2013§13.",
    ),
    "Screenshot 2026-10-31 062331.png": (
        "Hasil eksekusi end-to-end dan koreksi yang dilakukan saat verifikasi",
        "Respons menyatakan notebook dieksekusi 90 sel (45 sel kode), 0 error, 0 stderr, 19 gambar; "
        "menyertakan angka MA (titik valid, simpangan baku) dan daftar koreksi.",
    ),
    "Screenshot 2026-10-31 062409.png": (
        "Permintaan final audit (eksekusi, validasi visualisasi, validasi data)",
        "Prompt audit: restart kernel, Run All, relative path, empat visualisasi wajib, direct labeling, "
        "MA 7 & 30 hari, serta validasi dataset UCI.",
    ),
    "Screenshot 2026-10-31 062442.png": (
        "Laporan final audit dan perbaikan langsung",
        "Tabel delapan masalah yang ditemukan dan diperbaiki (path absolut, folder tujuan belum ada, "
        "grafik kosong, interpretasi, dll.), implementasi yang berhasil, dan grafik terverifikasi.",
    ),
}


# ---------------------------------------------------------------- document
doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(10)

sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin = sec.bottom_margin = Cm(2.0)

# header line
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("LEMBAR DEKLARASI PENGGUNAAN ARTIFICIAL INTELLIGENCE")
r.bold = True
r.font.size = Pt(15)
r.font.color.rgb = RGBColor(0x1F, 0x3B, 0x57)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Tugas Besar Tengah Semester - CAK4XBB3 Visualisasi Data")
r.font.size = Pt(10.5)
r.italic = True

# identity table
heading(doc, "A. Identitas Kelompok", size=12)
info = [
    ("Judul Proyek", PROJECT),
    ("Repository", REPO),
    ("Kelas", CLASS),
    ("Anggota", "\n".join(f"{i}. {n} / {nim}" for i, (n, nim) in enumerate(GROUP, 1))),
]
t = doc.add_table(rows=0, cols=2)
t.style = "Table Grid"
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for label, value in info:
    row = t.add_row().cells
    set_cell(row[0], label, bold=True)
    set_cell(row[1], value)
    shade(row[0], "EEF3F8")
t.columns[0].width = Cm(3.4)
t.columns[1].width = Cm(13.2)
for row in t.rows:
    row.cells[0].width = Cm(3.4)
    row.cells[1].width = Cm(13.2)

# declaration statement
heading(doc, "B. Pernyataan", size=12)
p = doc.add_paragraph()
p.paragraph_format.left_indent = Cm(0.8)
p.paragraph_format.right_indent = Cm(0.8)
p.paragraph_format.space_before = Pt(4)
p.paragraph_format.space_after = Pt(10)
p.paragraph_format.line_spacing = 1.3
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
r = p.add_run(
    f"Saya, {STUDENT_NAME} / {STUDENT_NIM}, menyatakan bahwa saya menggunakan alat AI generatif "
    "dalam pengerjaan tugas ini. Seluruh interpretasi, insight, dan kesimpulan yang disampaikan "
    "merupakan hasil pemahaman saya sendiri."
)
r.font.size = Pt(11)
r.italic = True

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(6)
r = p.add_run(
    "Pernyataan di atas ditandatangani oleh perwakilan kelompok yang terdaftar. Bantuan AI pada "
    "proyek ini digunakan untuk implementasi kode analisis, visualisasi, dan penulisan draft narasi; "
    "seluruh angka pada laporan dan notebook berasal dari eksekusi dataset asli UCI, bukan data karangan. "
    "Seluruh kode dan hasilnya dapat dijalankan ulang (Run All tanpa error)."
)
r.font.size = Pt(9.5)

# AI usage table
heading(doc, "C. Rincian Penggunaan AI", size=12)

t = doc.add_table(rows=1, cols=5)
t.style = "Table Grid"
t.alignment = WD_TABLE_ALIGNMENT.CENTER
table_borders(t)
hdr = ["No", "Nama Tools AI", "Bagian yang Dibantu", "Bentuk Bantuan / Tujuan Prompt", "Tingkat Ketergantungan"]
widths = [Cm(1.0), Cm(2.6), Cm(4.6), Cm(6.4), Cm(2.2)]
for cell, text, w in zip(t.rows[0].cells, hdr, widths):
    set_cell(cell, text, bold=True, center=True)
    shade(cell, "1F3B57")
    cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    cell.width = w
repeat_header(t.rows[0])

for idx, (tool, part, prompt, level) in enumerate(AI_ROWS, 1):
    row = t.add_row().cells
    for cell, text, w in zip(row, [str(idx), tool, part, prompt, level], widths):
        set_cell(cell, text, center=(cell is row[0]))
        cell.width = w
    if idx % 2 == 0:
        for cell in row:
            shade(cell, "F5F8FB")

body(
    doc,
    "Keterangan tingkat ketergantungan: Tinggi = sebagian besar kode pada bagian tersebut dihasilkan AI dan "
    "mahasiswa memverifikasi hasilnya melalui eksekusi; Sedang = AI menghasilkan kode/narasi yang disunting "
    "dan diperiksa ulang terhadap output; Rendah = materi non-teknis atau pendukung (dokumentasi).",
    size=8.5,
    italic=True,
)

body(
    doc,
    "Pemisahan tanggung jawab: AI menulis kode analisis dan draft interpretasi; mahasiswa bertanggung jawab "
    "memastikan dapat menjelaskan setiap keputusan teknis (deduplikasi timestamp, min_periods moving average, "
    "pemisahan hari lengkap/parsial), memeriksa angka pada narasi terhadap output sel notebook, serta "
    "menjalankan ulang notebook di lingkungan bersih sebelum dikumpulkan.",
    size=9,
)

# screenshots
doc.add_page_break()
heading(doc, "D. Lampiran Screenshot Prompting", size=12, space_before=0)
body(
    doc,
    "Seluruh screenshot berikut diambil dari sesi percakapan dengan platform AI generatif yang sama "
    "(Claude Code) dan menunjukkan prompt yang diajukan serta respons yang diberikan. Urutan mengikuti "
    "alur pengerjaan proyek.",
    size=9,
)

wide_sec = doc.add_section()
wide_section(wide_sec)

for i, (fname, (title, desc)) in enumerate(SHOT_META.items(), 1):
    path = SHOTS / fname
    if not path.exists():
        raise FileNotFoundError(path)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"Gambar {i}. {title}")
    r.bold = True
    r.font.size = Pt(10)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"Berkas: {fname}\n{desc}")
    r.font.size = Pt(8.5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Cm(23.5))

    if i < len(SHOT_META):
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# closing
doc.add_page_break()
heading(doc, "E. Pernyataan Penutup", size=12, space_before=0)
body(
    doc,
    "Deklarasi ini disusun secara jujur dan rinci. Semua bantuan AI yang memengaruhi isi proyek telah "
    "dicantumkan pada Tabel C, dan semua bukti percakapan dilampirkan pada bagian D. Apabila di kemudian "
    "hari ditemukan penggunaan AI lain yang tidak tercatat, saya bersedia mempertanggungjawabkannya sesuai "
    "ketentuan akademik yang berlaku.",
    size=10,
)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(24)
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = p.add_run("........................, 31 Oktober 2026\n\n\n\n")  # kota dikosongkan, bukan ditebak
r.font.size = Pt(10)
r = p.add_run(f"{STUDENT_NAME}\nNIM {STUDENT_NIM}")
r.font.size = Pt(10)
r.bold = True

doc.save(OUT)
print("saved:", OUT, OUT.stat().st_size, "bytes")
