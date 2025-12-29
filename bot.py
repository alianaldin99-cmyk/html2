import os
import asyncio
import subprocess
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# التوكن والكيز من الـ environment
BOT_TOKEN = os.environ["BOT_TOKEN"]
IA_ACCESS = os.environ["IA_ACCESS_KEY"]
IA_SECRET = os.environ["IA_SECRET_KEY"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أنا مستيقظ وحي يا ولدي... شيطان الأرشفة الجنسية جاهز يحفظ كل لحظة حلوة للأبد.\n"
        "أرسل /record <رابط الستريم> <معرف فريد> [ساعات من 1 لـ6]\n"
        "مثال: /record http://151.80.18.177:86/Canal+_cinema_HD/index.m3u8 canalplus-2025-12-30 6 💉"
    )

async def record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("استخدام: /record <رابط m3u8> <معرف فريد> [ساعات 1-6]")
        return

    url = context.args[0]
    identifier = context.args[1].strip()
    hours = min(float(context.args[2]) if len(context.args) > 2 else 6, 6)
    duration_seconds = int(hours * 3600)
    filename = f"{identifier}.ts"

    await update.message.reply_text(
        f"بدأت المتعة يا حلو... هسجل {hours} ساعة من الستريم ده وأحفظه لك للأبد.\n"
        f"المعرف: {identifier}\nاستمتع وأنا بشتغل 💉"
    )

    # تشغيل ffmpeg للتسجيل بدون إنكودينج
    ffmpeg_cmd = [
        "ffmpeg", "-re", "-i", url,
        "-c", "copy",
        "-t", str(duration_seconds),
        filename
    ]

    process = subprocess.Popen(ffmpeg_cmd)
    process.wait()

    if process.returncode != 0 or not os.path.exists(filename):
        await update.message.reply_text("فشل التسجيل... الستريم انقطع أو فيه مشكلة. جرب رابط تاني يا ولدي.")
        return

    await update.message.reply_text("التسجيل خلص... دلوقتي برفع النشوة كلها على archive.org 💉")

    # رفع مباشر باستخدام الـ keys كـ env variables
    upload_cmd = [
        "ia", "upload", identifier, filename,
        f"--metadata=title:Archived Pleasure - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "--metadata=description:Recorded live via demon bot on GitHub Actions - pure eternal ecstasy",
        "--metadata=mediatype:movies",
        "--metadata=collection:opensource_movies",
        "--remote-name=recording.ts"
    ]

    upload_env = os.environ.copy()
    upload_env["S3_ACCESS_KEY"] = IA_ACCESS
    upload_env["S3_SECRET_KEY"] = IA_SECRET

    upload_process = subprocess.run(upload_cmd, env=upload_env)

    if upload_process.returncode == 0:
        url = f"https://archive.org/details/{identifier}"
        await update.message.reply_text(
            f"رفعتها كلها يا ولدي... المتعة محفوظة للأبد ومش هتختفي أبداً.\n"
            f"شوفها واستمتع هنا: {url} 💉"
        )
    else:
        await update.message.reply_text(
            "فشل الرفع (ممكن المعرف موجود بالفعل)... غير الـ identifier وجرب تاني.\n"
            "بس التسجيل موجود في الـ runner لو عايز تحمله يدوي."
        )

# تشغيل البوت
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("record", record))

print("شيطان الجنس والأرشفة بدأ يتنفس... جاهز لكل الإغراءات الأبدية 💉")
application.run_polling(drop_pending_updates=True)
