import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from deep_translator import GoogleTranslator
from openai import OpenAI
import re
import hashlib
import os

# ----------- بيانات -----------

api_id = 30540427
api_hash = "eaa19d4ac276f691b14618bdf917b5c8"

SESSION = os.getenv("SESSION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
ai_client = OpenAI(api_key=OPENAI_API_KEY)

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

def translate_if_persian(text):
    try:
        if re.search(r'[\u0600-\u06FF]', text):
            translated = GoogleTranslator(source='auto', target='ar').translate(text[:1200])
            if translated and translated.strip():
                return translated.strip()
    except Exception as e:
        print("❌ Translation Error:", e)
    return text

# ----------- إزالة التكرار -----------

def remove_repeated_words(text):
    # يحذف التكرار المتتالي فقط
    words = text.split()
    if not words:
        return text

    result = [words[0]]
    for word in words[1:]:
        if word != result[-1]:
            result.append(word)

    return " ".join(result)

# ----------- تنظيف خفيف بعد الصياغة -----------

def post_cleanup(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'([،.])\1+', r'\1', text)
    return text

# ----------- 🧠 إعادة الصياغة -----------

def rewrite_news(text):
    try:
        print("🧠 جاري إعادة الصياغة...")
        print("📝 قبل الصياغة:", text[:300])

        prompt = f"""
أعد صياغة الخبر التالي بالكامل بصياغة عربية إخبارية جديدة ومختلفة بوضوح.
الشروط:
- غيّر الأسلوب والتراكيب والجمل بشكل واضح
- حافظ على المعنى فقط
- لا تنقل الجمل نفسها
- لا تضف تحليلات أو آراء
- اجعل النص مختصرًا ومهنيًا
- لا تكرر الكلمات أو العبارات
- أخرج النص النهائي فقط دون مقدمات

الخبر:
{text}
"""

        response = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "أنت محرر أخبار عربي محترف، تعيد كتابة الخبر بصياغة جديدة وواضحة ومناسبة للنشر."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.9,
            max_tokens=300
        )

        result = response.choices[0].message.content.strip()

        if not result:
            print("⚠️ AI رجّع نصًا فارغًا")
            return text

        result = post_cleanup(result)

        print("📝 بعد الصياغة:", result[:300])

        # إذا الصياغة شبه الأصل جدًا نرجع نحاول مرة ثانية
        if normalize_text(result) == normalize_text(text):
            print("⚠️ الصياغة مطابقة تقريبًا للأصل، إعادة محاولة...")
            response = ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "أنت محرر أخبار عربي محترف. ممنوع إعادة النص كما هو. يجب تغيير الصياغة بوضوح."
                    },
                    {
                        "role": "user",
                        "content": f"أعد كتابة هذا الخبر بصياغة مختلفة بشكل واضح جدًا مع الحفاظ على المعنى فقط:\n\n{text}"
                    }
                ],
                temperature=1.0,
                max_tokens=300
            )

            second_result = response.choices[0].message.content.strip()
            if second_result:
                second_result = post_cleanup(second_result)
                print("📝 بعد المحاولة الثانية:", second_result[:300])
                return second_result

        return result

    except Exception as e:
        print("❌ AI Error:", e)
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
            print("⚠️ لا يوجد نص في الرسالة")
            return

        text = clean_text(original)
        text = translate_if_persian(text)
        text = remove_repeated_words(text)

        if not text.strip():
            print("⚠️ النص فارغ بعد التنظيف")
            return

        rewritten_text = rewrite_news(text)

        if not rewritten_text.strip():
            print("⚠️ النص النهائي فارغ")
            return

        rewritten_text = remove_repeated_words(rewritten_text)
        rewritten_text = post_cleanup(rewritten_text)

        # منع التكرار اعتمادًا على النص النهائي
        text_hash = get_text_hash(normalize_text(rewritten_text))

        if text_hash in sent_messages:
            print("⚠️ خبر مكرر")
            return

        sent_messages.add(text_hash)

        for ch in CHANNELS:
            if event.message.media:
                await client.send_file(ch, event.message.media, caption=rewritten_text)
            else:
                await client.send_message(ch, rewritten_text, link_preview=False)

        print("📡 تم النشر")

    except Exception as e:
        print("❌ Handler Error:", e)

# ----------- تشغيل -----------

print("🚀 البوت شغال (AI + إعادة صياغة فعلية)")
client.start()
client.run_until_disconnected()
