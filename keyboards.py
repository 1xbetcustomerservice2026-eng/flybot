import random
from .config import APPS


def main_menu_keyboard(channel_invite: str) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "اشترك يا قلب أخوك 💙", "url": channel_invite}],
            [{"text": "✅ لقد اشتركت بالفعل", "callback_data": "check_sub"}],
        ]
    }


def apps_keyboard() -> dict:
    rows = []
    keys = list(APPS.keys())
    for i in range(0, len(keys), 2):
        row = []
        a1 = APPS[keys[i]]
        row.append({"text": f"{a1['emoji']} {a1['name']}", "callback_data": f"app_{keys[i]}"})
        if i + 1 < len(keys):
            a2 = APPS[keys[i + 1]]
            row.append({"text": f"{a2['emoji']} {a2['name']}", "callback_data": f"app_{keys[i + 1]}"})
        rows.append(row)
    return {"inline_keyboard": rows}


def app_actions_keyboard(
    app_key: str, is_vip: bool,
    vip_channel: str, support_username: str, guarantee_link: str
) -> dict:
    lock = "" if is_vip else "🔒 "
    plane_data = f"script_plane_{app_key}" if is_vip else "locked_feature"
    apple_data = f"script_apple_{app_key}" if is_vip else "locked_feature"
    rows = [
        [{"text": "📋 كيفية التسجيل", "callback_data": f"how_register_{app_key}"}],
        [
            {"text": f"{lock}✈️ اسكريبت الطيارة", "callback_data": plane_data},
            {"text": f"{lock}🍎 اسكريبت التفاحة", "callback_data": apple_data},
        ],
        [
            {"text": "🎟️ القسائم", "callback_data": f"vouchers_{app_key}"},
            {"text": "🎁 العروض",   "callback_data": f"offers_{app_key}"},
        ],
        [{"text": "🛡️ الضمان", "url": guarantee_link}],
    ]
    if is_vip:
        rows.append([{"text": "💎 قناة VIP", "url": vip_channel}])
    rows.append([{"text": "💬 تواصل مع الدعم", "url": f"https://t.me/{support_username.replace('@', '')}"}])
    rows.append([{"text": "📝 أريد التسجيل", "callback_data": f"register_{app_key}"}])
    return {"inline_keyboard": rows}


def cancel_keyboard(app_key: str) -> dict:
    return {"inline_keyboard": [[{"text": "❌ إلغاء", "callback_data": f"cancel_reg_{app_key}"}]]}


def plane_loading_keyboard(app_key: str) -> dict:
    return {"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": f"app_{app_key}"}]]}


def plane_result_keyboard(app_key: str) -> dict:
    return {
        "inline_keyboard": [[
            {"text": "🔄 RESTART", "callback_data": f"script_plane_{app_key}"},
            {"text": "🔙 رجوع",   "callback_data": f"app_{app_key}"},
        ]]
    }


def apple_loading_keyboard(app_key: str) -> dict:
    return {"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": f"app_{app_key}"}]]}


def apple_result_keyboard(app_key: str) -> dict:
    rows = []
    for _ in range(6):
        apple_pos = random.randint(0, 4)
        rows.append([
            {"text": "🍎" if col == apple_pos else "❌", "callback_data": "apple_cell"}
            for col in range(5)
        ])
    rows.append([
        {"text": "🔄 RESTART", "callback_data": f"apple_restart_{app_key}"},
        {"text": "🔙 رجوع",   "callback_data": f"app_{app_key}"},
    ])
    return {"inline_keyboard": rows}


def offers_list_keyboard(app_key: str, offers: list) -> dict:
    rows = [[{"text": o["name"], "callback_data": f"offer_view_{o['id']}"}] for o in offers]
    rows.append([{"text": "🔙 رجوع", "callback_data": f"app_{app_key}"}])
    return {"inline_keyboard": rows}


