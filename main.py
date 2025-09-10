import os
import csv
import io
from typing import List, Dict

from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from mlxtend.frequent_patterns import apriori, association_rules
import pandas as pd

# =========================
# KONFIGURASI BOT
# =========================
BOT_TOKEN = "7980657967:AAHuu7kfIh8jgaKmf7_sm_XQylSLcVabk-U"

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
# HANDLER COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Halo, selamat datang di Bot Rekap & Analisis Data Responden.\n\n"
        "Gunakan perintah berikut:\n\n"
        "📌 /input → Upload file CSV (format biner 42 variabel).\n"
        "📌 /rekap → Lihat rekapitulasi data responden.\n"
        "📌 /analyse → Analisis Apriori (itemset & aturan asosiasi).\n"
        "📌 /reset → Hapus semua data responden."
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
        await update.message.reply_text("❌ Belum ada data. Gunakan /input untuk upload CSV.")
        return

    total = len(DATA_RESPONDEN)
    rekap_count = {var: sum(r[var] for r in DATA_RESPONDEN) for var in VARIABEL}

    text = f"📊 *Rekap Data Responden*\n──────────────────────\n📌 Total Responden: *{total}*\n\n"
    text += f"👤 *Jenis Kelamin* :\n👩 Perempuan (JK1): {rekap_count['JK1']}\n👨 Laki-Laki (JK2): {rekap_count['JK2']}\n\n"
    text += "🎂 *Usia* :\n"
    text += f"<20 Tahun (UMR1): {rekap_count['UMR1']}\n20–30 Tahun (UMR2): {rekap_count['UMR2']}\n"
    text += f"31–40 Tahun (UMR3): {rekap_count['UMR3']}\n41–50 Tahun (UMR4): {rekap_count['UMR4']}\n"
    text += f">50 Tahun (UMR5): {rekap_count['UMR5']}\n\n"
    text += "📚 *Pendidikan Terakhir* :\n"
    text += f"SD (PDT1): {rekap_count['PDT1']}\nSMP (PDT2): {rekap_count['PDT2']}\n"
    text += f"SMA (PDT3): {rekap_count['PDT3']}\nDiploma/Sarjana (PDT4): {rekap_count['PDT4']}\n\n"
    text += "... (lanjutan variabel lain) ..."

    await update.message.reply_text(text, parse_mode="Markdown")

    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=VARIABEL)
    writer.writeheader()
    writer.writerows(DATA_RESPONDEN)
    csv_buffer.seek(0)

    await update.message.reply_document(
        document=InputFile(io.BytesIO(csv_buffer.getvalue().encode()), filename="rekap_biner.csv")
    )

async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not DATA_RESPONDEN:
        await update.message.reply_text("❌ Belum ada data. Gunakan /input untuk upload CSV.")
        return

    df = pd.DataFrame(DATA_RESPONDEN)

    # Apriori
    freq_itemsets = apriori(df, min_support=0.30, use_colnames=True, max_len=5)
    freq_itemsets = freq_itemsets[
        ~((freq_itemsets['itemsets'].apply(len) == 5) & (freq_itemsets['support'] < 0.35))
    ]

    rules = association_rules(freq_itemsets, metric="confidence", min_threshold=0.80)

    # Format Output
    text = "📈 *Analisis Frequent Itemset & Aturan Asosiasi*\n"
    text += "──────────────────────\n"
    text += "⚙️ Threshold:\n"
    text += "- Min Support (1–4 item): *0.30*\n"
    text += "- Min Support (5 item): *0.35*\n"
    text += "- Min Confidence: *0.80*\n\n"

    text += "*📊 Frequent Itemset*\n"
    text += "| Itemset | Support |\n|---------|---------|\n"
    for _, row in freq_itemsets.iterrows():
        items = ",".join(list(row['itemsets']))
        text += f"| {items} | {row['support']:.2f} |\n"

    text += "\n*🔗 Association Rules*\n"
    text += "| Rule | Support | Confidence |\n|------|---------|------------|\n"
    for _, row in rules.iterrows():
        antecedents = ",".join(list(row['antecedents']))
        consequents = ",".join(list(row['consequents']))
        text += f"| {{{antecedents}}} → {{{consequents}}} | {row['support']:.2f} | {row['confidence']:.2f} |\n"

    await update.message.reply_text(text, parse_mode="Markdown")

    # Kirim CSV hasil
    csv_buffer = io.StringIO()
    freq_itemsets.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    await update.message.reply_document(
        document=InputFile(io.BytesIO(csv_buffer.getvalue().encode()), filename="frequent_itemsets.csv")
    )

    rules_buffer = io.StringIO()
    rules.to_csv(rules_buffer, index=False)
    rules_buffer.seek(0)
    await update.message.reply_document(
        document=InputFile(io.BytesIO(rules_buffer.getvalue().encode()), filename="association_rules.csv")
    )

# =========================
# MAIN FUNCTION
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("rekap", rekap))
    app.add_handler(CommandHandler("analyse", analyse))
    app.add_handler(MessageHandler(filters.Document.FileExtension("csv"), input_file))

    print("🤖 Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
