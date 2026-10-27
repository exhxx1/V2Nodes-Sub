# -*- coding: utf-8 -*-
import os
import base64
import json
import requests
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# جلب الأسرار من الخزنة
API_URL = os.environ.get("SECRET_API")
secret_key_str = os.environ.get("SECRET_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
AES_KEY = secret_key_str.encode('utf-8')

# إعدادات قناتك
CHAT_ID = "@haideradel"
SUB_LINK = "https://raw.githubusercontent.com/exhxx1/V2Nodes-Sub/main/sub.txt"

HEADERS = {"User-Agent": "Mozilla/5.0"}
CUSTOM_TAG = "@exhxx78"

FLAGS = {
    "United States": "🇺🇸", "Germany": "🇩🇪", "United Kingdom": "🇬🇧",
    "Singapore": "🇸🇬", "Japan": "🇯🇵", "France": "🇫🇷", "Canada": "🇨🇦",
    "Netherlands": "🇳🇱", "India": "🇮🇳", "Australia": "🇦🇺",
    "Turkey": "🇹🇷", "Brazil": "🇧🇷", "South Korea": "🇰🇷", "Unknown": "🌍"
}

def decrypt_config(b64_config):
    try:
        data = base64.b64decode(b64_config)
        iv, ciphertext = data[:16], data[16:]
        keys = [AES_KEY.ljust(32, b"\x00"), AES_KEY.ljust(32, b" ")]
        for key in keys:
            try:
                cipher = AES.new(key, AES.MODE_CBC, iv)
                decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size).decode("utf-8")
                if any(decrypted.startswith(p) for p in ("vless://", "vmess://", "ss://", "trojan://")):
                    return decrypted
            except: continue
    except: pass
    return None

def rename_server(url, country, index):
    flag = FLAGS.get(country, "🌍")
    new_name = f"{flag} {country} {index:02d} | {CUSTOM_TAG}"
    try:
        if url.startswith("vmess://"):
            b64_str = url[8:]
            b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
            config = json.loads(base64.b64decode(b64_str).decode('utf-8'))
            config["ps"] = new_name
            new_b64 = base64.b64encode(json.dumps(config).encode('utf-8')).decode('utf-8')
            return f"vmess://{new_b64}"
        else:
            base_url = url.split("#")[0]
            return f"{base_url}#{new_name}"
    except:
        return url 

def send_telegram_alert(count):
    """دالة إرسال الإشعار إلى قناة التليجرام"""
    if not TELEGRAM_TOKEN:
        print("⚠️ توكن التليجرام غير موجود، لن يتم النشر.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # تصميم الرسالة (HTML)
    msg_text = (
        "✅ <b>تحديث جديد لسيرفرات V2Ray!</b> 🚀\n\n"
        f"🌍 عدد السيرفرات النشطة: <b>{count}</b> سيرفر\n"
        "🔄 <i>(يتم تحديث السيرفرات تلقائياً كل 6 ساعات)</i>\n\n"
        "👇 <b>رابط الاشتراك (اضغط عليه للنسخ):</b>\n"
        f"<code>{SUB_LINK}</code>\n\n"
        "🛡 <b>طريقة الاستخدام:</b>\n"
        "انسخ الرابط أعلاه، واذهب إلى تطبيق (V2RayNG) وأضفه من قائمة الاشتراكات."
    )
    
    # زر الاشتراك الشفاف
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔗 فتح الرابط في المتصفح", "url": SUB_LINK}]
        ]
    }
    
    payload = {
        "chat_id": CHAT_ID,
        "text": msg_text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(keyboard),
        "disable_web_page_preview": True
    }
    
    try:
        requests.post(url, data=payload)
        print("✅ تم النشر في قناة التليجرام بنجاح!")
    except Exception as e:
        print(f"❌ فشل النشر في التليجرام: {e}")

def main():
    if not API_URL or not secret_key_str:
        print("❌ الأسرار غير موجودة!")
        return

    print("🌐 جاري جلب السيرفرات...")
    response = requests.get(API_URL, headers=HEADERS, timeout=30).json()
    servers = response.get("servers", [])
    
    valid_servers = []
    country_counters = {}

    for s in servers:
        country = s.get("country", "Unknown") or "Unknown"
        url = decrypt_config(s.get("config", ""))
        
        if url:
            country_counters[country] = country_counters.get(country, 0) + 1
            idx = country_counters[country]
            renamed_url = rename_server(url, country, idx)
            valid_servers.append(renamed_url)

    if not valid_servers:
        return

    final_content = "\n".join(valid_servers)
    sub_base64 = base64.b64encode(final_content.encode('utf-8')).decode('utf-8')

    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(sub_base64)
        
    print(f"✅ تم تحديث ملف الاشتراك بعدد {len(valid_servers)} سيرفر.")
    
    # تشغيل دالة التليجرام لنشر الرسالة
    send_telegram_alert(len(valid_servers))

if __name__ == "__main__":
    main()
