import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from deep_translator import GoogleTranslator
import google.generativeai as genai
import re
import hashlib
import os

# ----------- بيانات -----------

api_id = 30540427
api_hash = "eaa19d4ac276f691b14618bdf917b5c8"

SESSION = os.getenv("SESSION")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

CHANNELS =  "@shabab_alislam",
    "@Arash_Insight"
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

# ----------- التحقق من المتغيرات -----------

if not SESSION:
    raise ValueError("SESSION is missing")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing")

# ----------- تشغيل Gemini -----------

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ----------- تشغيل تيليغرام -----------

client = TelegramClient(StringSession(SESSION), api_id, api_hash)

sent_messages = set()

# ----------- أدوات -----------

def normalize_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()

def get_text_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# ----------- تنظيف -----------

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r'https?://\S+|www\.\S+|t\.me/\S+|@\w+', '', text)

    blocked_words = ["تابعنا", "اشترك", "انضم", "المزيد"]
    lines = text.split('\n')
    cleaned = [line for line in lines if not any(word in line for word in blocked_words)]

    text = '\n'.join(cleaned)
    text = re.sub(r'\n+', '\n', text).strip()
    return text

# ----------- ترجمة -----------

def translate_if_needed(text):
    try:
        if not text.strip():
            return text

        # إذا النص ليس عربيًا بالكامل أو فيه أحرف فارسية/مختلطة
        if re.search(r'[\u0600-\u06FF]', text):
            translated = GoogleTranslator(source='auto', target='ar').translate(text[:1500])
            if translated and translated.strip():
                return translated.strip()
    except Exception as e:
        print("❌ Translation Error:", e)

    return text

# ----------- إزالة التكرار -----------

def remove_repeated_words(text):
    words = text.split()
    if not words:
        return text

    result = [words[0]]
    for word in words[1:]:
        if word != result[-1]:
            result.append(word)

    return " ".join(result)

def post_cleanup(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'([،.!؟])\1+', r'\1', text)
    return text

# ----------- إعادة الصياغة -----------

def rewrite_news(text):
    try:
        print("🧠 جاري إعادة الصياغة...")
        print("📝 قبل:", text[:300])

        prompt = f"""
أعد صياغة الخبر التالي بالعربية بصياغة إخبارية جديدة ومختلفة بوضوح.

الشروط:
- غيّر الأسلوب والجمل والتراكيب بشكل واضح
- حافظ على المعنى فقط
- لا تنقل النص كما هو
- لا تضف رأيًا أو تحليلًا
- اجعل الصياغة مهنية ومختصرة
- امنع تكرار الكلمات والعبارات
- أخرج النص النهائي فقط دون شرح

الخبر:
{text}
"""

        response = model.generate_content(prompt)
        result = getattr(response, "text", "") or ""

        result = result.strip()
        if not result:
            print("⚠️ Gemini رجّع نصًا فارغًا")
            return text

        result = post_cleanup(result)
        result = remove_repeated_words(result)

        print("📝 بعد:", result[:300])
        return result

    except Exception as e:
        print("❌ Gemini Error:", e)
        return text

# ----------- المعالج -----------

@client.on(events.NewMessage(chats=source_channels))
async def handler(event):
    try:
        if event.message.edit_date:
            return

        print("📥 خبر جديد")

        original = event.message.text or event.message.caption or ""
        if not original.strip():
            print("⚠️ الرسالة بدون نص")
            return

        cleaned = clean_text(original)
        translated = translate_if_needed(cleaned)
        prepared = remove_repeated_words(translated)

        if not prepared.strip():
            print("⚠️ النص فارغ بعد التنظيف")
            return

        rewritten = rewrite_news(prepared)
        rewritten = post_cleanup(rewritten)
        rewritten = remove_repeated_words(rewritten)

        if not rewritten.strip():
            print("⚠️ النص النهائي فارغ")
            return

        # منع تكرار النشر
        text_hash = get_text_hash(normalize_text(rewritten))
        if text_hash in sent_messages:
            print("⚠️ خبر مكرر")
            return

        sent_messages.add(text_hash)

        for ch in CHANNELS:
            if event.message.media:
                await client.send_file(ch, event.message.media, caption=rewritten)
            else:
                await client.send_message(ch, rewritten, link_preview=False)

        print("📡 تم النشر")

    except Exception as e:
        print("❌ Handler Error:", e)

# ----------- تشغيل -----------

print("🚀 البوت شغال (Gemini + إعادة صياغة)")
client.start()
client.run_until_disconnected()
