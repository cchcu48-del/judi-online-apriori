import os
import csv
import io
from itertools import combinations
from typing import List, Dict, Tuple

from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# =========================
# KONFIGURASI BOT
# =========================
BOT_TOKEN = "8038423070:AAH3shGNsdn_4C0N166rYRWZ8qhbS_uS9hY"

MIN_SUPPORT = 0.30
MIN_CONFIDENCE = 0.80

# =========================
# VARIABEL
# =========================
VARIABEL = [
    "JK1","JK2",
    "UMR1","UMR2","UMR3","UMR4","UMR5",
    "PDT1","PDT2","PDT3","PDT4",
    "JJ1","JJ2","JJ3","JJ4",
    "FBJ1","FBJ2","FBJ3","FBJ4",
    "DB1","DB2","DB3","DB4",
    "PDB1","PDB2","PDB3","PDB4",
    "MK1","MK2",
    "PT1","PT2","PT3","PT4",
    "KJO1","KJO2",
    "PJO1","PJO2",
    "ABJ1","ABJ2","ABJ3","ABJ4","ABJ5"
]

DATA_RESPONDEN: List[Dict[str, int]] = []

# =========================
# FUNGSI APRIORI
# =========================
def generate_frequent_itemsets(data: List[Dict[str, int]], k: int) -> Dict[Tuple[str], float]:
    total = len(data)
    itemsets = {}

    for row in data:
        aktif = [var for var, val in row.items() if val == 1]
        for combo in combinations(aktif, k):
            combo = tuple(sorted(combo))
            itemsets[combo] = itemsets.get(combo, 0) + 1

    # hitung support
    itemsets = {k: v/total for k, v in itemsets.items() if (v/total) >= MIN_SUPPORT}
    return dict(sorted(itemsets.items(), key=lambda x: x[1], reverse=True))

def generate_rules(data: List[Dict[str, int]]) -> List[Tuple[Tuple[str], Tuple[str], float, float]]:
    total = len(data)
    rules = []

    # kumpulkan semua item aktif
    all_itemsets = {}
    for k in range(1, 5):
        all_itemsets.update(generate_frequent_itemsets(data, k))

    for itemset, sup in all_itemsets.items():
        if len(itemset) < 2:
            continue
        for i in range(1, len(itemset)):
            for antecedent in combinations(itemset, i):
                consequent = tuple(sorted(set(itemset) - set(antecedent)))

                # hitung support antecedent
                count_a = sum(all(r[a] == 1 for a in antecedent) for r in data)
                support_a = count_a / total
                confidence = sup / support_a if support_a > 0 else 0

                if confidence >= MIN_CONFIDENCE:
                    rules.append((antecedent, consequent, sup, confidence))

    return sorted(rules, key=lambda x: x[3], reverse=True)

# =========================
# HANDLER COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Selamat datang di Bot Analisis Responden.\n\n"
        "Perintah yang tersedia:\n"
        "📌 /input → Upload file CSV (42 variabel biner)\n"
        "📌 /rekap → Rekapitulasi data\n"
        "📌 /apriori1 → Frequent 1-itemset\n"
        "📌 /apriori2 → Frequent 2-itemset\n"
        "📌 /apriori3 → Frequent 3-itemset\n"
        "📌 /apriori4 → Frequent 4-itemset\n"
        "📌 /rules → Association Rules\n"
        "📌 /reset → Hapus data"
    )
    await update.message.reply_text(text)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    DATA_RESPONDEN.clear()
    await update.message.reply_text("♻️ Semua data responden berhasil dihapus.")

async def input_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document:
        await update.message.reply_text("❌ Silakan upload file CSV.")
        return

    file = await document.get_file()
    file_bytes = await file.download_as_bytearray()
    file_stream = io.StringIO(file_bytes.decode("utf-8"))
    reader = csv.DictReader(file_stream)

    count = 0
    for row in reader:
        data_row = {var: int(row.get(var, 0)) for var in VARIABEL}
        DATA_RESPONDEN.append(data_row)
        count += 1

    await update.message.reply_text(f"✅ Data berhasil disimpan. {count} responden ditambahkan.")

