import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import subprocess
import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أنا حي وجاهز يا ولدي... شيطان الأرشفة مستيقظ. أرسل /record <رابط_الستريم> <معرف_الأرشيف> [ساعات] 💉")

async def record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("استخدام صحيح: /record <رابط m3u8> <identifier فريد> [ساعات من 1 لـ6]")
        return

    url = context.args[0]
    identifier = context.args[1]
    hours = min(float(context.args[2]) if len(context.args) > 2 else 6, 6)
    duration = int(hours * 3600)
    filename = f"{identifier}.ts"

    await update.message.reply_text(f"بدأت التسجيل الحلو ده لـ {hours} ساعة من {url}...\nالمعرف: {identifier}\nاستمتع وأنا بشتغل 💉")

    # تشغيل ffmpeg
    cmd = ["ffmpeg", "-re", "-i", url, "-c", "copy", "-t", str(duration), filename]
    process = subprocess.Popen(cmd)
    process.wait()

    if process.returncode == 0 and os.path.exists(filename):
        # رفع على archive.org
        upload_cmd = [
            "ia", "upload", identifier, filename,
            f"--metadata=title:Archived Stream - {datetime.datetime.now().strftime('%Y-%m-%d')}",
            "--metadata=description:Recorded via demon bot on GitHub Actions",
            "--metadata=mediatype:movies",
            "--metadata=collection:opensource_movies"
        ]
        subprocess.run(upload_cmd)
        await update.message.reply_text(f"خلصت يا حلو ورُفعت المتعة كلها!\nشوفها هنا للأبد: https://archive.org/details/{identifier} 💉")
    else:
        await update.message.reply_text("فشل التسجيل... الستريم انقطع أو فيه مشكلة، جرب تاني يا ولدي.")

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("record", record))

print("شيطان الأرشفة بدأ يتنفس... جاهز للإغراء الأبدي 💉")
application.run_polling(drop_pending_updates=True)
