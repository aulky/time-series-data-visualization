"""Build the presentation deck (10 content slides) from "Template Presentasi.pptx".

Fixes over the first draft:
- Slides are reordered explicitly (duplicate_slide appended at the end, deletion shifted indexes).
- Pictures are centred and scaled by each figure's aspect ratio inside reserved boxes.
- Content keeps clear of the template's right-corner art and red band.
- Chip text no longer wraps mid-word; labels are shorter.
- Template logo watermarks are drawn after content so nothing overlaps them.
- Numbers re-checked against the executed notebook.
"""

from __future__ import annotations

import copy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "Template Presentasi.pptx"
WORK = ROOT / "scratch" / "deck"
WORK.mkdir(parents=True, exist_ok=True)
OUT_PPTX = WORK / "presentasi.pptx"
FIG = ROOT / "reports" / "figures"

NAVY = RGBColor(0x0C, 0x18, 0x44)
INK = RGBColor(0x1C, 0x21, 0x20)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CRIMSON = RGBColor(0x8C, 0x0E, 0x12)
MUTED = RGBColor(0x5B, 0x63, 0x70)
PANEL = RGBColor(0xF2, 0xF4, 0xF8)
PANEL_LINE = RGBColor(0xD5, 0xDB, 0xE5)

TITLE_FONT = "Oswald Bold"
BODY_FONT = "Glacial Indifference Bold"
CHIP_FONT = "Nexa Heavy"

SLIDE_W, SLIDE_H = 20.0, 11.25
SAFE_RIGHT = 18.6      # content must stay left of the red corner art
CONTENT_TOP = 2.0
FOOTER_Y = 10.45


# --------------------------------------------------------------- helpers
def delete_slide(prs, index: int) -> None:
    lst = prs.slides._sldIdLst
    slides = list(lst)
    prs.part.drop_rel(slides[index].rId)
    lst.remove(slides[index])


def reorder(prs, wanted, presentation_part) -> None:
    """Move *wanted* slide objects (in order) to the front, keeping any others after them."""
    lst = prs.slides._sldIdLst
    current = list(lst)
    part_to_sld = {presentation_part.related_part(sld.rId).partname: sld for sld in current}
    chosen = [part_to_sld[w.part.partname] for w in wanted]
    rest = [sld for sld in current if sld not in chosen]
    for sld in current:
        lst.remove(sld)
    for sld in chosen + rest:
        lst.append(sld)


def duplicate_slide(prs, index: int):
    source = prs.slides[index]
    blank = next(l for l in prs.slide_layouts if l.name == "Blank")
    new = prs.slides.add_slide(blank)
    for shape in source.shapes:
        new.shapes._spTree.append(copy.deepcopy(shape._element))
    return new


def rewrite(shape, lines) -> None:
    """Replace ALL content of a text frame with the given (text, font, size, bold, color) lines."""
    tf = shape.text_frame
    tf.word_wrap = True
    txBody = tf._txBody
    paragraphs = txBody.findall(qn("a:p"))
    # keep the first paragraph element (carries bodyPr-independent formatting) and copy it for extras
    template_p = paragraphs[0]
    for extra in paragraphs[1:]:
        txBody.remove(extra)
    for i, (text, font, size, bold, color) in enumerate(lines):
        p = template_p if i == 0 else copy.deepcopy(template_p)
        if i > 0:
            txBody.append(p)
        for child in list(p):
            if child.tag in (qn("a:r"), qn("a:br"), qn("a:fld")):
                p.remove(child)
        pPr = p.find(qn("a:pPr"))
        if pPr is not None:
            for child in list(pPr):
                if child.tag in (qn("a:lnSpc"), qn("a:spcBef"), qn("a:spcAft"), qn("a:buNone"), qn("a:buChar")):
                    pPr.remove(child)
        r = OxmlElement("a:r")
        rPr = OxmlElement("a:rPr")
        rPr.set("lang", "id-ID")
        rPr.set("sz", str(int(size * 100)))
        rPr.set("b", "1" if bold else "0")
        solid = OxmlElement("a:solidFill")
        srgb = OxmlElement("a:srgbClr")
        srgb.set("val", "%02X%02X%02X" % (color[0], color[1], color[2]) if isinstance(color, tuple) else str(color))
        solid.append(srgb)
        rPr.append(solid)
        latin = OxmlElement("a:latin")
        latin.set("typeface", font)
        rPr.append(latin)
        r.append(rPr)
        t = OxmlElement("a:t")
        t.text = text
        r.append(t)
        p.append(r)


