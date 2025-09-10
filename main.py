import os
import csv
import io
from itertools import combinations
from typing import List, Tuple, Dict

from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# =========================
# KONFIGURASI
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8304855655:AAGMmOBEt3gcmeDKwC4PEARhTp-Bc8Fl-JQ"

MIN_SUPPORT_1_4 = 0.30
MIN_SUPPORT_5 = 0.35
MIN_CONFIDENCE = 0.80

GROUPS = [
    ("TOTAL",),
    ("JK1", "JK2"),
    ("UMR1", "UMR2", "UMR3", "UMR4", "UMR5"),
    ("PT1", "PT2", "PT3", "PT4"),
    ("FBJ1", "FBJ2", "FBJ3", "FBJ4"),
    ("JJ1", "JJ2", "JJ3", "JJ4"),
    ("PDB1", "PDB2", "PDB3", "PDB4"),
    ("KJO1", "KJO2"),
    ("PJO1", "PJO2"),
    ("ABJ1", "ABJ2", "ABJ3", "ABJ4", "ABJ5"),
]

DETAILED_LABELS = {
    "JK1": "👩 Jumlah Perempuan (JK1): {JK1}",
    "JK2": "👨 Jumlah Laki-Laki (JK2): {JK2}",
    "UMR1": "🎂 Jumlah usia < 20 Tahun (UMR1): {UMR1}",
    "UMR2": "🧑‍💼 Jumlah usia 20-30 Tahun (UMR2): {UMR2}",
    "UMR3": "👨‍👩‍👧‍👦 Jumlah usia 31-40 Tahun (UMR3): {UMR3}",
    "UMR4": "👴 Jumlah usia 41-50 Tahun (UMR4): {UMR4}",
    "UMR5": "👵 Jumlah usia > 50 Tahun (UMR5): {UMR5}",
    "PT1": "📚 Tamatan SD/Sederajat (PT1): {PT1}",
    "PT2": "🏫 Tamatan SMP/Sederajat (PT2): {PT2}",
    "PT3": "🎓 Tamatan SMA/Sederajat (PT3): {PT3}",
    "PT4": "🎓🎓 Tamatan Diploma/Sarjana (PT4): {PT4}",
    "FBJ1": "📅🔥 Frekuensi Bermain Hampir Setiap Hari (FBJ1): {FBJ1}",
    "FBJ2": "📅 Frekuensi Bermain 2-3 kali/minggu (FBJ2): {FBJ2}",
    "FBJ3": "📆 Frekuensi Bermain 1 kali/minggu (FBJ3): {FBJ3}",
    "FBJ4": "⏳ Frekuensi Bermain <1 kali/minggu (FBJ4): {FBJ4}",
    "JJ1": "🎲 Jenis Judi Togel/Lotere Online (JJ1): {JJ1}",
    "JJ2": "⚽ Jenis Judi Taruhan Olahraga (JJ2): {JJ2}",
    "JJ3": "🃏 Jenis Judi Kasino Online (JJ3): {JJ3}",
    "JJ4": "❓ Jenis Judi Lainnya (JJ4): {JJ4}",
    "PDB1": "💸 Pengeluaran < Rp 500Rb (PDB1): {PDB1}",
    "PDB2": "💰 Pengeluaran Rp 500Rb - Rp 2 Jt (PDB2): {PDB2}",
    "PDB3": "💵 Pengeluaran 2 Jt - 5 Jt (PDB3): {PDB3}",
    "PDB4": "🏦 Pengeluaran > Rp 5 Jt (PDB4): {PDB4}",
    "MK1": "❗ Masalah Keuangan YA (MK1): {MK1}",
    "MK2": "✔️ Masalah Keuangan TIDAK (MK2): {MK2}",
    "FB1": "🙅‍♂️ Frekuensi Bertengkar Tidak Pernah (FB1): {FB1}",
    "FB2": "🤏 Frekuensi Bertengkar Jarang 1-2 Kali/bln (FB2): {FB2}",
    "FB3": "🔥 Frekuensi Bertengkar Sering 1-2 Kali/bln (FB3): {FB3}",
    "FB4": "💥 Frekuensi Bertengkar Hampir Setiap Hari (FB4): {FB4}",
    "KJO1": "🎰❗ Kecanduan Judi Online YA (KJO1): {KJO1}",
    "KJO2": "✔️ Kecanduan Judi Online TIDAK (KJO2): {KJO2}",
    "PJO1": "💔 Perceraian YA (PJO1): {PJO1}",
    "PJO2": "💖 Perceraian TIDAK (PJO2): {PJO2}",
    "ABJ1": "🎰 Kecanduan Bermain Judi Online (ABJ1): {ABJ1}",
    "ABJ2": "❗ Masalah Keuangan dalam Pernikahan (ABJ2): {ABJ2}",
    "ABJ3": "🗣️ Pertengkaran/Komunikasi yang Buruk (ABJ3): {ABJ3}",
    "ABJ4": "⚠ Konflik dan Kekerasan dalam Pernikahan (ABJ4): {ABJ4}",
    "ABJ5": "🕵 Ketidakjujuran Pasangan Akibat Judi Online (ABJ5): {ABJ5}",
}

