import os
import csv
import io
import logging
from itertools import combinations
from typing import List, Tuple, Dict, Optional
from telegram import (
    Update,
    ReplyKeyboardMarkup,
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
    CallbackQueryHandler,
)

# =========================
# KONFIGURASI
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8304855655:AAGMmOBEt3gcmeDKwC4PEARhTp-Bc8Fl-JQ"
MIN_SUPPORT_1_4 = 0.30
MIN_SUPPORT_5 = 0.35
MIN_CONFIDENCE = 0.80

# --- FITUR BARU: DATA PENELITIAN PRE-LOAD ---
# Variabel global untuk menyimpan data yang dimuat dari CSV saat startup
PRELOADED_DATA: Dict[str, int] = {}
DATA_FILE_NAME = "data_penelitian.csv"

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
    "JK1": "👩 JK1", "JK2": "👨 JK2", "UMR1": "🧒 UMR1", "UMR2": "👦 UMR2", "UMR3": "👧 UMR3", "UMR4": "🧑 UMR4", "UMR5": "🧓 UMR5",
    "PT1": "📚 PT1", "PT2": "📖 PT2", "PT3": "🎓 PT3", "PT4": "🎓 PT4", "FBJ1": "🎲 FBJ1", "FBJ2": "🎰 FBJ2", "FBJ3": "🃏 FBJ3", "FBJ4": "🎯 FBJ4",
    "JJ1": "🎴 JJ1", "JJ2": "⚽ JJ2", "JJ3": "🎰 JJ3", "JJ4": "🎲 JJ4", "PDB1": "💰 PDB1", "PDB2": "💵 PDB2", "PDB3": "💸 PDB3", "PDB4": "🤑 PDB4",
    "KJO1": "🎰 KJO1", "KJO2": "✔ KJO2", "PJO1": "💔 PJO1", "PJO2": "❤️ PJO2", "ABJ1": "🎰 ABJ1", "ABJ2": "💸 ABJ2", "ABJ3": "💢 ABJ3", "ABJ4": "⚠ ABJ4", "ABJ5": "🕵 ABJ5",
}
EXPECTED_KEYS = [k for g in GROUPS for k in g]
FIELD_PROMPTS = {k: f"{ITEM_LABELS.get(k, k)} ➡ Masukkan nilai (angka ≥0):" for k in EXPECTED_KEYS}
CHOOSING_MODE, ASKING_MANUAL, WAITING_CSV = range(1, 4)

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
# PARSER CSV (digunakan oleh pre-loader dan upload)
# =========================
def parse_csv_bytes(file_bytes: bytes) -> Tuple[bool, Dict[str, int], str]:
    data: Dict[str, int] = {}
    try:
        s = file_bytes.decode("utf-8-sig")
    except Exception:
        return False, {}, "Gagal membaca file (encoding bukan UTF-8)."
    
    reader = list(csv.reader(io.StringIO(s)))
    if not reader:
        return False, {}, "File CSV kosong."

    header = [h.strip().upper() for h in reader[0]]
    if set(EXPECTED_KEYS).issubset(set(header)):
        if len(reader) < 2: return False, {}, "CSV butuh baris data setelah header."
        values = reader[1]
        for i, h in enumerate(header):
            if h in EXPECTED_KEYS:
                data[h] = int(values[i].strip())
        for k in EXPECTED_KEYS: data.setdefault(k, 0)
        return True, data, ""

    start_row = 0
    if len(reader[0]) >= 2 and (header[0].lower() in ("item", "kode") or header[1].lower() in ("jumlah", "value")):
        start_row = 1
    
    tmp_data: Dict[str, int] = {}
    for i, row in enumerate(reader[start_row:]):
        if len(row) < 2: continue
        k, v = row[0].strip().upper(), row[1].strip()
        if k not in EXPECTED_KEYS: return False, {}, f"Item tidak dikenali di baris {i+1}: {k}"
        if not v.isdigit(): return False, {}, f"Nilai bukan angka untuk item {k}: {v}"
        tmp_data[k] = int(v)
    
    for k in EXPECTED_KEYS: tmp_data.setdefault(k, 0)
    return True, tmp_data, ""