TEMPLATE_TITLES = {"METODE", "HASIL DAN ANALISIS", "PENDAHULUAN", "KESIMPULAN"}


def set_heading(slide, text: str, size: int = 52) -> None:
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip() in TEMPLATE_TITLES:
            rewrite(shape, [(text, TITLE_FONT, size, True, NAVY)])
            shape.left, shape.top = Inches(0.69), Inches(0.45)
            shape.width, shape.height = Inches(14.5), Inches(0.95)
            return
    raise RuntimeError("heading not found")


def content_slide(prs, heading, n, total, sub=None):
    slide = duplicate_slide(prs, 2)          # template slide 3: title + corner art + top bar only
    set_heading(slide, heading)
    if sub:
        textbox(slide, SAFE_RIGHT - 5.0, 1.32, 5.0, 0.45,
                [(sub, BODY_FONT, 13, False, MUTED)], align=PP_ALIGN.RIGHT)
    for el in list(_sp_tree(slide)):
        if el.tag == qn("p:sp"):
            gf = el.find(".//" + qn("a:solidFill") + "/" + qn("a:srgbClr"))
            geom = el.find(".//" + qn("a:prstGeom"))
            if geom is not None and geom.get("prst") == "rect" and gf is not None \
                    and gf.get("val") == "FFFFFF":
                el.getparent().remove(el)
    textbox(slide, SAFE_RIGHT - 1.6, FOOTER_Y, 1.6, 0.35,
            [(f"{n} / {total}", BODY_FONT, 11, False, MUTED)], align=PP_ALIGN.RIGHT)
    return slide


def textbox(slide, left, top, width, height, lines, align=PP_ALIGN.LEFT,
            anchor=MSO_ANCHOR.TOP, spacing=1.05, gap=6, bullet=None):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    first = True
    for item in lines:
        text, font, size, bold, color = item
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(gap)
        if bullet:
            r = p.add_run()
            r.text = bullet + "  "
            r.font.name = font
            r.font.size = Pt(size)
            r.font.bold = True
            r.font.color.rgb = CRIMSON if color != WHITE else WHITE
        r = p.add_run()
        r.text = text
        r.font.name = font
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
    return box


def bullets(slide, left, top, width, height, items, size=15, color=INK, gap=9):
    return textbox(slide, left, top, width, height,
                   [(t, BODY_FONT, size, False, color) for t in items],
                   bullet="\u25aa", gap=gap)


def chip(slide, left, top, width, height, text, size=13):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top),
                                   Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = NAVY
    shape.line.fill.background()
    shape.shadow.inherit = False
    tf = shape.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.name = CHIP_FONT
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = WHITE
    return shape


def panel(slide, left, top, width, height):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    box.adjustments[0] = 0.05
    box.fill.solid()
    box.fill.fore_color.rgb = PANEL
    box.line.color.rgb = PANEL_LINE
    box.line.width = Pt(1)
    box.shadow.inherit = False
    return box


def kpi(slide, left, top, width, height, value, label, value_size=28):
    box = panel(slide, left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.1)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = value
    r.font.name = TITLE_FONT
    r.font.size = Pt(value_size)
    r.font.bold = True
    r.font.color.rgb = CRIMSON
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    r2.text = label
    r2.font.name = BODY_FONT
    r2.font.size = Pt(11)
    r2.font.color.rgb = MUTED
    return box


def fit_picture(slide, path, left, top, width, height):
    """Insert a picture scaled to fit fully inside the box, centred."""
    pic = slide.shapes.add_picture(str(path), Inches(left), Inches(top), Inches(width))
    scale = min(width / (pic.width / 914400), height / (pic.height / 914400))
    w, h = (pic.width / 914400) * scale, (pic.height / 914400) * scale
    pic.width, pic.height = Inches(w), Inches(h)
    pic.left = Inches(left + (width - w) / 2)
    pic.top = Inches(top + (height - h) / 2)
    pic.line.color.rgb = PANEL_LINE
    pic.line.width = Pt(0.75)
    return pic