async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not DATA_RESPONDEN:
        await update.message.reply_text("❌ Belum ada data.")
        return

    total = len(DATA_RESPONDEN)
    rekap_count = {var: sum(r[var] for r in DATA_RESPONDEN) for var in VARIABEL}

    text = f"📊 Rekap Data Responden\n──────────────────────\n📌 Total Responden: {total}\n"
    for var, cnt in rekap_count.items():
        text += f"{var}: {cnt}\n"

    await update.message.reply_text(text)

# =========================
# HANDLER APRIORI
# =========================
async def apriori_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, k: int):
    if not DATA_RESPONDEN:
        await update.message.reply_text("❌ Belum ada data.")
        return

    frequent = generate_frequent_itemsets(DATA_RESPONDEN, k)
    if not frequent:
        await update.message.reply_text(f"❌ Tidak ada frequent {k}-itemset memenuhi min_support.")
        return

    # tampilkan top 5
    top5 = list(frequent.items())[:5]
    text = f"📊 Top 5 Frequent {k}-Itemset\n──────────────────────\n"
    for i, (items, sup) in enumerate(top5, 1):
        text += f"{i}. {{{','.join(items)}}} = {sup:.2f}\n"
    await update.message.reply_text(text)

    # simpan ke CSV
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["Itemset", "Support"])
    for items, sup in frequent.items():
        writer.writerow(["{" + ",".join(items) + "}", f"{sup:.2f}"])
    csv_buffer.seek(0)

    await update.message.reply_document(
        document=InputFile(io.BytesIO(csv_buffer.getvalue().encode()), filename=f"apriori{k}.csv")
    )

    # simpan ke TXT
    txt_buffer = io.StringIO()
    for items, sup in frequent.items():
        txt_buffer.write(f"{{{','.join(items)}}} = {sup:.2f}\n")
    txt_buffer.seek(0)

    await update.message.reply_document(
        document=InputFile(io.BytesIO(txt_buffer.getvalue().encode()), filename=f"apriori{k}.txt")
    )

async def apriori1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await apriori_handler(update, context, 1)

async def apriori2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await apriori_handler(update, context, 2)

async def apriori3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await apriori_handler(update, context, 3)

async def apriori4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await apriori_handler(update, context, 4)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not DATA_RESPONDEN:
        await update.message.reply_text("❌ Belum ada data.")
        return

    rule_list = generate_rules(DATA_RESPONDEN)
    if not rule_list:
        await update.message.reply_text("❌ Tidak ada rules memenuhi min_support & min_confidence.")
        return

    # tampilkan top 5
    top5 = rule_list[:5]
    text = "📑 Top 5 Association Rules\n──────────────────────\n"
    for i, (ante, cons, sup, conf) in enumerate(top5, 1):
        text += f"{i}. {{{','.join(ante)}}} => {{{','.join(cons)}}} (sup={sup:.2f}, conf={conf:.2f})\n"
    await update.message.reply_text(text)

    # simpan CSV
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["Antecedent", "Consequent", "Support", "Confidence"])
    for ante, cons, sup, conf in rule_list:
        writer.writerow(["{" + ",".join(ante) + "}", "{" + ",".join(cons) + "}", f"{sup:.2f}", f"{conf:.2f}"])
    csv_buffer.seek(0)

    await update.message.reply_document(
        document=InputFile(io.BytesIO(csv_buffer.getvalue().encode()), filename="rules.csv")
    )

    # simpan TXT
    txt_buffer = io.StringIO()
    for ante, cons, sup, conf in rule_list:
        txt_buffer.write(f"{{{','.join(ante)}}} => {{{','.join(cons)}}} (sup={sup:.2f}, conf={conf:.2f})\n")
    txt_buffer.seek(0)

    await update.message.reply_document(
        document=InputFile(io.BytesIO(txt_buffer.getvalue().encode()), filename="rules.txt")
    )

# =========================
# MAIN FUNCTION
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("rekap", rekap))
    app.add_handler(CommandHandler("apriori1", apriori1))
    app.add_handler(CommandHandler("apriori2", apriori2))
    app.add_handler(CommandHandler("apriori3", apriori3))
    app.add_handler(CommandHandler("apriori4", apriori4))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(MessageHandler(filters.Document.FileExtension("csv"), input_file))

    print("🤖 Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