def vouchers_type_keyboard(app_key: str, is_vip: bool) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": f"{'💎' if is_vip else '🔒 💎'} قسائم VIP", "callback_data": f"vouchers_vip_{app_key}" if is_vip else "locked_feature"},
                {"text": "🎫 قسائم مجانية", "callback_data": f"vouchers_free_{app_key}"},
            ],
            [{"text": "🔙 رجوع", "callback_data": f"app_{app_key}"}],
        ]
    }


def vouchers_list_keyboard(app_key: str, vouchers: list, _type: str) -> dict:
    rows = [[{"text": f"{'💎 ' if v['type'] == 'vip' else '🎫 '}{v['name']}", "callback_data": f"voucher_view_{v['id']}"}] for v in vouchers]
    rows.append([{"text": "🔙 رجوع", "callback_data": f"vouchers_{app_key}"}])
    return {"inline_keyboard": rows}


def offer_view_keyboard(app_key: str) -> dict:
    return {"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": f"offers_{app_key}"}]]}


def voucher_view_keyboard(app_key: str) -> dict:
    return {"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": f"vouchers_{app_key}"}]]}


def admin_approve_keyboard(user_id: int) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "📋 نسخ المعرف", "callback_data": f"copy_uid_{user_id}"}],
            [{"text": "✅ قبول", "callback_data": f"admin_approve_{user_id}"}, {"text": "❌ رفض", "callback_data": f"admin_reject_{user_id}"}],
        ]
    }


def admin_main_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "📊 إحصائيات",             "callback_data": "admin_stats"}],
            [{"text": "📢 رسالة جماعية",         "callback_data": "admin_broadcast"}],
            [{"text": "💎 منح VIP",              "callback_data": "admin_grant_vip"}],
            [{"text": "🚫 إلغاء VIP",            "callback_data": "admin_revoke_vip"}],
            [{"text": "🎁 إضافة عرض",            "callback_data": "admin_add_offer"}],
            [{"text": "🎫 إضافة قسيمة مجانية",  "callback_data": "admin_add_voucher_free"}],
            [{"text": "💎 إضافة قسيمة VIP",     "callback_data": "admin_add_voucher_vip"}],
            [{"text": "🗑️ حذف عرض/قسيمة",      "callback_data": "admin_delete_item"}],
            [{"text": "🔗 تعديل الروابط",        "callback_data": "admin_edit_links"}],
            [{"text": "🔄 تغيير تطبيق مستخدم",  "callback_data": "admin_change_app"}],
            [{"text": "❌ إغلاق",               "callback_data": "admin_close"}],
        ]
    }


def admin_back_keyboard() -> dict:
    return {"inline_keyboard": [[{"text": "BACK ← رجوع للوحة الأدمن", "callback_data": "admin_panel"}]]}


def admin_apps_keyboard(prefix: str) -> dict:
    rows = [[{"text": f"{v['emoji']} {v['name']}", "callback_data": f"{prefix}{k}"}] for k, v in APPS.items()]
    rows.append([{"text": "BACK ← رجوع للوحة الأدمن", "callback_data": "admin_panel"}])
    return {"inline_keyboard": rows}


def edit_links_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "📡 رابط قناة الاشتراك الإجباري",   "callback_data": "editlink_channel"}],
            [{"text": "🔑 ID القناة (للتحقق من الاشتراك)", "callback_data": "editlink_channel_id"}],
            [{"text": "💎 رابط قناة VIP",                  "callback_data": "editlink_vip"}],
            [{"text": "🛡️ رابط الضمان",                    "callback_data": "editlink_guarantee"}],
            [{"text": "💬 يوزر الدعم",                     "callback_data": "editlink_support"}],
            [{"text": "BACK ← رجوع للوحة الأدمن",          "callback_data": "admin_panel"}],
        ]
    }


def skip_photo_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "⏭️ تخطي الصورة",               "callback_data": "admin_skip_photo"}],
            [{"text": "BACK ← رجوع للوحة الأدمن", "callback_data": "admin_panel"}],
        ]
    }