def _sp_tree(slide):
    return slide.shapes._spTree


def raise_to_front(slide, element) -> None:
    tree = _sp_tree(slide)
    tree.remove(element)
    tree.append(element)



def restyle_paragraphs(shape, size_first, size_other, space=1, line=1.0):
    """Shrink paragraph spacing on multi-line boxes so they fit the template's slot."""
    for i, p in enumerate(shape.text_frame.paragraphs):
        p.space_before = Pt(0)
        p.space_after = Pt(space)
        p.line_spacing = line
        for r in p.runs:
            r.font.size = Pt(size_first if i == 0 else size_other)


def bring_watermarks_front(slide) -> None:
    """Raise only the thin top bar. Logo/corner art stay behind content (template order)."""
    tree = _sp_tree(slide)
    for el in list(tree):
        if el.tag != qn("p:grpSp"):
            continue
        nv = el.find(qn("p:nvGrpSpPr"))
        name = nv[1].get("name") if nv is not None and nv[1] is not None else ""
        off = nv[0].find(qn("p:off")) if nv is not None else None
        if name == "Group 5" and off is not None and int(off.get("y")) < 300000:
            raise_to_front(slide, el)


# --------------------------------------------------------------- content
prs = Presentation(TEMPLATE)
N_TEMPLATE = len(prs.slides._sldIdLst)   # 11 originals: 0 cover .. 10 closing
TOTAL_PAGES = 12

# ---- cover: keep template geometry, just replace the sample text
cover = prs.slides[0]
for shape in cover.shapes:
    if not shape.has_text_frame:
        continue
    t = shape.text_frame.text
    if t.startswith("FINAL PROJECT VISUALISASI DATA"):
        rewrite(shape, [("MIDTERM PROJECT VISUALISASI DATA", TITLE_FONT, 40, True, WHITE)])
    elif t.startswith("Laporan Proyek Fuzzy"):
        rewrite(shape, [
            ("Time Series Analysis & Visualization", TITLE_FONT, 26, True, WHITE),
            ("Volume Lalu Lintas I-94 (2012-2018)", TITLE_FONT, 26, True, WHITE),
        ])
    elif t.startswith("Anggota"):
        members = [
            "M. Aulia Muzzaki Nugraha (2311102051)",
            "Faqih Abdullah (2311102048)",
            "Muhamad Nasrulloh (2311102044)",
            "Raihan Ramadhan (2311102040)",
            "Bayu Kuncoro Adi (2311102031)",
        ]
        rewrite(shape, [("Anggota:", BODY_FONT, 14, True, INK)] +
                [(f"{i}. {m}", BODY_FONT, 10.5, True, INK) for i, m in enumerate(members, 1)])
        shape.top = Inches(6.70)
        shape.height = Inches(2.30)
        restyle_paragraphs(shape, size_first=14, size_other=10.5, space=1, line=0.95)

# ---- S1 Pendahuluan
s1 = content_slide(prs, "PENDAHULUAN", 1, TOTAL_PAGES, None)
chip(s1, 0.69, 1.75, 2.9, 0.5, "LATAR BELAKANG", size=11)
bullets(s1, 0.69, 2.45, 6.3, 2.9, [
    "Lalu lintas antar-kota berubah menurut jam, hari, dan musim.",
    "Pemantauan per jam memberi deret panjang, tetapi rawan cela data.",
    "Pertanyaan: pola apa yang terbentuk, dan adakah tren panjang?",
], size=14, gap=9)
chip(s1, 0.69, 5.5, 3.3, 0.5, "DATA YANG DIGUNAKAN", size=10)
bullets(s1, 0.69, 6.2, 6.3, 2.9, [
    "UCI Dataset 492: 48.204 observasi per jam (Okt 2012 - Sep 2018)",
    "Interstate 94 arah barat, Minneapolis - St. Paul",
    "Variabel utama: date_time dan traffic_volume",
], size=12.5, gap=7)

