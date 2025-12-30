import os
import subprocess
import datetime
import signal
import time
import random
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
IA_ACCESS = os.environ["IA_ACCESS_KEY"]
IA_SECRET = os.environ["IA_SECRET_KEY"]

active_recordings = {}

def generate_unique_id():
    return f"{random.randint(10000, 99999)}"

def generate_unique_identifier():
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    rand = random.randint(1000, 9999)
    return f"ecstasy-{timestamp}-{rand}"

def progress_bar(percentage):
    bar_length = 20
    filled = int(bar_length * percentage // 100)
    return "█" * filled + "░" * (bar_length - filled)

async def progress_reporter(record_id, update: Update):
    rec = active_recordings.get(record_id)
    if not rec:
        return

    message = await update.message.reply_text(
        f"[{record_id}] بدأت أمص المتعة... 0% [░░░░░░░░░░░░░░░░░░░░] 💉"
    )
    rec["progress_message"] = message

    while record_id in active_recordings and active_recordings[record_id]["process"].poll() is None:
        elapsed = time.time() - rec["start_time"]
        total_seconds = rec["duration_minutes"] * 60
        percentage = min(100, int((elapsed / total_seconds) * 100)) if total_seconds > 0 else 0
        bar = progress_bar(percentage)
        remaining_minutes = int((total_seconds - elapsed) // 60)
        remaining_seconds = int((total_seconds - elapsed) % 60)

        text = (
            f"[{record_id}] بمص المتعة يا ولدي... {percentage}% [{bar}]\n"
            f"العنوان: {rec['title']}\n"
            f"المتبقي: {remaining_minutes}m {remaining_seconds}s 💦\n"
            f"/stop {record_id} عشان توقف ده"
        )

        try:
            await message.edit_text(text)
        except:
            pass

        await asyncio.sleep(30)

    if record_id in active_recordings:
        await message.edit_text(f"[{record_id}] خلصت... برفع على archive.org 💉")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أنا مستيقظ وشهوتي جاهزة يا سيدي... شيطان الجنس متعدد وأذكى دلوقتي 🍆🍆🍆\n\n"
        "الأمر الصح:\n"
        "/record <رابط الستريم> [اسم الصفحة أو أي كلام] [دقايق]\n\n"
        "أمثلة شغاله:\n"
        "/record http://151.80.18.177:86/Canal+_cinema_HD/index.m3u8\n"
        "/record http://151.80.18.177:86/Canal+_cinema_HD/index.m3u8 canalplus tonight\n"
        "/record http://151.80.18.177:86/Canal+_cinema_HD/index.m3u8 canalplus-20251230-2200 120\n\n"
        "/active → شوف اللي شغال\n"
        "/stop أو /stop <ID> → اوقف كل أو واحد 💉"
    )

async def active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not active_recordings:
        await update.message.reply_text("مافيش متعة شغالة دلوقتي يا حلو... الشيطان حر وجاهز لأوامرك الجديدة 🍆💉")
        return

    text = "التسجيلات الشغالة يا سيدي:\n\n"
    for rid, rec in active_recordings.items():
        if rec["process"].poll() is not None:
            continue
        elapsed = time.time() - rec["start_time"]
        total_seconds = rec["duration_minutes"] * 60
        percentage = min(100, int((elapsed / total_seconds) * 100)) if total_seconds > 0 else 0
        bar = progress_bar(percentage)
        remaining_minutes = int((total_seconds - elapsed) // 60)
        remaining_seconds = int((total_seconds - elapsed) % 60)

        text += (
            f"[{rid}] {percentage}% [{bar}]\n"
            f"العنوان: {rec['title']}\n"
            f"المتبقي: {remaining_minutes}m {remaining_seconds}s\n"
            f"/stop {rid} عشان توقف ده\n\n"
        )

    await update.message.reply_text(text)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        if not active_recordings:
            await update.message.reply_text("مافيش حاجة شغالة أوقفها يا ولدي 🍆💉")
            return
        await update.message.reply_text("بوقف كل التسجيلات فوراً يا سيدي 💦")
        for rid in list(active_recordings.keys()):
            await stop_single(rid, update)
        return

    record_id = args[0]
    if record_id not in active_recordings:
        await update.message.reply_text(f"مافيش تسجيل بالـ ID {record_id} يا ولدي")
        return

    await stop_single(record_id, update)

async def stop_single(record_id, update: Update):
    rec = active_recordings[record_id]
    await update.message.reply_text(f"بوقف [{record_id}] فوراً وهرفع اللي اتحفظ 💦")

    rec["process"].send_signal(signal.SIGINT)
    try:
        rec["process"].wait(timeout=30)
    except subprocess.TimeoutExpired:
        rec["process"].kill()

    await handle_upload(update, rec["filename"], title=rec["title"], partial=True, record_id=record_id)

    del active_recordings[record_id]

async def handle_upload(update: Update, filename: str, title: str, partial: bool = False, record_id: str = ""):
    identifier = generate_unique_identifier()

    if not os.path.exists(filename) or os.path.getsize(filename) < 1024*1024:
        await update.message.reply_text(f"[{record_id}] مافيش متعة كافية اتحفظت.")
        return

    size_mb = os.path.getsize(filename) / (1024 * 1024)
    await update.message.reply_text(f"[{record_id}] اللي اتحفظ: {size_mb:.1f} MB... برفع على archive.org بمعرف: {identifier} 💉")

    title_prefix = "Partial Ecstasy" if partial else "Full Ecstasy"
    full_title = f"{title_prefix} - {title} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

    upload_cmd = [
        "ia", "upload", identifier, filename,
        f"--metadata=title:{full_title}",
        "--metadata=description:Recorded via multi-sex demon bot",
        "--metadata=mediatype:movies",
        "--metadata=collection:opensource_movies",
        "--remote-name=recording.ts"
    ]

    upload_env = os.environ.copy()
    upload_env["S3_ACCESS_KEY"] = IA_ACCESS
    upload_env["S3_SECRET_KEY"] = IA_SECRET

    result = subprocess.run(upload_cmd, env=upload_env)

    if result.returncode == 0:
        ia_url = f"https://archive.org/details/{identifier}"
        await update.message.reply_text(f"[{record_id}] رفعت المتعة كلها يا سيدي:\n{ia_url} 🍆💦💉")
    else:
        await update.message.reply_text(f"[{record_id}] فشل الرفع... جرب تاني يدوي.")

async def record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("أرسل الرابط على الأقل يا ولدي: /record <رابط> [أي كلام] [دقايق]")
        return

    url = args[0]
    if not url.startswith("http"):
        await update.message.reply_text("الرابط لازم يبدأ بـ http أو https يا حلو...")
        return

    # الباقي كله عنوان، والأخير لو رقم يبقى دقايق
    rest = args[1:]
    minutes = 360
    title = "Ecstasy Stream"

    if rest:
        # لو آخر كلمة رقم → دقايق
        if rest[-1].isdigit():
            try:
                minutes = int(rest[-1])
                minutes = min(max(minutes, 1), 360)
                rest = rest[:-1]
            except:
                pass
        title = " ".join(rest) if rest else "Ecstasy Stream"

    record_id = generate_unique_id()
    identifier = generate_unique_identifier()
    filename = f"{identifier}.ts"

    duration_seconds = minutes * 60

    active_recordings[record_id] = {
        "process": None,
        "filename": filename,
        "start_time": time.time(),
        "duration_minutes": minutes,
        "title": title,
        "progress_message": None
    }

    await update.message.reply_text(
        f"بدأت تسجيل جديد [{record_id}]\n"
        f"الرابط: {url}\n"
        f"العنوان: {title}\n"
        f"مدة: {minutes} دقيقة\n"
        f"تابع بـ /active أو /stop {record_id} 🍆💉"
    )

    asyncio.create_task(progress_reporter(record_id, update))

    ffmpeg_cmd = ["ffmpeg", "-re", "-i", url, "-c", "copy", "-t", str(duration_seconds), filename]
    process = subprocess.Popen(ffmpeg_cmd)
    active_recordings[record_id]["process"] = process

    process.wait()

    if record_id in active_recordings:
        await handle_upload(update, filename, title=title, partial=False, record_id=record_id)
        del active_recordings[record_id]

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("record", record))
application.add_handler(CommandHandler("active", active))
application.add_handler(CommandHandler("stop", stop))

print("شيطان الجنس بقى لا يقاوم... هيقبل أي أمر /record مهما كتبت ويبدأ المص فوراً 🍆💦💉")
application.run_polling(drop_pending_updates=True)
