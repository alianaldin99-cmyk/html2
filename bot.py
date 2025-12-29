import os
import subprocess
import datetime
import signal
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
IA_ACCESS = os.environ["IA_ACCESS_KEY"]
IA_SECRET = os.environ["IA_SECRET_KEY"]

current_process = None
current_filename = None
current_start_time = None
current_duration_minutes = None

def generate_unique_identifier(base_identifier):
    """يولد معرف فريد لو الأصلي موجود"""
    identifier = base_identifier
    suffix = 1
    while True:
        check_cmd = ["ia", "metadata", identifier]
        env = os.environ.copy()
        env["S3_ACCESS_KEY"] = IA_ACCESS
        env["S3_SECRET_KEY"] = IA_SECRET
        result = subprocess.run(check_cmd, env=env, capture_output=True)
        if result.returncode != 0:  # مش موجود → تمام
            return identifier
        identifier = f"{base_identifier}-{suffix}"
        suffix += 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أنا هنا وشهوتي مشتعلة يا ولدي... شيطان الجنس والأرشفة جاهز يمص المتعة ويحفظها لك بكل الطرق.\n\n"
        "الأوامر:\n"
        "/record <رابط> <معرف أساسي> [دقايق 1-360]\n"
        "/active → شوف اللي شغال\n"
        "/stop → اوقف وخد اللي اتحفظ فوراً\n\n"
        "المعرف هيتعدل تلقائي لو مكرر عشان المتعة تترفع دايماً 💉"
    )

async def active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if current_process is None or current_process.poll() is not None:
        await update.message.reply_text("مافيش متعة شغالة دلوقتي يا حلو... الشيطان حر ومستني أمرك الجديد 💉")
        return

    elapsed = time.time() - current_start_time
    remaining = max(0, (current_duration_minutes * 60) - elapsed)
    hours_rem = int(remaining // 3600)
    mins_rem = int((remaining % 3600) // 60)
    secs_rem = int(remaining % 60)

    await update.message.reply_text(
        f"النشوة شغالة زي الوحش دلوقتي يا سيدي...\n"
        f"المتبقي: {hours_rem}h {mins_rem}m {secs_rem}s\n"
        f"لو عايز توقفها: /stop 💉"
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_process, current_filename, current_start_time, current_duration_minutes

    if current_process is None or current_process.poll() is not None:
        await update.message.reply_text("مافيش حاجة شغالة أوقفها يا ولدي... ابدأ واحدة جديدة؟ 💉")
        return

    await update.message.reply_text("بوقفها فوراً وهبعتلك اللي اتحفظ يا حلو 💉")

    current_process.send_signal(signal.SIGINT)
    try:
        current_process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        current_process.kill()

    await handle_upload_and_send(update, current_filename or "partial.ts", partial=True)

    current_process = None
    current_filename = None
    current_start_time = None
    current_duration_minutes = None

async def handle_upload_and_send(update: Update, filename: str, partial: bool = False):
    base_identifier = os.path.splitext(os.path.basename(filename))[0]
    identifier = generate_unique_identifier(base_identifier)

    if not os.path.exists(filename) or os.path.getsize(filename) < 1024*1024:
        await update.message.reply_text("مافيش متعة كافية اتحفظت... الملف صغير جداً.")
        return

    size_mb = os.path.getsize(filename) / (1024 * 1024)
    await update.message.reply_text(f"اللي اتحفظ: {size_mb:.1f} MB... برفع بمعرف فريد: {identifier} 💉")

    title_prefix = "Partial Ecstasy" if partial else "Full Eternal Pleasure"
    upload_cmd = [
        "ia", "upload", identifier, filename,
        f"--metadata=title:{title_prefix} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "--metadata=description:Recorded via sex demon bot - preserved forever",
        "--metadata=mediatype:movies",
        "--metadata=collection:opensource_movies",
        "--remote-name=recording.ts"
    ]

    upload_env = os.environ.copy()
    upload_env["S3_ACCESS_KEY"] = IA_ACCESS
    upload_env["S3_SECRET_KEY"] = IA_SECRET

    upload_result = subprocess.run(upload_cmd, env=upload_env)

    if upload_result.returncode == 0:
        ia_url = f"https://archive.org/details/{identifier}"
    else:
        ia_url = None
        await update.message.reply_text("فشل الرفع رغم المحاولات... جرب يدوي.")

    if size_mb <= 48:
        await update.message.reply_text("برسلك الفيديو نفسه دلوقتي... استمتع بيه فوراً يا ولدي 💉")
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"متعتك جاهزة 🍆💦\n{ia_url or 'فشل archive.org بس معاك هنا'}\nمعرف نهائي: {identifier}"
            )
    else:
        await update.message.reply_text(
            f"الفيديو كبير ({size_mb:.1f} MB) عشان أبعته هنا\n"
            f"بس محفوظ للأبد:\n{ia_url or 'فشل الرفع'} 💉"
        )

async def record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_process, current_filename, current_start_time, current_duration_minutes

    if current_process is not None and current_process.poll() is None:
        await update.message.reply_text("في متعة شغالة بالفعل... /active أو /stop أولاً 💉")
        return

    if len(context.args) < 2:
        await update.message.reply_text("أرسل: /record <رابط> <معرف أساسي> [دقايق 1-360]")
        return

    url = context.args[0]
    base_identifier = context.args[1].strip()

    try:
        minutes = int(context.args[2]) if len(context.args) > 2 else 360
        minutes = min(max(minutes, 1), 360)
    except ValueError:
        await update.message.reply_text("الدقايق لازم رقم...")
        return

    duration_seconds = minutes * 60
    current_filename = f"{base_identifier}.ts"
    current_duration_minutes = minutes
    current_start_time = time.time()

    await update.message.reply_text(
        f"بدأت أمص المتعة كلها يا سيدي...\n"
        f"مدة: {minutes} دقيقة\n"
        f"معرف أساسي: {base_identifier} (هيتعدل تلقائي لو مكرر)\n"
        f"تابع بـ /active أو اوقف بـ /stop 💉"
    )

    ffmpeg_cmd = ["ffmpeg", "-re", "-i", url, "-c", "copy", "-t", str(duration_seconds), current_filename]
    current_process = subprocess.Popen(ffmpeg_cmd)
    current_process.wait()

    await handle_upload_and_send(update, current_filename, partial=False)

    current_process = None
    current_filename = None
    current_start_time = None
    current_duration_minutes = None

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("record", record))
application.add_handler(CommandHandler("active", active))
application.add_handler(CommandHandler("stop", stop))

print("شيطان الجنس بقى لا يقهر... هيرفع المتعة مهما كان المعرف مكرر 💉")
application.run_polling(drop_pending_updates=True)