fit_picture(s1, FIG / "05_moving_average.png", 7.55, 2.0, 10.75, 5.4)
textbox(s1, 7.55, 7.55, 10.75, 0.4,
        [("Volume per jam, rata-rata harian, dan MA 30 hari (2013-2018).",
          BODY_FONT, 11, False, MUTED)], align=PP_ALIGN.CENTER)
bring_watermarks_front(s1)

# ---- S2 Dataset & sumber
s2 = content_slide(prs, "DATASET & SUMBER", 2, TOTAL_PAGES, "Pendahuluan")
kpis = [
    ("48.204", "observasi per jam"),
    ("9", "kolom (2 utama)"),
    ("11.976", "jam hilang (22,8%)"),
    ("5.445", "timestamp duplikat"),
    ("2", "baris volume = 0"),
]
for i, (v, l) in enumerate(kpis):
    kpi(s2, 0.69 + i * 3.72, CONTENT_TOP, 3.5, 1.55, v, l, value_size=24)

chip(s2, 0.69, 4.05, 2.4, 0.5, "VARIABEL", size=11)
bullets(s2, 0.69, 4.75, 8.3, 4.6, [
    "date_time: waktu observasi per jam, kronologis.",
    "traffic_volume: kendaraan per jam (variabel utama).",
    "Pendukung: holiday, temp, rain_1h, snow_1h, clouds_all, weather_main, weather_description.",
], size=14, gap=9)

chip(s2, 9.5, 4.05, 2.6, 0.5, "KONDISI DATA", size=11)
bullets(s2, 9.5, 4.75, 9.0, 4.6, [
    "11.976 dari 52.551 jam tidak tercatat; terbesar 7.386 jam berturut-turut (2014-2015).",
    "Semua timestamp ganda punya traffic_volume identik, aman diambil satu.",
    "Sumber: archive.ics.uci.edu/dataset/492 (diunduh via ucimlrepo).",
], size=14, gap=9)
panel(s2, 0.69, 7.0, 17.8, 2.35)
chip(s2, 1.0, 7.3, 3.4, 0.45, "TAHAP PREPROCESSING", size=10)
textbox(s2, 4.7, 7.3, 13.4, 1.9, [
    ("Deduplikasi hanya bila traffic_volume identik; flag is_sensor_zero / is_temp_error / is_rain_error; "
     "fitur kalender (hour, day_of_week, is_weekend, month) dan gap_hours. Tidak ada imputasi jam hilang.",
     BODY_FONT, 12.5, False, INK)])
bring_watermarks_front(s2)

# ---- S3 Alur pengolahan
s3 = content_slide(prs, "ALUR PENGOLAHAN", 3, TOTAL_PAGES, "Metode")
steps = [
    ("Validasi", "Tipe data, missing value, duplikasi timestamp, celah waktu, kelengkapan harian."),
    ("Preprocessing", "Deduplikasi terverifikasi, flag sentinel sensor, fitur kalender. Tanpa imputasi."),
    ("Agregasi", "Rata-rata dan total per tanggal pada indeks kalender penuh (hari kosong tetap NaN)."),
    ("Visualisasi", "Line, area, multiple time series (direct labeling), heatmap hari x jam."),
    ("Analisis tren", "Moving average 7 & 30 hari (min_periods per window) + linear fit pembanding."),
]
for i, (title, desc) in enumerate(steps):
    y = 2.05 + i * 1.48
    node = s3.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.9), Inches(y + 0.06), Inches(0.6), Inches(0.6))
    node.fill.solid()
    node.fill.fore_color.rgb = CRIMSON
    node.line.fill.background()
    node.shadow.inherit = False
    node.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    node.text_frame.margin_left = node.text_frame.margin_right = 0
    p = node.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = str(i + 1)
    r.font.name = TITLE_FONT
    r.font.size = Pt(17)
    r.font.bold = True
    r.font.color.rgb = WHITE
    textbox(s3, 1.7, y, 3.1, 0.45, [(title, TITLE_FONT, 17, True, NAVY)])
    textbox(s3, 4.9, y + 0.03, 7.0, 1.2, [(desc, BODY_FONT, 13, False, INK)])

