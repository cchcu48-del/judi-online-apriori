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

# =========================
# KONFIGURASI BOT
# =========================
BOT_TOKEN = "7980657967:AAHuu7kfIh8jgaKmf7_sm_XQylSLcVabk-U"

MIN_SUPPORT_1_4 = 0.30
MIN_SUPPORT_5 = 0.35
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
# HANDLER COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Halo, selamat datang di Bot Rekap Data Responden.\n\n"
        "Gunakan perintah berikut:\n\n"
        "📌 /input → Upload file CSV (format biner 42 variabel).\n"
        "📌 /rekap → Lihat rekapitulasi data.\n"
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

    # Hitung total
    total = len(DATA_RESPONDEN)

    # Rekap per variabel
    rekap_count = {var: sum(r[var] for r in DATA_RESPONDEN) for var in VARIABEL}

    # Format Output
    text = f"📊 Rekap Data Responden\n──────────────────────\n📌 Total Responden: {total}\n\n"
    text += f"👤 Jenis Kelamin :\n👩 Perempuan (JK1): {rekap_count['JK1']}\n👨 Laki-Laki (JK2): {rekap_count['JK2']}\n\n"

    text += "🎂 Usia :\n"
    text += f"< 20 Tahun (UMR1): {rekap_count['UMR1']}\n20–30 Tahun (UMR2): {rekap_count['UMR2']}\n"
    text += f"31–40 Tahun (UMR3): {rekap_count['UMR3']}\n41–50 Tahun (UMR4): {rekap_count['UMR4']}\n"
    text += f">50 Tahun (UMR5): {rekap_count['UMR5']}\n\n"

    text += "📚 Pendidikan Terakhir :\n"
    text += f"SD (PDT1): {rekap_count['PDT1']}\nSMP (PDT2): {rekap_count['PDT2']}\n"
    text += f"SMA (PDT3): {rekap_count['PDT3']}\nDiploma/Sarjana (PDT4): {rekap_count['PDT4']}\n\n"

    text += "🎲 Jenis Judi Online :\n"
    text += f"Togel (JJ1): {rekap_count['JJ1']}\nOlahraga (JJ2): {rekap_count['JJ2']}\n"
    text += f"Kasino (JJ3): {rekap_count['JJ3']}\nLainnya (JJ4): {rekap_count['JJ4']}\n\n"

    text += "📅 Frekuensi Bermain :\n"
    text += f"Hampir setiap hari (FBJ1): {rekap_count['FBJ1']}\n"
    text += f"2–3 kali/minggu (FBJ2): {rekap_count['FBJ2']}\n"
    text += f"1 kali/minggu (FBJ3): {rekap_count['FBJ3']}\n"
    text += f"< 1 kali/minggu (FBJ4): {rekap_count['FBJ4']}\n\n"

    text += "⏳ Durasi Bermain :\n"
    text += f"<30 menit (DB1): {rekap_count['DB1']}\n30m–1j (DB2): {rekap_count['DB2']}\n"
    text += f"1–2j (DB3): {rekap_count['DB3']}\n>2j (DB4): {rekap_count['DB4']}\n\n"

~, [11/09/2025 1:10]
text += "💵 Pengeluaran :\n"
    text += f"<500rb (PDB1): {rekap_count['PDB1']}\n500rb–2jt (PDB2): {rekap_count['PDB2']}\n"
    text += f"2jt–5jt (PDB3): {rekap_count['PDB3']}\n>5jt (PDB4): {rekap_count['PDB4']}\n\n"

    text += "❗️ Masalah Keuangan :\n"
    text += f"Ya (MK1): {rekap_count['MK1']}\nTidak (MK2): {rekap_count['MK2']}\n\n"

    text += "🗣 Pertengkaran :\n"
    text += f"Tidak Pernah (PT1): {rekap_count['PT1']}\nJarang (PT2): {rekap_count['PT2']}\n"
    text += f"Sering (PT3): {rekap_count['PT3']}\nHampir setiap hari (PT4): {rekap_count['PT4']}\n\n"

    text += "🎰 Sulit Berhenti :\n"
    text += f"Ya (KJO1): {rekap_count['KJO1']}\nTidak (KJO2): {rekap_count['KJO2']}\n\n"

    text += "💔 Perceraian :\n"
    text += f"Ya (PJO1): {rekap_count['PJO1']}\nTidak (PJO2): {rekap_count['PJO2']}\n\n"

    text += "⚠️ Faktor Perceraian :\n"
    text += f"ABJ1: {rekap_count['ABJ1']}, ABJ2: {rekap_count['ABJ2']}, ABJ3: {rekap_count['ABJ3']}, "
    text += f"ABJ4: {rekap_count['ABJ4']}, ABJ5: {rekap_count['ABJ5']}\n"

    await update.message.reply_text(text)

    # Simpan CSV
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=VARIABEL)
    writer.writeheader()
    writer.writerows(DATA_RESPONDEN)
    csv_buffer.seek(0)

    await update.message.reply_document(
        document=InputFile(io.BytesIO(csv_buffer.getvalue().encode()), filename="rekap_biner.csv")
    )

    # Simpan TXT
    txt_buffer = io.StringIO()
    for idx, row in enumerate(DATA_RESPONDEN, start=1):
        txt_buffer.write(f"RESPONDEN {idx}\n")
        txt_buffer.write(", ".join([f"{k}={v}" for k, v in row.items()]) + "\n\n")
    txt_buffer.seek(0)

    await update.message.reply_document(
        document=InputFile(io.BytesIO(txt_buffer.getvalue().encode()), filename="rekap_biner.txt")
    )

# =========================
# MAIN FUNCTION
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("rekap", rekap))
    app.add_handler(MessageHandler(filters.Document.FileExtension("csv"), input_file))

    print("🤖 Bot berjalan...")
    app.run_polling()

if name == "main":
    main()