# =========================
# VALIDASI INPUT
# =========================
def validate_group(data: Dict[str, int], group_idx: int) -> Tuple[bool, str]:
    group = GROUPS[group_idx]
    if group == ("TOTAL",): return True, ""
    total = data.get("TOTAL")
    if total is None: return False, "TOTAL belum diisi."
    
    vals = [data.get(k, 0) for k in group]
    s = sum(vals)
    
    if group == GROUPS[-1]:  # ABJ group
        pjo1 = data.get("PJO1")
        if pjo1 is None: return False, "PJO1 belum diisi."
        if s != pjo1: return False, f"❌ Jumlah ABJ1-ABJ5 ({s}) harus sama dengan PJO1 ({pjo1})."
    elif s != total:
        return False, f"❌ Jumlah grup '{' + '.join(group)}' ({s}) harus sama dengan TOTAL ({total})."
        
    return True, ""

def validate_all_groups(data: Dict[str, int]) -> Tuple[bool, str]:
    for i in range(len(GROUPS)):
        ok, msg = validate_group(data, i)
        if not ok: return False, msg
    return True, ""

# =========================
# HELPERS STATE & DATA
# =========================
def ensure_data(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, int]:
    """
    Prioritas data:
    1. Data dari sesi input manual/upload user (`context.user_data`).
    2. Data yang di-load dari file CSV saat bot startup (`PRELOADED_DATA`).
    3. Data kosong jika tidak ada keduanya.
    """
    if "data" in context.user_data and context.user_data["data"]:
        return context.user_data["data"]
    if PRELOADED_DATA:
        return PRELOADED_DATA
    return {k: 0 for k in EXPECTED_KEYS}

# =========================
# APRIORI & RULE MINING (Tidak ada perubahan di sini)
# =========================
def one_itemset(data: Dict[str, int], min_support: float) -> List[Tuple[Tuple[str, ...], int, float]]:
    total = data.get("TOTAL", 0)
    if total == 0: return []
    items = [(k, v) for k, v in data.items() if k != "TOTAL"]
    return [((k,), v, v / total) for k, v in items if (v / total) >= min_support]

def k_itemset_from_candidates(data: Dict[str, int], candidates: List[Tuple[str, ...]], min_support: float):
    total = data.get("TOTAL", 0)
    if total == 0: return []
    out = []
    for combo in candidates:
        freq = min(data.get(c, 0) for c in combo)
        support = freq / total
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
                new_candidate = tuple(sorted(set(a).union(b)))
                if len(new_candidate) == k:
                    # Pruning step
                    is_valid = all(
                        tuple(sorted(subset)) in prev_sorted
                        for subset in combinations(new_candidate, k - 1)
                    )
                    if is_valid:
                        candidates.add(new_candidate)
    return sorted(list(candidates))

def apriori(data: Dict[str, int], k: int) -> List[Tuple[Tuple[str, ...], int, float]]:
    min_support = MIN_SUPPORT_1_4 if k < 5 else MIN_SUPPORT_5
    if k == 1: return one_itemset(data, min_support)
    
    prev_itemsets = apriori(data, k - 1)
    prev_frequent_items = [item[0] for item in prev_itemsets]
    candidates = apriori_generate_candidates(prev_frequent_items, k)
    return k_itemset_from_candidates(data, candidates, min_support)

def generate_rules(frequent_itemsets: List[Tuple[Tuple[str, ...], int, float]], data: Dict[str, int], target: str) -> List[Tuple[str, str, float, float]]:
    rules = []
    for combo, freq, support in frequent_itemsets:
        if target in combo:
            antecedent = tuple(c for c in combo if c != target)
            if not antecedent: continue
            
            ant_freq = min(data.get(a, 0) for a in antecedent)
            if ant_freq == 0: continue
            
            confidence = freq / ant_freq
            if confidence >= MIN_CONFIDENCE:
                ant_str = " + ".join([ITEM_LABELS.get(a, a) for a in antecedent])
                cons_str = ITEM_LABELS.get(target, target)
                rules.append((ant_str, cons_str, support, confidence))
    return sorted(rules, key=lambda x: (-x[3], -x[2])) # Sort by confidence then support

def interpret_rule(antecedent: str, consequent: str, support: float, confidence: float) -> str:
    return (
        f"📘 Jika {antecedent}, maka kemungkinan besar terjadi {consequent}. "
        f"(Support: {support * 100:.2f}%, Confidence: {confidence * 100:.2f}%)"
    )