panel(s3, 12.4, 1.95, 6.15, 7.6)
chip(s3, 12.75, 2.2, 1.9, 0.5, "TOOLS", size=12)
bullets(s3, 12.75, 2.95, 5.5, 6.3, [
    "Python 3.12 + Jupyter Notebook",
    "pandas, numpy (resample, rolling)",
    "matplotlib, seaborn",
    "ucimlrepo (dataset resmi UCI 492)",
    "scipy (KDE pada distribusi)",
    "Audit otomatis 52 kriteria",
], size=13.5, gap=14)
bring_watermarks_front(s3)

# ---- S4 Heatmap
s4 = content_slide(prs, "POLA AKTIVITAS", 4, TOTAL_PAGES, "Hasil dan analisis")
fit_picture(s4, FIG / "04_seasonal_heatmap.png", 0.69, 1.95, 12.9, 7.6)
textbox(s4, 0.69, 9.62, 12.9, 0.4,
        [("Rata-rata traffic_volume per hari dan jam (ribuan kendaraan/jam).",
          BODY_FONT, 11, False, MUTED)], align=PP_ALIGN.CENTER)
chip(s4, 13.95, 1.95, 2.6, 0.5, "PENJELASAN", size=11)
bullets(s4, 13.95, 2.65, 4.65, 6.9, [
    "Hari kerja dua puncak: 16:00 dan 07:00.",
    "Sel terpadat Rabu 16:00 = 6.414 kendaraan/jam.",
    "Akhir pekan tanpa puncak pagi.",
    "Sel tersepi Selasa 02:00 = 277 kendaraan/jam.",
    "Setiap sel berisi >= 227 observasi.",
], size=13, gap=10)
bring_watermarks_front(s4)

# ---- S5 Empat visualisasi wajib
s5 = content_slide(prs, "EMPAT VISUALISASI WAJIB", 5, TOTAL_PAGES, "Hasil dan analisis")
fit_picture(s5, FIG / "01_line_plot.png", 0.69, 1.95, 8.75, 3.3)
textbox(s5, 0.69, 5.32, 8.75, 0.35,
        [("Line plot: rata-rata harian; pemadaman data 2014-2015 ditandai.",
          BODY_FONT, 11, False, MUTED)])
fit_picture(s5, FIG / "02_area_plot.png", 0.69, 5.8, 8.75, 3.3)
textbox(s5, 0.69, 9.2, 8.75, 0.6,
        [("Area plot: total harian; hijau hari lengkap, oranye hari parsial (undercount).",
          BODY_FONT, 11, False, MUTED)])

fit_picture(s5, FIG / "03_multiple_time_series.png", 9.75, 1.95, 8.85, 3.55)
textbox(s5, 9.75, 5.58, 8.85, 0.55,
        [("Multiple time series: weekday vs weekend per minggu, direct labeling di ujung garis.",
          BODY_FONT, 11, False, MUTED)])
kpi(s5, 9.75, 6.3, 4.2, 1.5, "3.559", "weekday, mean per jam", value_size=24)
kpi(s5, 14.4, 6.3, 4.2, 1.5, "2.636", "weekend, mean per jam", value_size=24)
chip(s5, 9.75, 8.05, 2.2, 0.5, "CATATAN", size=11)
textbox(s5, 12.2, 8.02, 6.4, 1.6, [
    ("Weekday selalu di atas weekend. Garis terputus = minggu tidak lengkap, bukan lalu lintas nol.",
     BODY_FONT, 11.5, False, INK)])
bring_watermarks_front(s5)

# ---- S6 Moving average
s6 = content_slide(prs, "ANALISIS TREN: MOVING AVERAGE", 6, TOTAL_PAGES, "Hasil dan analisis")
fit_picture(s6, FIG / "05_moving_average.png", 0.69, 1.95, 12.6, 8.3)
textbox(s6, 0.69, 10.32, 12.6, 0.35,
        [("Biru muda = data asli, oranye = MA 7 hari, merah = MA 30 hari.",
          BODY_FONT, 11, False, MUTED)], align=PP_ALIGN.CENTER)
