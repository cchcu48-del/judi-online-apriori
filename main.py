import os
import csv
import io
from itertools import combinations
from typing import List, Tuple, Dict

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
BOT_TOKEN = "8265856945:AAGLtpVtH4RVzBTEfTT4ZK_GI8nD2z8FQN0"
MIN_SUPPORT = 0.3
MIN_CONFIDENCE = 0.8

# Penyimpanan sementara data upload
DATA: List[Dict[str, int]] = []
VARIABLES: List[str] = []

# =========================
# HELPER FUNCTIONS
# =========================
def load_csv(file_bytes: bytes) -> Tuple[List[Dict[str, int]], List[str]]:
    text = file_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    variables = reader.fieldnames
    data = []
    for row in reader:
        data.append({var: int(row[var]) for var in variables})
    return data, variables


def rekap_data(data: List[Dict[str, int]]) -> Dict[str, int]:
    rekap = {}
    for row in data:
        for k, v in row.items():
            if v == 1:
                rekap[k] = rekap.get(k, 0) + 1
    return rekap


def save_file_csv(filename: str, rows: List[List]):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def save_file_txt(filename: str, lines: List[str]):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_itemsets(data: List[Dict[str, int]], variables: List[str], k: int):
    itemsets = {}
    n = len(data)
    for comb in combinations(variables, k):
        count = sum(all(row[var] == 1 for var in comb) for row in data)
        support = count / n
        if support >= MIN_SUPPORT:
            itemsets[comb] = support
    return itemsets


def generate_rules(frequent_itemsets: Dict[Tuple, float], data: List[Dict[str, int]]):
    rules = []
    n = len(data)
    for itemset, sup in frequent_itemsets.items():
        if len(itemset) < 2:
            continue
        for i in range(1, len(itemset)):
            for antecedent in combinations(itemset, i):
                consequent = tuple(sorted(set(itemset) - set(antecedent)))
                count_ante = sum(all(row[var] == 1 for var in antecedent) for row in data)
                if count_ante == 0:
                    continue
                confidence = sup / (count_ante / n)
                if confidence >= MIN_CONFIDENCE:
                    rules.append((antecedent, consequent, sup, confidence))
    return rules

# =========================
# HANDLER FUNCTIONS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
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


async def input_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DATA, VARIABLES
    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()
    DATA, VARIABLES = load_csv(file_bytes)
    await update.message.reply_text(f"✅ Data berhasil diupload. Total responden: {len(DATA)}")


async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not DATA:
        await update.message.reply_text("⚠️ Upload dulu file CSV dengan /input")
        return
    rec = rekap_data(DATA)
    lines = [f"{k}: {v}" for k, v in rec.items()]
    filename_csv = "rekap_biner.csv"
    filename_txt = "rekap_biner.txt"
    save_file_csv(filename_csv, [["Variabel", "Jumlah"]] + [[k, v] for k, v in rec.items()])
    save_file_txt(filename_txt, lines)
    await update.message.reply_text("📊 Rekapitulasi Data")
    await update.message.reply_document(InputFile(filename_csv))
    await update.message.reply_document(InputFile(filename_txt))


async def apriori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not DATA:
        await update.message.reply_text("⚠️ Upload dulu file CSV dengan /input")
        return
    cmd = update.message.text.replace("/", "")
    k = int(cmd.replace("apriori", ""))
    itemsets = generate_itemsets(DATA, VARIABLES, k)
    sorted_items = sorted(itemsets.items(), key=lambda x: x[1], reverse=True)
    top5 = sorted_items[:5]
    lines = [f"{set(k)} = {v:.2f}" for k, v in top5]

    filename_csv = f"apriori{k}.csv"
    filename_txt = f"apriori{k}.txt"
    save_file_csv(filename_csv, [["Itemset", "Support"]] + [["{"+','.join(k)+"}", v] for k, v in sorted_items])
    save_file_txt(filename_txt, [f"{set(k)} = {v:.2f}" for k, v in sorted_items])

    await update.message.reply_text(f"📊 Top 5 Frequent {k}-Itemset\n" + "\n".join(lines))
    await update.message.reply_document(InputFile(filename_csv))
    await update.message.reply_document(InputFile(filename_txt))


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not DATA:
        await update.message.reply_text("⚠️ Upload dulu file CSV dengan /input")
        return
    all_itemsets = {}
    for k in range(1, 5):
        all_itemsets.update(generate_itemsets(DATA, VARIABLES, k))
    rules_list = generate_rules(all_itemsets, DATA)
    sorted_rules = sorted(rules_list, key=lambda x: x[2], reverse=True)[:5]

    lines = [f"{set(a)} => {set(c)} (sup={s:.2f}, conf={cf:.2f})" for a, c, s, cf in sorted_rules]

    filename_csv = "rules.csv"
    filename_txt = "rules.txt"
    save_file_csv(filename_csv, [["Antecedent", "Consequent", "Support", "Confidence"]] +
                  [["{"+','.join(a)+"}", "{"+','.join(c)+"}", s, cf] for a, c, s, cf in rules_list])
    save_file_txt(filename_txt, [f"{set(a)} => {set(c)} (sup={s:.2f}, conf={cf:.2f})" for a, c, s, cf in rules_list])

    await update.message.reply_text("📑 Top 5 Association Rules\n" + "\n".join(lines))
    await update.message.reply_document(InputFile(filename_csv))
    await update.message.reply_document(InputFile(filename_txt))


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DATA, VARIABLES
    DATA, VARIABLES = [], []
    await update.message.reply_text("✅ Data direset")

# =========================
# MAIN FUNCTION
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rekap", rekap))
    app.add_handler(CommandHandler("apriori1", apriori))
    app.add_handler(CommandHandler("apriori2", apriori))
    app.add_handler(CommandHandler("apriori3", apriori))
    app.add_handler(CommandHandler("apriori4", apriori))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.Document.ALL, input_file))
    app.run_polling()

if __name__ == "__main__":
    main()
