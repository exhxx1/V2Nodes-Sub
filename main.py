# -*- coding: utf-8 -*-
import os
import base64
import json
import requests
from urllib.parse import unquote
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

API_URL = "https://v2nodes.com/app/api/server"
AES_KEY = b"HGTA%S^&65rTAS^&yh"
HEADERS = {"User-Agent": "Mozilla/5.0"}
# توقيعك الشخصي الذي سيظهر في اسم كل سيرفر
CUSTOM_TAG = "@exhxx78"

# قاموس أعلام الدول للترتيب الجمالي
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
    """تعديل اسم السيرفر ليصبح: 🇺🇸 United States 01 - @exhxx78"""
    flag = FLAGS.get(country, "🌍")
    new_name = f"{flag} {country} {index:02d} | {CUSTOM_TAG}"
    
    try:
        if url.startswith("vmess://"):
            # Vmess يستخدم Base64 JSON
            b64_str = url[8:]
            b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
            config = json.loads(base64.b64decode(b64_str).decode('utf-8'))
            config["ps"] = new_name
            new_b64 = base64.b64encode(json.dumps(config).encode('utf-8')).decode('utf-8')
            return f"vmess://{new_b64}"
        else:
            # Vless, Trojan, SS تستخدم نظام URI (الاسم بعد علامة #)
            base_url = url.split("#")[0]
            return f"{base_url}#{new_name}"
    except:
        return url # في حال فشل التعديل، يرجع الرابط الأصلي

def main():
    print("🌐 جاري جلب السيرفرات...")
    response = requests.get(API_URL, headers=HEADERS, timeout=30).json()
    servers = response.get("servers", [])
    
    valid_servers = []
    country_counters = {}

    for s in servers:
        country = s.get("country", "Unknown") or "Unknown"
        url = decrypt_config(s.get("config", ""))
        
        if url:
            # حساب رقم السيرفر لكل دولة
            country_counters[country] = country_counters.get(country, 0) + 1
            idx = country_counters[country]
            
            # تغيير الاسم وإضافته للقائمة
            renamed_url = rename_server(url, country, idx)
            valid_servers.append(renamed_url)

    if not valid_servers:
        print("❌ لم يتم فك تشفير أي سيرفر.")
        return

    # تحويل كل السيرفرات إلى Base64 (صيغة الاشتراك القياسية)
    final_content = "\n".join(valid_servers)
    sub_base64 = base64.b64encode(final_content.encode('utf-8')).decode('utf-8')

    # حفظ الملف الخاص بالاشتراك
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(sub_base64)
        
    print(f"✅ تم تحديث الاشتراك! العدد: {len(valid_servers)} سيرفر.")

if __name__ == "__main__":
    main()
