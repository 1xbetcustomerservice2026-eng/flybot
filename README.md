# ColdBet Bot — Python

## التشغيل

### 1. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 2. تعيين التوكن
```bash
export TELEGRAM_BOT_TOKEN="توكن البوت هنا"
```
أو على Windows:
```cmd
set TELEGRAM_BOT_TOKEN=توكن البوت هنا
```

### 3. تشغيل البوت
```bash
python main.py
```

## هيكل الملفات
```
coldbet_bot_py/
├── main.py              # نقطة البداية
├── requirements.txt
├── data/
│   ├── fly.jpg
│   ├── apple.jpg
│   ├── plane.jpg
│   └── bot_data.json    # يُنشأ تلقائياً
└── bot/
    ├── config.py        # الإعدادات والثوابت
    ├── database.py      # قاعدة البيانات (JSON)
    ├── messages.py      # نصوص الرسائل
    ├── keyboards.py     # لوحات المفاتيح
    └── bot.py           # المنطق الرئيسي
```
