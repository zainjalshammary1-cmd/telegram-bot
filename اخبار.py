import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from deep_translator import GoogleTranslator
import re
import hashlib
import os

# ----------- بيانات -----------

api_id = 30540427
api_hash = "eaa19d4ac276f691b14618bdf917b5c8"

SESSION = os.getenv("SESSION")

CHANNELS = ["@Arash_Insight"]

source_channels = [
    "@iran_military_capabilities",
    "@almayadeen",
    "@alnourradio",
    "@sepahcybery",
    "@mmirleb",
    "@manarbreaking",
    "@media_operations_center",
    "@altaifaalmansoora",
    "@muraselon"
]

client = TelegramClient(StringSession(SESSION), api_id, api_hash)

sent_messages = set()

# ----------- أدوات -----------

def normalize_text(text):
    return re.sub(r'\s+', ' ', text.lower()).strip()

def get_text_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

# ----------- تنظيف -----------

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r'https?://\S+|www\.\S+|t\.me/\S+|@\w+', '', text)

    lines = text.split('\n')
    cleaned = [l for l in lines if not any(w in l for w in ["تابعنا", "اشترك", "انضم", "المزيد"])]

    return re.sub(r'\n+', '\n', '\n'.join(cleaned)).strip()

# ----------- ترجمة -----------

def translate_if_persian(text):
    try:
        if re.search(r'[\u0600-\u06FF]', text):
            return GoogleTranslator(source='auto', target='ar').translate(text[:400])
    except:
        pass
    return text

# ----------- إزالة التكرار -----------

def remove_repeated_words(text):
    words, result = text.split(), []
    for w in words:
        if not result or w != result[-1]:
            result.append(w)
    return " ".join(result)

# ----------- المعالج -----------

@client.on(events.NewMessage(chats=source_channels))
async def handler(event):
    try:
        # ❌ تجاهل التعديلات
        if event.message.edit_date:
            return

        print("📥 خبر جديد")

        original = event.message.text or event.message.caption or ""

        text = clean_text(original)
        text = translate_if_persian(text)
        text = remove_repeated_words(text)

        if not text:
            return

        text_hash = get_text_hash(normalize_text(original))

        if text_hash in sent_messages:
            print("⚠️ مكرر")
            return

        sent_messages.add(text_hash)

        for ch in CHANNELS:
            if event.message.media:
                await client.send_file(ch, event.message.media, caption=text)
            else:
                await client.send_message(ch, text, link_preview=False)

        print("📡 تم النشر")

    except Exception as e:
        print("❌ خطأ:", e)

# ----------- تشغيل -----------

print("🚀 bot started")

client.start()
client.run_until_disconnected()
