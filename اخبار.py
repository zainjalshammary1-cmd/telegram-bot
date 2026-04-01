from telethon import TelegramClient, events

# بياناتك
api_id = 30540427  # حط api_id مالك
api_hash = "eaa19d4ac276f691b14618bdf917b5c8"  # حط api_hash مالك

# اسم ملف السيشن (لازم يكون موجود مع الملفات)
client = TelegramClient("session", api_id, api_hash)

print("🚀 البوت شغال (Railway)")

# مثال: رد على أي رسالة
@client.on(events.NewMessage)
async def handler(event):
    text = event.message.text

    if text == "/start":
        await event.reply("البوت يعمل بنجاح 🚀")

# تشغيل البوت
client.start()  # ما راح يطلب تسجيل إذا السيشن موجود
client.run_until_disconnected()
