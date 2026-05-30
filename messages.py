import random
from .config import APPS


def _esc_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def intro_msg(first_name: str) -> str:
    return (
        f"ازيك يا {first_name} 👋\n\n"
        "أولا انا هبقي صحبك وعاملني معاملة الصحاب\n\n"
        "انا واحد شخص مساعد يسعدك انك تعمل فلوس\n\n"
        "وسيبك من القنوات الي بتقولك تعالي وفي الاخر تلاقي نفسك خسرت كل حاجة وصاحب القناة حظرك\n\n"
        "ابدا معايا ومعايا ضمانات\n\n"
        "لو مش مصدق الفرصة مش بتيجي مرتين استغلها عشان تكسب 💪\n\n"
        "⬇️ اشترك في القناة الأول وبعدين ارجعلي ⬇️"
    )


def welcome_back_msg(first_name: str, user_id: int) -> str:
    return f"أهلاً بيك يا *{first_name}* 🦅\n\n🆔 معرفك: `{user_id}`\n\nاختر التطبيق اللي عاوز تشتغل بيه 👇"


def subscribed_msg(first_name: str, user_id: int) -> str:
    return (
        f"✅ *تم التحقق من اشتراكك!* 🦅\n\n"
        f"🆔 معرفك: `{user_id}`\n\n"
        f"أهلاً بيك يا *{first_name}* في عالم الكسب الحقيقي 🚀\n\n"
        "اختر التطبيق اللي عاوز تشتغل بيه 👇"
    )


def app_selected_msg(first_name: str, app_key: str, user_id: int) -> str:
    app = APPS[app_key]
    return (
        f"🦅 *مرحبًا بك يا {first_name}!*\n\n"
        f"🆔 معرفك: `{user_id}`\n\n"
        f"أكيد اخترت تبقى {app['emoji']} *{app['name']}* 🎯\n\n"
        f"عشان كده قدمتلك بروموكود خاص:\n\n"
        f"`{app['promo']}`\n\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "بص لو فضلت تعد المميزات من هنا للسنة الجاية مش هتخلص 😄\n\n"
        "1️⃣ بونص *200%* — ده حاجة أساسية\n\n"
        "2️⃣ حساب مكافأة 5 أضعاف الشحنة — لو شحنت 200 هيوصلك 1000 جنيه وأبعتلك أكواد تراكمية\n\n"
        "3️⃣ مفيش حاجة اسمها نصب أو احتيال — أنا بديك منتج لو استغليته هتعرف تجيب فلوس\n\n"
        "4️⃣ مكافآت الجمعة السعيدة، السبت الممتاز، الاثنين وكل مناسبة 🎂\n\n"
        "5️⃣ رهانات مجانية من 150 لـ 1700 جنيه ومسابقات طرش الطرش\n\n"
        "6️⃣ نتائج صحيحة وتراكميات مسربة وVIP — دمار شامل 💥\n\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "اختر من الأزرار أدناه 👇"
    )


def how_register_msg(app_key: str) -> str:
    app = APPS[app_key]
    return (
        f"🦅 📋 *طريقة التسجيل بالبروموكود — {app['emoji']} {app['name']}*\n\n"
        "1️⃣ اخرج من الحساب القديم — قوله أنت طالق بتلاتة وسيبه خالص 😂\n\n"
        "2️⃣ اضغط على تسجيل جنب تسجيل الدخول\n\n"
        "3️⃣ اضغط على نقرة واحدة\n\n"
        f"4️⃣ خانة الرمز الترويجي — حط: *{app['promo']}*\n\n"
        "5️⃣ وافق على كل الشروط\n\n"
        "6️⃣ اضغط على تسجيل\n\n"
        "7️⃣ اعمل سكرين شوت بالإيدي والباسورد واحفظه عندك 😅\n\n"
        "8️⃣ شحن 170 جنيه — وهذه خطوة أساسية\n\n"
        "9️⃣ ابعت الصور في زرار أريد التسجيل"
    )


def plane_loading_msg() -> str:
    return "✈️ *اسكريبت الطيارة*\n\n⏳ جاري التحليل..."


def plane_result_msg() -> str:
    values = ["1.43","2.07","3.51","1.88","4.22","2.73","5.10","1.31","6.05","2.34","1.62","3.18","7.40","1.95","2.88"]
    pick = random.choice(values)
    return f"✈️ *اسكريبت الطيارة*\n\n🎯 اسحب قبل: *{pick}x*"


def apple_loading_msg() -> str:
    return "🍎 *اسكريبت التفاحة*\n\n⏳ جاري التحليل..."


def apple_result_msg() -> str:
    return "🍎 *اسكريبت التفاحة*\n\n🎯 اختار التفاحة:"


def offers_empty_msg(app_key: str) -> str:
    app = APPS[app_key]
    return f"🎁 *عروض {app['emoji']} {app['name']}*\n\nلا توجد عروض متاحة حالياً\nتابعنا لأحدث العروض 📢"


def reg_step1_msg() -> str:
    return "🔑 *طلب التسجيل — الخطوة 1/3*\n\nمن فضلك أكتب الـ ID الخاص بك في التطبيق 👇"


def reg_step2_msg() -> str:
    return "📸 *طلب التسجيل — الخطوة 2/3*\n\nارسل سكرين شوت يوضح أنك سجلت بالبروموكود الصح 👇"


def reg_step3_msg() -> str:
    return "📸 *طلب التسجيل — الخطوة 3/3*\n\nارسل سكرين شوت يوضح عملية الإيداع 👇"


def pending_review_msg() -> str:
    return "✅ *تم إرسال طلبك للمراجعة!*\n\nسيتم مراجعة بياناتك وإخطارك بالنتيجة قريباً.\nشكراً على صبرك 🙏"


def approved_msg() -> str:
    return "🎉 *تهانينا! أخدت العضوية* 👑\n\n✅ تم قبول طلبك وتفعيل عضوية VIP!\n\nدلوقتي تقدر تدخل قناة VIP والاستمتاع بالاسكريبتات والتراكميات اليومية والمباع المميز ❤️ 🚀"


def rejected_msg() -> str:
    return "❌ *نأسف!*\n\nبعد مراجعة محتوياتك، فشل السيستم في تحديد هل أنت مسجل بالبروموكود ولا لا.\n\nتقدر تعيد المحاولة بالضغط على *أريد التسجيل* 👇"


def admin_request_msg(
    user_id: int, username: str | None, first_name: str | None,
    app_key: str, request_number: int, app_user_id: str | None = None
) -> str:
    app = APPS[app_key]
    name  = _esc_html(first_name or "غير معروف")
    uname = "@" + _esc_html(username) if username else "بدون يوزر"
    app_id = _esc_html(app_user_id or "غير محدد")
    return (
        f"📬 <b>طلب تسجيل جديد</b>\n\n"
        f"🔢 رقم الطلب: <b>#{request_number}</b>\n"
        f"👤 الاسم: {name}\n"
        f"🆔 المعرف: <code>{user_id}</code>\n"
        f"📛 اليوزر: {uname}\n"
        f"📱 التطبيق: {app['emoji']} {app['name']}\n"
        f"🔑 ID في التطبيق: {app_id}"
    )