ITEM_LABELS = {
    "JK1": "👩 JK1",
    "JK2": "👨 JK2",
    "UMR1": "🧒 UMR1",
    "UMR2": "👦 UMR2",
    "UMR3": "👧 UMR3",
    "UMR4": "🧑 UMR4",
    "UMR5": "🧓 UMR5",
    "PT1": "📚 PT1",
    "PT2": "📖 PT2",
    "PT3": "🎓 PT3",
    "PT4": "🎓 PT4",
    "FBJ1": "🎲 FBJ1",
    "FBJ2": "🎰 FBJ2",
    "FBJ3": "🃏 FBJ3",
    "FBJ4": "🎯 FBJ4",
    "JJ1": "🎴 JJ1",
    "JJ2": "⚽ JJ2",
    "JJ3": "🎰 JJ3",
    "JJ4": "🎲 JJ4",
    "PDB1": "💰 PDB1",
    "PDB2": "💵 PDB2",
    "PDB3": "💸 PDB3",
    "PDB4": "🤑 PDB4",
    "MK1": "❌ MK1",
    "MK2": "✔ MK2",
    "FB1": "🤝 FB1",
    "FB2": "🗨 FB2",
    "FB3": "💢 FB3",
    "FB4": "🔥 FB4",
    "KJO1": "🎰 KJO1",
    "KJO2": "✔ KJO2",
    "PJO1": "💔 PJO1",
    "PJO2": "❤️ PJO2",
    "ABJ1": "🎰 ABJ1",
    "ABJ2": "💸 ABJ2",
    "ABJ3": "💢 ABJ3",
    "ABJ4": "⚠ ABJ4",
    "ABJ5": "🕵 ABJ5",
}

# Conversation states (only CSV)
WAITING_CSV = 1

# =========================
# UTILITAS CSV/TXT
# =========================
def export_rows_to_csv(filename: str, header: List[str], rows: List[List[str]]):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

