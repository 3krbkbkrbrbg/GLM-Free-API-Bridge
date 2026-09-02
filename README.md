# 🚀 GLM / Z.ai Free API Bridge

پروکسی سبک، پرسرعت و رایگان برای تبدیل وب‌سرویس **Z.ai (chat.z.ai)** به اندپوینت استاندارد و سازگار با **OpenAI API**، همراه با داشبورد مدیریت مدرن و اختصاصی برای تمامی مدل‌های سری **GLM**.

این پروژه به شما اجازه می‌دهد بدون پرداخت هزینه یا نیاز به API Key رسمی، از تمام مدل‌های پیشرفته Zhipu AI و Z.ai (شامل `glm-5`, `glm-4.7`, `glm-4.7-thinking`, `glm-4.6v`, `GLM-4.5` و ...) در کلاینت‌های مختلف (مانند Minis, NextChat, LobeChat, Cursor, LibreChat و ...) استفاده کنید.

---

## ✨ قابلیت‌ها و ویژگی‌ها

- **سازگاری کامل با OpenAI API**: پیاده‌سازی کامل `/v1/chat/completions` و `/v1/models`
- **پشتیبانی از استریم (SSE Streaming)**: دریافت پاسخ‌ها به صورت کلمه به کلمه و زنده
- **تولید خودکار امضای کلاینت (ZS Signature)**: دور زدن و اعتبارسنجی خودکار درخواست‌ها با امضای HMAC-SHA256 بر مبنای منطق فرانت‌اند Z.ai
- **پاک‌سازی هوشمند متادیتا و تگ‌های استدلال**: حذف خودکار تگ‌های `<details>`, `<summary>` و متادیتای وب فرانت‌اند در هر دو حالت متنی و استریم
- **داشبورد مدیریت و پلی‌گراند وب**: رابط کاربری زیبا با دارک مود برای تست مدل‌ها، مشاهده وضعیت و تعویض آسان توکن
- **استقرار روی دایتونا (Daytona Cloud Sandbox)**: اجرای کاملاً ابری بدون نیاز به روشن نگه داشتن سیستم شخصی
- **بدون وابستگی خارجی (Zero Dependencies)**: اجرا با پایتون استاندارد بدون نیاز به نصب پکیج‌های اضافی (pip)

---

## 🤖 مدل‌های پشتیبانی شده

| شناسه مدل | کاربرد و توضیحات |
|---|---|
| `glm-5` | پرچمدار نسل جدید GLM با قابلیت‌های استدلال فوق‌العاده عمیق |
| `glm-4.7` | مدل قدرتمند، سریع و بالانس شده برای تمامی کارهای برنامه‌نویسی و روزمره |
| `glm-4.7-thinking` | حالت تفکر عمیق با زنجیره استدلال (Chain of Thought) |
| `glm-4.7-search` | نسخه متصل به موتور جستجوی وب برای پاسخ‌های به‌روز |
| `glm-4.6v` | مدل چندرسانه‌ای برای تحلیل و درک تصاویر (Vision) |
| `GLM-4.5` | مدل ۳۶۰ میلیارد پارامتری استاندارد Zhipu |
| `GLM-4.5-Thinking` | نسخه استدلالی GLM-4.5 |
| `GLM-4.5-Air` | مدل سبک و پرسرعت ۱۰۶ میلیارد پارامتری |

---

## 🔑 نحوه دریافت توکن Z.ai

1. وارد حساب کاربری خود در [chat.z.ai](https://chat.z.ai) شوید.
2. کلید `F12` را زده یا وارد **Developer Tools** مرورگر شوید.
3. به تب **Application** (یا Storage) بروید.
4. در بخش **Cookies** یا **LocalStorage**، مقدار `token` را کپی کنید (یک رشته طولانی JWT که با `eyJ...` شروع می‌شود).

---

## ☁️ روش اول: استقرار ابری و رایگان روی دایتونا (Daytona Sandbox)

اگر نمی‌خواهید برنامه را روی سیستم شخصی یا گوشی اجرا کنید، می‌توانید آن را با یک دستور روی سَندباکس ابری **Daytona** اجرا کنید:

### ۱. نصب SDK دایتونا
```bash
pip install daytona
```

### ۲. اجرای خودکار
اسکریپت `deploy_daytona.py` را با کلید دسترسی دایتونا و توکن Z.ai خود اجرا کنید:
```bash
python3 deploy_daytona.py "YOUR_DAYTONA_API_KEY" "YOUR_ZAI_JWT_TOKEN"
```

این اسکریپت یک سَندباکس اختصاصی ایجاد کرده، پروکسی را بالا آورده و یک **Signed Preview URL** معتبر ۲۴ ساعته برای پورت ۸۰۸۰ تولید می‌کند:
```text
🔗 Base URL: https://8080-xxxxx.daytonaproxy01.net/v1
📊 Dashboard: https://8080-xxxxx.daytonaproxy01.net/admin
```

---

## 💻 روش دوم: نصب و اجرای محلی (Localhost)

### ۱. کلون کردن مخزن
```bash
git clone https://github.com/3krbkbkrbrbg/GLM-Free-API-Bridge.git
cd GLM-Free-API-Bridge
```

### ۲. تنظیم توکن
توکن کپی‌شده را داخل پوشه `.secrets` ذخیره کنید:
```bash
mkdir -p .secrets
echo "YOUR_ZAI_JWT_TOKEN" > .secrets/zai_token.txt
```
*(یا می‌توانید بعد از اجرای برنامه، توکن را مستقیماً از داخل داشبورد وب وارد کنید)*

### ۳. اجرا
```bash
python3 server.py
```

سرور روی آدرس `http://127.0.0.1:8080` در دسترس خواهد بود.

---

## 📊 داشبورد وب

پس از اجرا، مرورگر خود را باز کرده و به مسیر `/admin` بروید:
- در حالت محلی: `http://127.0.0.1:8080/admin`
- در حالت دایتونا: `https://YOUR_DAYTONA_URL/admin`

در این صفحه می‌توانید:
- وضعیت آنلاین بودن پروکسی را بررسی کنید.
- با مدل‌های مختلف GLM در بخش **API Playground** چت و گفتگو کنید.
- توکن نشست خود را بدون نیاز به ری‌استارت سرور به‌روزرسانی کنید.

---

## 📡 نحوه استفاده در کلاینت‌ها و برنامه‌ها

### تنظیمات اتصال (Base URL):
- **API Base URL**: `http://127.0.0.1:8080/v1` (یا آدرس دایتونا)
- **API Key**: هر رشته دلخواهی (مثلاً `sk-glm-local` یا `dummy`)

### نمونه درخواست با cURL:
```bash
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.7",
    "messages": [
      {"role": "user", "content": "سلام، خودت را معرفی کن."}
    ],
    "stream": true
  }'
```

### نمونه استفاده در پایتون (OpenAI SDK):
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="sk-dummy"
)

response = client.chat.completions.create(
    model="glm-4.7",
    messages=[{"role": "user", "content": "یک تابع پایتون برای مرتب‌سازی حبابی بنویس."}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## 📜 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.