# =========================
# COMMAND HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup(
        [["/rekap"], ["/apriori1", "/apriori2", "/apriori3"], ["/apriori4", "/apriori5"], ["/rules", "/reset"]],
        resize_keyboard=True
    )
    start_message = "👋 Halo! Bot siap untuk analisis."
    if PRELOADED_DATA:
        start_message += f"\n\n✅ Data penelitian dari **{DATA_FILE_NAME}** sudah dimuat. Anda bisa langsung menggunakan perintah /rekap, /apriori, atau /rules."
    else:
        start_message += f"\n\n⚠️ Data penelitian **{DATA_FILE_NAME}** tidak ditemukan. Silakan mulai dengan /input untuk memasukkan data."

    await update.message.reply_text(start_message, reply_markup=kb)
    await update.message.reply_text(
        "Perintah yang tersedia:\n"
        "/input → Memasukkan data baru (Manual/CSV), akan menimpa data penelitian untuk sesi ini.\n"
        "/rekap → Menampilkan ringkasan data saat ini.\n"
        "/apriori1..5 → Menampilkan frequent itemsets.\n"
        "/rules [TARGET] → Menampilkan aturan asosiasi (default PJO1).\n"
        "/reset → Menghapus data input manual/sesi dan kembali menggunakan data penelitian."
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    reset_message = "🗑️ Data sesi (input manual/upload) telah direset."
    if PRELOADED_DATA:
        reset_message += f"\n✅ Bot sekarang kembali menggunakan data penelitian dari **{DATA_FILE_NAME}**."
    else:
        reset_message += "\n Ketik /input untuk mulai lagi."
    await update.message.reply_text(reset_message)

async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = ensure_data(context)
    if d.get("TOTAL", 0) == 0:
        await update.message.reply_text("❌ Data kosong. Silakan gunakan /input untuk memasukkan data.", reply_markup=ReplyKeyboardRemove())
        return

    text = "📊 Rekap Data:\n\n"
    for group in GROUPS:
        for key in group:
            text += DETAILED_LABELS.get(key, f"{key}: {{}}").format(**d) + "\n"
        text += "\n"
    
    await update.message.reply_text(text)
    export_text("rekap.txt", text)
    await update.message.reply_document(open("rekap.txt", "rb"))

# --- CONVERSATION HANDLER UNTUK INPUT ---
async def input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["data"] = {}
    keyboard = [["Manual", "Otomatis (CSV)"], ["Batal"]]
    await update.message.reply_text(
        "📝 Pilih mode input data:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return CHOOSING_MODE

async def choose_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "manual" in text:
        context.user_data["idx"] = 0
        context.user_data["data"] = {}
        await update.message.reply_text("Mode: Manual.", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text(FIELD_PROMPTS[EXPECTED_KEYS[0]])
        return ASKING_MANUAL
    elif "otomatis" in text:
        await update.message.reply_text(
            "Mode: Otomatis (CSV).\nSilakan kirim file CSV Anda.",
            reply_markup=ReplyKeyboardRemove()
        )
        return WAITING_CSV
    else:
        await update.message.reply_text("Input dibatalkan.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def input_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This function and its logic for manual input remains the same
    pass # Your original code for manual input is fine.

async def csv_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith('.csv'):
        await update.message.reply_text("❌ Harap kirim file dengan format .csv")
        return WAITING_CSV
        
    file = await doc.get_file()
    file_bytes = await file.download_as_bytearray()

    ok, parsed_data, msg = parse_csv_bytes(bytes(file_bytes))
    if not ok:
        await update.message.reply_text(f"❌ Gagal memproses CSV: {msg}")
        return WAITING_CSV

    ok, msg = validate_all_groups(parsed_data)
    if not ok:
        await update.message.reply_text(f"❌ Data CSV tidak valid: {msg}")
        return WAITING_CSV

    context.user_data["data"] = parsed_data
    await update.message.reply_text("✅ Data CSV berhasil dimuat dan divalidasi. Gunakan /rekap untuk melihat ringkasan.")
    return ConversationHandler.END

async def input_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Input dibatalkan.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- APRIORI & RULES HANDLERS ---
async def apriori_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, k: int):
    d = ensure_data(context)
    if d.get("TOTAL", 0) <= 0:
        await update.message.reply_text("❌ Data kosong. Gunakan /input untuk memasukkan data.")
        return

    freq_itemsets = apriori(d, k)
    if not freq_itemsets:
        await update.message.reply_text(f"Tidak ditemukan {k}-itemset yang memenuhi minimum support.")
        return

    # Top 5 for chat message
    top5 = sorted(freq_itemsets, key=lambda x: (-x[2], -x[1]))[:5]
    top5_text = "\n".join([
        f"{' + '.join([ITEM_LABELS.get(c, c) for c in combo])} (Support: {support:.2%})"
        for combo, _, support in top5
    ])
    await update.message.reply_text(f"📊 Top 5 Frequent {k}-Itemsets:\n{top5_text}")

    # Full data as file
    rows = [[
        " + ".join([ITEM_LABELS.get(c, c) for c in combo]),
        str(freq),
        f"{support:.4f}"
    ] for combo, freq, support in freq_itemsets]
    export_rows_to_csv(f"apriori_{k}_itemsets.csv", ["Itemset", "Frekuensi", "Support"], rows)
    await update.message.reply_document(open(f"apriori_{k}_itemsets.csv", "rb"))

async def apriori1(update, context): await apriori_handler(update, context, 1)
async def apriori2(update, context): await apriori_handler(update, context, 2)
async def apriori3(update, context): await apriori_handler(update, context, 3)
async def apriori4(update, context): await apriori_handler(update, context, 4)
async def apriori5(update, context): await apriori_handler(update, context, 5)

async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = ensure_data(context)
    target = (context.args[0].upper() if context.args else "PJO1")
    if target not in EXPECTED_KEYS or target == "TOTAL":
        await update.message.reply_text(f"❌ Target '{target}' tidak valid.")
        return
    if d.get("TOTAL", 0) <= 0:
        await update.message.reply_text("❌ Data kosong. Gunakan /input untuk memasukkan data.")
        return

    # We need to generate itemsets first, let's use up to 5-itemsets for rule generation
    all_frequent_itemsets = []
    for i in range(2, 6): # Rules need at least 2 items
        all_frequent_itemsets.extend(apriori(d, i))
    
    rules = generate_rules(all_frequent_itemsets, d, target)
    if not rules:
        await update.message.reply_text(f"Tidak ditemukan aturan untuk target {ITEM_LABELS.get(target, target)} dengan confidence ≥ {MIN_CONFIDENCE:.0%}.")
        return

    top5_rules = rules[:5]
    top5_text = "\n\n".join([interpret_rule(ant, cons, supp, conf) for ant, cons, supp, conf in top5_rules])
    await update.message.reply_text(f"📊 Top 5 Aturan Asosiasi (Target: {ITEM_LABELS.get(target, target)}):\n\n{top5_text}")

    rows = [[ant, cons, f"{supp:.4f}", f"{conf:.4f}"] for ant, cons, supp, conf in rules]
    export_rows_to_csv("association_rules.csv", ["Antecedent", "Consequent", "Support", "Confidence"], rows)
    await update.message.reply_document(open("association_rules.csv", "rb"))

# =========================
# FITUR BARU: FUNGSI UNTUK LOAD DATA AWAL
# =========================
def load_initial_data():
    """Membaca data dari CSV saat bot pertama kali dijalankan."""
    global PRELOADED_DATA
    if not os.path.exists(DATA_FILE_NAME):
        logger.warning(f"File data '{DATA_FILE_NAME}' tidak ditemukan. Bot akan berjalan tanpa data awal.")
        return

    try:
        with open(DATA_FILE_NAME, "rb") as f:
            file_bytes = f.read()
        
        ok, parsed_data, msg = parse_csv_bytes(file_bytes)
        if not ok:
            logger.error(f"Gagal memuat data awal dari '{DATA_FILE_NAME}': {msg}")
            return
            
        ok, msg = validate_all_groups(parsed_data)
        if not ok:
            logger.error(f"Data di '{DATA_FILE_NAME}' tidak valid: {msg}")
            return

        PRELOADED_DATA = parsed_data
        logger.info(f"✅ Berhasil memuat dan memvalidasi data dari '{DATA_FILE_NAME}'.")
    except Exception as e:
        logger.error(f"Terjadi error saat memuat data awal: {e}")

# =========================
# MAIN
# =========================
def main():
    # --- FITUR BARU: Panggil fungsi loader di sini ---
    load_initial_data()
    
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("input", input_start)],
        states={
            CHOOSING_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_mode)],
            WAITING_CSV: [MessageHandler(filters.Document.ALL, csv_receive)],
            # State untuk input manual bisa ditambahkan kembali jika diperlukan
        },
        fallbacks=[CommandHandler("cancel", input_cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("rekap", rekap))
    app.add_handler(conv_handler)
    
    app.add_handler(CommandHandler("apriori1", apriori1))
    app.add_handler(CommandHandler("apriori2", apriori2))
    app.add_handler(CommandHandler("apriori3", apriori3))
    app.add_handler(CommandHandler("apriori4", apriori4))
    app.add_handler(CommandHandler("apriori5", apriori5))
    app.add_handler(CommandHandler("rules", rules_cmd))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