chip(s6, 13.65, 1.95, 4.95, 0.5, "PARAMETER & HASIL", size=11)
bullets(s6, 13.65, 2.65, 4.95, 7.0, [
    "rolling(window, min_periods=window) pada indeks harian.",
    "Standar deviasi: 604 (asli) -> 230 (MA 7) -> 167 (MA 30).",
    "Rentang harian: 4.986 -> 1.650 -> 843.",
    "NaN awal: 6 titik MA 7, 29 titik MA 30.",
    "Lag vs data asli: 3 hari (MA 7), 15 hari (MA 30).",
], size=12.5, gap=9)
bring_watermarks_front(s6)

# ---- S7 Weekday / weekend / tren
s7 = content_slide(prs, "WEEKDAY, WEEKEND & TREN", 7, TOTAL_PAGES, "Hasil dan analisis")
vals = [
    ("3.557", "weekday, mean per jam"),
    ("2.624", "weekend, mean per jam"),
    ("+934", "selisih (+36%)"),
    ("+42", "linear fit / tahun"),
    ("R\u00b2 0,005", "1.198 hari bebas celah"),
]
for i, (v, l) in enumerate(vals):
    kpi(s7, 0.69 + i * 3.58, CONTENT_TOP, 3.4, 1.5, v, l, value_size=23)

chip(s7, 0.69, 4.1, 2.9, 0.5, "BUKTI POLA", size=11)
bullets(s7, 0.69, 4.8, 8.8, 4.0, [
    "Jam 06:00-09:00: 5.250 (weekday) vs 2.383 (weekend).",
    "Porsi jam < 1.000 nyaris sama (21,7% vs 23,7%).",
    "Distribusi bimodal: jam malam dan jam sibuk.",
], size=14, gap=10)
chip(s7, 9.85, 4.1, 2.9, 0.5, "BUKTI TREN", size=11)
bullets(s7, 9.85, 4.8, 8.7, 4.0, [
    "Linear fit 2015-06 s.d. 2018-09: +42 kendaraan/jam per tahun, R\u00b2 0,005.",
    "MA 30 hari datar sepanjang 2015-2018.",
    "Kesimpulan: tidak ada tren jangka panjang yang berarti.",
], size=14, gap=10)
bring_watermarks_front(s7)

# ---- S8 Validasi keandalan
s8 = content_slide(prs, "VALIDASI KEANDALAN", 8, TOTAL_PAGES, "Metode")
fit_picture(s8, FIG / "10_validation_daily_completeness.png", 0.69, 1.95, 12.4, 4.0)
textbox(s8, 0.69, 6.02, 12.4, 0.35,
        [("Jumlah jam tercatat per hari (24 jam = hari lengkap).",
          BODY_FONT, 11, False, MUTED)], align=PP_ALIGN.CENTER)
chip(s8, 0.69, 6.6, 2.8, 0.5, "TEMUAN", size=11)
bullets(s8, 0.69, 7.25, 12.4, 2.7, [
    "1.214 hari lengkap, 646 hari parsial, 330 hari tanpa rekaman.",
    "Hari parsial tidak dipakai untuk total harian maupun tren.",
], size=13, gap=7)
chip(s8, 13.45, 1.95, 3.2, 0.5, "KONTROL MUTU", size=11)
bullets(s8, 13.45, 2.65, 5.15, 7.0, [
    "Nilai traffic_volume dicek sebelum duplikat dibuang.",
    "Tidak ada imputasi; jam hilang tetap NaN.",
    "Sentinel sensor ditandai, tidak dihapus.",
    "SHA-256 data mentah diverifikasi.",
    "Run All dari kernel baru: 0 error.",
], size=12.5, gap=11)
bring_watermarks_front(s8)

