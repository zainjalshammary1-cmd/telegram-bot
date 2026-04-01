import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

from telethon import TelegramClient, events
from deep_translator import GoogleTranslator
import re

# ----------- إعدادات -----------
CHANNELS = [
    "@Arash_Insight",
    # "@shabab_alislam",
    # "@channel3"
]

api_id = 30540427
api_hash = "eaa19d4ac276f691b14618bdf917b5c8"

# ----------- قنوات المصدر -----------
source_channels = [
    "iran_military_capabilities",
    "almayadeen",
    "alnourradio",
    "sepahcybery",
    "mmirleb",
    "manarbreaking",
    "media_operations_center",
    "mehwaralmokawma",
    "altaifaalmansoora",
    "StateMediaTeamForums",
    "muraselon",
    "jbt_313"
]

client = TelegramClient("session", api_id, api_hash)

sent_messages = set()

# ----------- تنظيف النص -----------
def clean_text(text):
    if not text:
        return ""

    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    text = re.sub(r't\.me/\S+', '', text)
    text = re.sub(r'@\w+', '', text)

    lines = text.split('\n')
    cleaned = []
    for line in lines:
        if any(word in line for word in ["تابعنا", "اشترك", "انضم", "المزيد"]):
            continue
        cleaned.append(line)

    text = '\n'.join(cleaned)
    text = re.sub(r'\n+', '\n', text)

    return text.strip()

# ----------- ترجمة -----------
def translate_if_persian(text):
    try:
        if any("\u0600" <= c <= "\u06FF" for c in text):
            return GoogleTranslator(source='auto', target='ar').translate(text)
    except:
        pass
    return text

# ----------- إزالة التكرار -----------
def remove_repeated_words(text):
    words = text.split()
    cleaned = []
    for word in words:
        if not cleaned or word != cleaned[-1]:
            cleaned.append(word)
    return " ".join(cleaned)

# ----------- إعادة صياغة -----------
def rewrite_text(text):
    if not text:
        return ""

    text = text.strip()

    if len(text) > 300:
        text = text[:300] + "..."

    return text

# ----------- تيليغرام -----------
@client.on(events.NewMessage(chats=source_channels))
async def handler(event):
    try:
        unique_id = f"{event.chat_id}_{event.message.id}"

        # منع التكرار
        if unique_id in sent_messages:
            return
        sent_messages.add(unique_id)

        text = event.message.text or event.message.caption or ""

        text = clean_text(text)
        text = translate_if_persian(text)
        text = remove_repeated_words(text)
        text = rewrite_text(text)

        if not text:
            return

        for ch in CHANNELS:
            if event.message.photo:
                await client.send_file(ch, event.message.photo, caption=text)
            elif event.message.video:
                await client.send_file(ch, event.message.video, caption=text)
            else:
                await client.send_message(ch, text, link_preview=False)

        print("📡 تم نشر خبر")

    except Exception as e:
        print("خطأ:", e)

# ----------- تشغيل -----------
print("🚀 البوت شغال (نظيف + متعدد القنوات)")

client.start()
client.run_until_disconnected()