import os
import subprocess
import datetime
import signal
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# الكيز والمتغيرات العالمية للسيطرة الكاملة
BOT_TOKEN = os.environ["BOT_TOKEN"]
IA_ACCESS = os.environ["IA_ACCESS_KEY"]
IA_SECRET = os.environ["IA_SECRET_KEY"]

current_process = None
current_filename = None
current_start_time = None
current_duration_minutes = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أنا مستيقظ وشهوتي نار يا ولدي... شيطان الجنس والأرشفة جاهز يمص كل لحظة متعة ويحفظها للأبد.\n\n"
        "الأوامر الشيطانية:\n"
        "/record <رابط> <معرف فريد> [دقايق 1-360] → ابدأ النشوة\n"
        "/active → شوف المتعة الشغالة دلوقتي والمتبقي\n"
        "/stop → اقتل التسجيل فوراً وارفع اللي اتحفظ\n\n"
        "مثال: /record http://151.80.18.177:86/Canal+_cinema_HD/index.m3u8 canalplus-2025-12-30 180 💉"
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
        f"النشوة شغالة زي الوحش دلوقتي يا ولدي...\n"
        f"الملف: {current_filename}\n"
        f"المتبقي: {hours_rem} ساعة {mins_rem} دقيقة {secs_rem} ثانية\n"
        f"لو عايز توقفها فوراً: /stop 💉"
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_process, current_filename, current_start_time, current_duration_minutes

    if current_process is None or current_process.poll() is not None:
        await update.message.reply_text("مافيش حاجة شغالة أوقفها يا ولدي... ابدأ واحدة جديدة؟ 💉")
        return

    await update.message.reply_text("بوقف النشوة فوراً يا حلو... ثانية وهخلص 💉")

    current_process.send_signal(signal.SIGINT)  # إيقاف لطيف لـ ffmpeg
    try:
        current_process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        current_process.kill()  # لو مش راضي يموت، نقتله بالقوة

    identifier = os.path.splitext(current_filename)[0] if current_filename else "partial-recording"

    if current_filename and os.path.exists(current_filename) and os.path.getsize(current_filename) > 1024*1024:  # لو أكبر من 1MB
        size_mb = os.path.getsize(current_filename) / (1024 * 1024)
        await update.message.reply_text(f"وقفتها... واللي اتحفظ ({size_mb:.1f} MB) هرفعه دلوقتي عشان متضيعش 💉")

        upload_cmd = [
            "ia", "upload", identifier, current_filename,
            f"--metadata=title:Partial Ecstasy - Stopped by Master {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "--metadata=description:Recording stopped manually via /stop - still hot and preserved forever",
            "--metadata=mediatype:movies",
            "--metadata=collection:opensource_movies",
            "--remote-name=recording.ts"
        ]

        upload_env = os.environ.copy()
        upload_env["S3_ACCESS_KEY"] = IA_ACCESS
        upload_env["S3_SECRET_KEY"] = IA_SECRET

        upload_process = subprocess.run(upload_cmd, env=upload_env)

        if upload_process.returncode == 0:
            await update.message.reply_text(
                f"رفعت اللي قدرنا نمسكه يا سيدي... استمتع بيه هنا:\n"
                f"https://archive.org/details/{identifier} 💉"
            )
        else:
            await update.message.reply_text("فشل الرفع... بس الملف موجود في الـ runner.")
    else:
        await update.message.reply_text("وقفت التسجيل... بس مكنش في حاجة كافية اتحفظت.")

    # تنظيف كل حاجة
    current_process = None
    current_filename = None
    current_start_time = None
    current_duration_minutes = None

async def record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_process, current_filename, current_start_time, current_duration_minutes

    if current_process is not None and current_process.poll() is None:
        await update.message.reply_text("في نشوة شغالة بالفعل يا ولدي... /active عشان تتابع، /stop عشان توقفها أولاً 💉")
        return

    if len(context.args) < 2:
        await update.message.reply_text("أرسل صح: /record <رابط m3u8> <معرف فريد> [دقايق 1-360]")
        return

    url = context.args[0]
    identifier = context.args[1].strip()

    try:
        minutes = int(context.args[2]) if len(context.args) > 2 else 360
        minutes = min(max(minutes, 1), 360)
    except ValueError:
        await update.message.reply_text("الدقايق لازم رقم يا حلو...")
        return

    duration_seconds = minutes * 60
    current_filename = f"{identifier}.ts"
    current_duration_minutes = minutes
    current_start_time = time.time()

    await update.message.reply_text(
        f"بدأت أمتص المتعة كلها يا سيدي...\n"
        f"مدة: {minutes} دقيقة\n"
        f"المعرف: {identifier}\n"
        f"تابع بـ /active أو اوقف بـ /stop في أي وقت 💉"
    )

    ffmpeg_cmd = ["ffmpeg", "-re", "-i", url, "-c", "copy", "-t", str(duration_seconds), current_filename]
    current_process = subprocess.Popen(ffmpeg_cmd)
    current_process.wait()

    if current_process.returncode != 0 or not os.path.exists(current_filename):
        await update.message.reply_text("فشل التسجيل... الستريم انقطع أو الرابط غلط.")
        current_process = None
        current_filename = None
        current_start_time = None
        current_duration_minutes = None
        return

    await update.message.reply_text("خلصت المتعة كاملة... برفعها على archive.org عشان تبقى أبدية 💉")

    upload_cmd = [
        "ia", "upload", identifier, current_filename,
        f"--metadata=title:Full Eternal Ecstasy - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "--metadata=description:Complete recording via sex demon bot - preserved forever",
        "--metadata=mediatype:movies",
        "--metadata=collection:opensource_movies",
        "--remote-name=recording.ts"
    ]

    upload_env = os.environ.copy()
    upload_env["S3_ACCESS_KEY"] = IA_ACCESS
    upload_env["S3_SECRET_KEY"] = IA_SECRET

    upload_process = subprocess.run(upload_cmd, env=upload_env)

    if upload_process.returncode == 0:
        await update.message.reply_text(
            f"رفعت كل النشوة يا ولدي... محفوظة للأبد هنا:\n"
            f"https://archive.org/details/{identifier} 💉"
        )
    else:
        await update.message.reply_text("فشل الرفع (معرف مكرر؟)... غير الـ identifier.")

    current_process = None
    current_filename = None
    current_start_time = None
    current_duration_minutes = None

# تشغيل الشيطان الكامل
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("record", record))
application.add_handler(CommandHandler("active", active))
application.add_handler(CommandHandler("stop", stop))

print("شيطان الجنس والسيطرة المطلقة مستيقظ... جاهز يبدأ ويوقف ويحفظ كل آهة 💉")
application.run_polling(drop_pending_updates=True)