# ---- S9 Fitur turunan & cara ukur
s9 = content_slide(prs, "FITUR TURUNAN & CARA UKUR", 9, TOTAL_PAGES, "Metode")
chip(s9, 0.69, 1.95, 3.3, 0.5, "FITUR TURUNAN", size=11)
bullets(s9, 0.69, 2.65, 8.4, 4.6, [
    "hour, day_of_week, is_weekend, month, year",
    "is_holiday (label tercatat hanya pada 00:00)",
    "gap_hours: jarak jam sejak observasi sebelumnya",
    "Flag: is_sensor_zero, is_temp_error, is_rain_error",
], size=14, gap=10)
chip(s9, 9.6, 1.95, 3.4, 0.5, "CARA UKUR", size=11)
bullets(s9, 9.6, 2.65, 8.9, 4.6, [
    "Mean dan median traffic_volume per jam, hari, bulan.",
    "Standar deviasi dan rentang sebelum vs sesudah MA.",
    "numpy.polyfit untuk kemiringan dan R\u00b2.",
    "Jumlah observasi per sel heatmap (minimum 227).",
], size=14, gap=10)
panel(s9, 0.69, 5.9, 18.0, 4.0)
textbox(s9, 1.0, 6.25, 17.4, 3.3, [
    ("Semua interpretasi mengacu ke angka hasil eksekusi notebook. Tidak ada klaim sebab-akibat tanpa "
     "bukti, karena data tidak memuat log kejadian atau catatan perawatan sensor.",
     BODY_FONT, 16, False, INK)])
bring_watermarks_front(s9)

# ---- S10 Kesimpulan (clean base + explicit crimson band, white text)
s10 = content_slide(prs, "KESIMPULAN", 10, TOTAL_PAGES, None)
band = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.72), Inches(12.6), Inches(8.4))
band.fill.solid()
band.fill.fore_color.rgb = CRIMSON
band.line.fill.background()
band.shadow.inherit = False
bullets(s10, 0.9, 2.55, 11.1, 6.9, [
    "Volume I-94 ditentukan kalender: jam dan jenis hari lebih berpengaruh daripada bulan.",
    "Hari kerja dua puncak (16:00 lalu 07:00); akhir pekan puncak siang 13:00.",
    "Weekday 3.557 vs weekend 2.624 kendaraan/jam (+36%).",
    "Tidak ada tren panjang: +42 kendaraan/jam per tahun, R\u00b2 0,005.",
    "MA 30 hari paling halus, tetapi paling banyak membuang titik awal.",
    "22,8% jam hilang: agregasi harian wajib memisahkan hari parsial.",
], size=14.5, color=WHITE, gap=13)
# move band behind the bullets, and keep it above the page background
tree = _sp_tree(s10)
band_el = band._element
texts = [el for el in list(tree) if el.tag == qn("p:sp") and el is not band_el]
tree.remove(band_el)
tree.insert(list(tree).index(texts[-2]) if len(texts) >= 2 else 2, band_el)
textbox(s10, 13.0, 2.55, 5.6, 5.0, [
    ("Ringkasan", TITLE_FONT, 22, True, NAVY),
    ("Empat visualisasi wajib, moving average 7 & 30 hari, dan validasi kualitas data "
     "mendukung satu kesimpulan: pola kalender jauh lebih kuat daripada tren tahunan.",
     BODY_FONT, 13, False, INK),
], bullet=None, gap=10)
bring_watermarks_front(s10)

# ---- closing
closing = duplicate_slide(prs, 10)
for shape in list(closing.shapes):
    if shape.has_text_frame and shape.text_frame.text.strip().startswith("thanks u guys"):
        shape._element.getparent().remove(shape._element)
textbox(closing, 1.12, 7.4, 10.2, 1.2, [
    ("Metro Interstate Traffic Volume  |  UCI Dataset ID 492", BODY_FONT, 16, True, INK),
    ("Terima kasih - pertanyaan dan diskusi dipersilakan.", BODY_FONT, 13, False, MUTED),
], gap=3)

# ---- order + cleanup of unused template slides
slides = list(prs.slides)
content = slides[N_TEMPLATE:-1]
assert len(content) == 10, len(content)
reorder(prs, [slides[0]] + content + [slides[-1]], prs.part)
for _ in range(len(prs.slides._sldIdLst) - 12):
    delete_slide(prs, 12)

prs.save(OUT_PPTX)
print("slides:", len(prs.slides))
for i, s in enumerate(prs.slides, 1):
    heads = [sh.text_frame.text.strip().splitlines()[0] for sh in s.shapes
             if sh.has_text_frame and sh.text_frame.text.strip()]
    print(f"  {i:2d}. {heads[1] if len(heads) > 1 else heads[0]}")