def export_text(filename: str, content: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

# =========================
# VALIDASI INPUT
# =========================
def is_int_nonneg(text: str) -> bool:
    try:
        return int(text) >= 0
    except:
        return False

def validate_group(data: Dict[str, int], group_idx: int) -> Tuple[bool, str]:
    group = GROUPS[group_idx]

    if group == ("TOTAL",):
        return True, ""

    total = data.get("TOTAL", None)
    if total is None:
        return False, "TOTAL belum diisi"

    vals = [data.get(k) for k in group]
    if any(v is None for v in vals):
        return False, "Ada nilai yang belum diisi di grup ini"

    s = sum(vals)

    # ABJ (wajib = PJO1)
    if group == GROUPS[-1]:
        pjo1 = data.get("PJO1")
        if pjo1 is None:
            return False, "PJO1 belum diisi"
        if s != pjo1:
            return False, f"❌ ABJ1–ABJ5 harus = PJO1 ({pjo1}), sekarang={s}"
        return True, ""

    # PJO juga harus = TOTAL
    if group == GROUPS[8]:
        if s != total:
            return False, f"❌ PJO1+PJO2 harus = TOTAL ({total}), sekarang={s}"
        return True, ""

    # Selain itu semua grup harus = TOTAL
    if s != total:
        return False, f"❌ Jumlah {', '.join(group)} harus = TOTAL ({total}), sekarang={s}"
    return True, ""

def validate_all_groups(data: Dict[str, int]) -> Tuple[bool, str]:
    """Validasi semua grup setelah input otomatis CSV."""
    for gi in range(len(GROUPS)):
        ok, msg = validate_group(data, gi)
        if not ok:
            return False, msg
    return True, ""

# =========================
# FORMAT REKAP
# =========================
def format_rekap_text(data: dict) -> str:
    text = "📊 Rekap Data:\n\n"
    for group in GROUPS:
        for key in group:
            if key in DETAILED_LABELS:
                try:
                    text += DETAILED_LABELS[key].format(**data) + "\n"
                except KeyError:
                    text += f"{key}: Data tidak tersedia\n"
            else:
                text += f"{key}: {data.get(key, 'Data tidak tersedia')}\n"
        text += "\n"
    return text

def rekap_rows_csv(d: Dict[str, int]) -> List[List[str]]:
    rows = []
    for g in GROUPS[1:]:
        for k in g:
            rows.append([ITEM_LABELS[k], str(d.get(k, 0))])
    return rows

# =========================
# APRIORI
# =========================
def one_itemset(data: Dict[str, int], min_support: float) -> List[Tuple[Tuple[str, ...], int, float]]:
    total = data["TOTAL"]
    items = [(k, v) for k, v in data.items() if k != "TOTAL"]
    out = []
    for k, v in items:
        s = v / total if total > 0 else 0
        if s >= min_support:
            out.append(((k,), v, s))
    return out

def k_itemset_from_candidates(data: Dict[str, int], candidates: List[Tuple[str, ...]], min_support: float):
    total = data["TOTAL"]
    out = []
    for combo in candidates:
        freq = min(data.get(c, 0) for c in combo)
        support = freq / total if total > 0 else 0
        if support >= min_support:
            out.append((combo, freq, support))
    return out

def apriori_generate_candidates(prev_frequents: List[Tuple[str, ...]], k: int):
    prev_sorted = [tuple(sorted(x)) for x in prev_frequents]
    candidates = set()
    for i in range(len(prev_sorted)):
        for j in range(i + 1, len(prev_sorted)):
            a, b = prev_sorted[i], prev_sorted[j]
            if a[:k - 2] == b[:k - 2]:
                new = tuple(sorted(set(a).union(b)))
                if len(new) == k:
                    all_subfreq = True
                    for sub in combinations(new, k - 1):
                        if tuple(sorted(sub)) not in prev_sorted:
                            all_subfreq = False
                            break
                    if all_subfreq:
                        candidates.add(new)
    return sorted(candidates)

def apriori(data: Dict[str, int], k: int) -> List[Tuple[Tuple[str, ...], int, float]]:
    min_support = MIN_SUPPORT_1_4 if k < 5 else MIN_SUPPORT_5
    if k == 1:
        return one_itemset(data, min_support)
    prev = apriori(data, k - 1)
    prev_freq = [x[0] for x in prev]
    candidates = apriori_generate_candidates(prev_freq, k)
    return k_itemset_from_candidates(data, candidates, min_support)

# =========================
# RULE MINING
# =========================
def generate_rules(
    frequent_itemsets: List[Tuple[Tuple[str, ...], int, float]],
    data: Dict[str, int],
    target: str
) -> List[Tuple[str, str, float, float]]:
    rules = []
    for combo, freq, support in frequent_itemsets:
        if target in combo:
            antecedent = [c for c in combo if c != target]
            if not antecedent:
                continue
            ant_count = min(data.get(a, 0) for a in antecedent)
            confidence = freq / ant_count if ant_count > 0 else 0
            if confidence >= MIN_CONFIDENCE:
                rules.append((
                    " + ".join([ITEM_LABELS.get(a, a) for a in antecedent]),
                    ITEM_LABELS.get(target, target),
                    support,
                    confidence
                ))
    return rules

def interpret_rule(antecedent: str, consequent: str, support: float, confidence: float) -> str:
    return (
        f"📘 Jika seseorang memiliki karakteristik: {antecedent}, maka kemungkinan besar mereka juga "
        f"memiliki karakteristik {consequent}. (Support: {support * 100:.2f}%, Confidence: {confidence * 100:.2f}%)"
    )

# =========================
# HELPERS STATE & DATA
# =========================
def ensure_data(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, int]:
    d = {k: 0 for g in GROUPS for k in g}
    if "data" in context.user_data:
        for k, v in context.user_data["data"].items():
            d[k] = v
    return d

# =========================
# START & RESET
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Kirim CSV (via /input)", callback_data="CSV_HINT")]]
    )
    await update.message.reply_text(
        "👋 Halo! Gunakan perintah /input untuk mengunggah file CSV.\nPerintah lain: /rekap, /apriori1..5, /rules, /reset",
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🗑 Data direset. Ketik /input untuk mulai lagi.", reply_markup=ReplyKeyboardRemove())

# =========================
# REKAP
# =========================
async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = ensure_data(context)
    text = format_rekap_text(d)
    await update.message.reply_text(text)
    export_text("rekap.txt", text)
    await update.message.reply_document(open("rekap.txt", "rb"))
    rows = rekap_rows_csv(d)
    export_rows_to_csv("rekap.csv", ["Item", "Jumlah"], rows)
    await update.message.reply_document(open("rekap.csv", "rb"))

# =========================
# INPUT: CSV (OTOMATIS) — SINGLE FLOW
# =========================
EXPECTED_KEYS = [k for g in GROUPS for k in g]

def parse_csv_bytes(file_bytes: bytes) -> Tuple[bool, Dict[str, int], str]:
    """
    Coba beberapa pola CSV:
    A) Header: Item,Jumlah (baris: JK1,40)
    B) Header: semua kolom (TOTAL,JK1,...) satu baris angka
    C) Tanpa header 2 kolom (JK1,40)
    """
    data: Dict[str, int] = {}
    try:
        s = file_bytes.decode("utf-8-sig")
    except:
        try:
            s = file_bytes.decode("latin-1")
        except:
            return False, {}, "Format file tidak terbaca (encoding)."

    reader = list(csv.reader(io.StringIO(s)))
    if not reader:
        return False, {}, "CSV kosong."

    header = [h.strip() for h in reader[0]]
    lower_header = [h.lower() for h in header]

    # Pola B: header semua kolom
    if set(EXPECTED_KEYS).issubset(set(header)):
        if len(reader) < 2:
            return False, {}, "CSV butuh minimal 2 baris (header + data)."
        values = [c.strip() for c in reader[1]]
        if len(values) < len(header):
            return False, {}, "Baris data kurang kolom."
        for i, h in enumerate(header):
            if h in EXPECTED_KEYS:
                v = values[i] if i < len(values) else "0"
                if not v.isdigit():
                    return False, {}, f"Nilai bukan angka untuk kolom {h}."
                data[h] = int(v)
        for k in EXPECTED_KEYS:
            data.setdefault(k, 0)
        return True, data, ""

    # Pola A/C: dua kolom (Item, Jumlah) dengan/ tanpa header
    start_row = 0
    if len(reader[0]) >= 2 and (lower_header[0] in ("item", "key", "kode") or lower_header[1] in ("jumlah", "value")):
        start_row = 1  # skip header

    tmp: Dict[str, int] = {}
    for r in reader[start_row:]:
        if len(r) < 2:
            if len("".join(r).strip()) == 0:
                continue
            else:
                return False, {}, "Ditemukan baris CSV dengan kolom kurang dari 2."
        k = r[0].strip()
        v = r[1].strip()
        if k not in EXPECTED_KEYS:
            return False, {}, f"Item tidak dikenali: {k}"
        if not v.isdigit():
            return False, {}, f"Nilai bukan angka untuk item {k}: {v}"
        tmp[k] = int(v)

    for k in EXPECTED_KEYS:
        tmp.setdefault(k, 0)

    return True, tmp, ""

async def input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Langsung minta user untuk upload CSV. Tidak ada mode manual."""
    context.user_data["data"] = {}
    await update.message.reply_text(
        "📁 Mode Otomatis (CSV) — Silakan kirim file CSV dengan salah satu format:\n"
        "1) Header dua kolom Item,Jumlah (contoh: JK1,40)\n"
        "2) Header lengkap: TOTAL,JK1,JK2,... dan satu baris angka\n"
        "3) Tanpa header, dua kolom per baris (JK1,40)\n\n"
        "Kirim file sekarang."
    )
    return WAITING_CSV

async def csv_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not (doc.file_name.endswith(".csv") or doc.mime_type in ("text/csv", "application/vnd.ms-excel")):
        await update.message.reply_text("❌ Harap kirim *file CSV* yang valid (ekstensi .csv).")
        return WAITING_CSV

    file = await doc.get_file()
    file_bytes = await file.download_as_bytearray()

    ok, parsed, msg = parse_csv_bytes(bytes(file_bytes))
    if not ok:
        await update.message.reply_text(f"❌ CSV tidak valid: {msg}\nSilakan kirim ulang file CSV yang benar.")
        return WAITING_CSV

    context.user_data["data"] = parsed
    good, vmsg = validate_all_groups(parsed)
    if not good:
        await update.message.reply_text(f"❌ Data tidak valid: {vmsg}\nSilakan perbaiki CSV dan upload lagi.")
        return WAITING_CSV

    await update.message.reply_text("✅ Data CSV berhasil dibaca & divalidasi. Gunakan /rekap untuk melihat ringkasan.")
    return ConversationHandler.END

# =========================
# APRIORI HANDLER (Top 5 di chat)
# =========================
def top_n_itemsets(itemsets: List[Tuple[Tuple[str, ...], int, float]], n: int = 5):
    return sorted(itemsets, key=lambda x: (-x[2], -x[1], "+".join(x[0])))[:n]

async def apriori_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, k: int):
    d = ensure_data(context)
    if d.get("TOTAL", 0) <= 0:
        await update.message.reply_text("❌ TOTAL belum diisi atau 0. Input data dulu via /input.")
        return

    freq_itemsets = apriori(d, k)
    rows = []
    for combo, freq, support in freq_itemsets:
        rows.append([
            " + ".join([ITEM_LABELS.get(c, c) for c in combo]),
            f"{freq}/{d['TOTAL']} = {support:.4f}",
        ])

    best5 = top_n_itemsets(freq_itemsets, 5)
    text_top5 = "\n".join([
        f"{' + '.join([ITEM_LABELS.get(c, c) for c in combo])} → {freq}/{d['TOTAL']} = {support:.4f}"
        for (combo, freq, support) in best5
    ]) or "Tidak ada"

    await update.message.reply_text(f"📊 Top 5 {k}-Itemset:\n{text_top5}")

    export_rows_to_csv(f"apriori{k}.csv", ["Itemset", "Support"], rows)
    export_text(f"apriori{k}.txt", "\n".join([f"{r[0]} | {r[1]}" for r in rows]))
    await update.message.reply_document(open(f"apriori{k}.csv", "rb"))
    await update.message.reply_document(open(f"apriori{k}.txt", "rb"))

    if k == 5:
        rules = generate_rules(freq_itemsets, d, target="PJO1")
        if rules:
            rules_sorted = sorted(rules, key=lambda r: (-r[3], -r[2]))
            best5r = rules_sorted[:5]
            text_rules = "\n\n".join([
                f"Jika {r[0]} → Maka {r[1]} (Support={r[2]:.4f}, Confidence={r[3]:.4f})\n"
                f"{interpret_rule(r[0], r[1], r[2], r[3])}"
                for r in best5r
            ])
            await update.message.reply_text("📊 Rule Mining (Confidence ≥80%) — Top 5:\n" + text_rules)

            text_all = "\n\n".join([
                f"Jika {r[0]} → Maka {r[1]} (Support={r[2]:.4f}, Confidence={r[3]:.4f})\n"
                f"{interpret_rule(r[0], r[1], r[2], r[3])}"
                for r in rules_sorted
            ])
            export_text("rules.txt", f"📊 Rules untuk target {ITEM_LABELS.get('PJO1','PJO1')}:\n\n{text_all}")
            csv_rows = [[r[0], r[1], f"{r[2]:.4f}", f"{r[3]:.4f}"] for r in rules_sorted]
            export_rows_to_csv("rules.csv", ["Antecedent", "Consequent", "Support", "Confidence"], csv_rows)
            await update.message.reply_document(open("rules.txt", "rb"))
            await update.message.reply_document(open("rules.csv", "rb"))

            kb = InlineKeyboardMarkup(
                [[InlineKeyboardButton("✅ Selesai", callback_data="SELESAI")]]
            )
            await update.message.reply_text("Klik tombol di bawah untuk selesai.", reply_markup=kb)
        else:
            await update.message.reply_text("📊 Rule Mining: Tidak ditemukan aturan dengan confidence ≥80%.")

# Wrapper command handlers
async def apriori1(update, context): await apriori_handler(update, context, 1)
async def apriori2(update, context): await apriori_handler(update, context, 2)
async def apriori3(update, context): await apriori_handler(update, context, 3)
async def apriori4(update, context): await apriori_handler(update, context, 4)
async def apriori5(update, context): await apriori_handler(update, context, 5)

# =========================
# /rules (Top 5 di chat + file lengkap + tombol /selesai)
# =========================
async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = ensure_data(context)
    args = context.args
    target = args[0].upper() if args else "PJO1"
    if target not in d or target == "TOTAL":
        await update.message.reply_text("❌ Target tidak valid. Contoh: /rules PJO1")
        return
    if d.get("TOTAL", 0) <= 0:
        await update.message.reply_text("❌ TOTAL belum diisi atau 0. Input data dulu via /input.")
        return

    freq_itemsets = apriori(d, 5)
    rules = generate_rules(freq_itemsets, d, target)

    if not rules:
        await update.message.reply_text(f"📊 Tidak ditemukan aturan asosiasi untuk target {target} dengan confidence ≥80%.")
        return

    rules_sorted = sorted(rules, key=lambda r: (-r[3], -r[2]))

    best5 = rules_sorted[:5]
    preview_text = "\n\n".join([
        f"Jika {r[0]} → Maka {r[1]} (Support={r[2]:.4f}, Confidence={r[3]:.4f})"
        for r in best5
    ])
    await update.message.reply_text(f"📊 Aturan Asosiasi (Top 5) untuk {ITEM_LABELS.get(target, target)}:\n\n{preview_text}")

    text_rules = "\n\n".join([
        f"Jika {r[0]} → Maka {r[1]} (Support={r[2]:.4f}, Confidence={r[3]:.4f})\n"
        f"{interpret_rule(r[0], r[1], r[2], r[3])}"
        for r in rules_sorted
    ])
    export_text("rules.txt", f"📊 Rules untuk target {ITEM_LABELS.get(target, target)}:\n\n{text_rules}")
    csv_rows = [[r[0], r[1], f"{r[2]:.4f}", f"{r[3]:.4f}"] for r in rules_sorted]
    export_rows_to_csv("rules.csv", ["Antecedent", "Consequent", "Support", "Confidence"], csv_rows)
    await update.message.reply_document(open("rules.txt", "rb"))
    await update.message.reply_document(open("rules.csv", "rb"))

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Selesai", callback_data="SELESAI")]])
    await update.message.reply_text("Klik tombol di bawah untuk selesai.", reply_markup=kb)

# =========================
# /selesai (text + voice/audio)
# =========================
SELAMAT_TEXT = (
    "Buat bang amin yang paling serius yang udah bangun bot ini, semangat terus y bang amin "
    "jalanin sidang skripsi nya, lancar terus sidangnya tanpa hambatan, sukses selalu, dan "
    "semoga dapat hasil yang memuaskan seperti yang diharapkan. jaya jaya jaya.....💪"
)

async def selesai_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(SELAMAT_TEXT)
    await try_send_voice(query)

async def selesai_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(SELAMAT_TEXT)
    await try_send_voice(update)

async def try_send_voice(target):
    try:
        from gtts import gTTS  # type: ignore
        tts = gTTS(SELAMAT_TEXT, lang="id")
        mp3_path = "selesai.mp3"
        tts.save(mp3_path)
        if hasattr(target, "message") and target.message:
            await target.message.reply_audio(audio=open(mp3_path, "rb"), title="Semangat Bang Amin!")
        else:
            await target.message.reply_audio(audio=open(mp3_path, "rb"), title="Semangat Bang Amin!")
        return
    except Exception:
        pass

# =========================
# FALLBACK & HELPERS
# =========================
async def ignore_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Perintah tidak dikenali di mode ini. Jika ingin input CSV, ketik /input atau kirim file CSV saat diminta.")

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("input", input_start)],
        states={
            WAITING_CSV: [
                MessageHandler(filters.Document.ALL, csv_receive),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text("Kirim file CSV ya 😊")),
                MessageHandler(filters.COMMAND, ignore_unknown),
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("❌ Dibatalkan. Ketik /input untuk mulai lagi."))],
        name="input_conversation",
        persistent=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(conv)
    app.add_handler(CommandHandler("rekap", rekap))
    app.add_handler(CommandHandler("apriori1", apriori1))
    app.add_handler(CommandHandler("apriori2", apriori2))
    app.add_handler(CommandHandler("apriori3", apriori3))
    app.add_handler(CommandHandler("apriori4", apriori4))
    app.add_handler(CommandHandler("apriori5", apriori5))
    app.add_handler(CommandHandler("rules", rules_cmd))
    app.add_handler(CommandHandler("selesai", selesai_cmd))

    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(selesai_callback, pattern="^SELESAI$"))

    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
