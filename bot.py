import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from .config import BOT_TOKEN, ADMIN_ID, APPS, FLY_IMAGE, APPLE_IMAGE, PLANE_IMAGE
from .database import (
    get_user, save_user, delete_user, get_all_users,
    add_pending_request, get_pending_requests,
    remove_pending_request,
    get_links, save_links,
    get_offers, add_offer, delete_offer,
    get_vouchers, add_voucher, delete_voucher,
    next_request_number,
)
from .keyboards import (
    main_menu_keyboard, apps_keyboard, app_actions_keyboard,
    cancel_keyboard,
    plane_loading_keyboard, plane_result_keyboard,
    apple_loading_keyboard, apple_result_keyboard,
    offers_list_keyboard, vouchers_type_keyboard, vouchers_list_keyboard,
    offer_view_keyboard, voucher_view_keyboard,
    admin_approve_keyboard, admin_main_keyboard, admin_back_keyboard,
    admin_apps_keyboard, edit_links_keyboard, skip_photo_keyboard,
)
from .messages import (
    intro_msg, welcome_back_msg, subscribed_msg, app_selected_msg,
    how_register_msg,
    plane_loading_msg, plane_result_msg,
    apple_loading_msg, apple_result_msg,
    offers_empty_msg,
    reg_step1_msg, reg_step2_msg, reg_step3_msg,
    pending_review_msg, approved_msg, rejected_msg,
    admin_request_msg,
)

# ── Simple logger ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _log_info(msg: str):
    logger.info(f"[INFO]  {datetime.now(timezone.utc).isoformat()} {msg}")

def _log_warn(msg: str):
    logger.warning(f"[WARN]  {datetime.now(timezone.utc).isoformat()} {msg}")


# ── Image file-id cache ───────────────────────────────────────────────────────
_fid: dict[str, str] = {}

bot: Optional[AsyncTeleBot] = None


async def _safe(coro):
    try:
        return await coro
    except Exception as e:
        _log_warn(f"tg-api: {e}")
        return None


async def _send_image(
    chat_id: int,
    img_key: str,   # "fly" | "apple" | "plane"
    caption: str,
    markup: Optional[dict] = None
) -> Optional[types.Message]:
    if img_key == "fly":
        img_path = FLY_IMAGE
    elif img_key == "apple":
        img_path = APPLE_IMAGE
    else:
        img_path = PLANE_IMAGE

    opts = {"caption": caption, "parse_mode": "Markdown"}
    if markup:
        opts["reply_markup"] = types.InlineKeyboardMarkup(
            keyboard=[[types.InlineKeyboardButton(**btn) for btn in row] for row in markup["inline_keyboard"]]
        )

    if _fid.get(img_key):
        return await _safe(bot.send_photo(chat_id, _fid[img_key], **opts))

    if not img_path.exists():
        return await _safe(bot.send_message(chat_id, caption, parse_mode="Markdown", reply_markup=opts.get("reply_markup")))

    with open(img_path, "rb") as f:
        res = await _safe(bot.send_photo(chat_id, f, **opts))
    if res and res.photo:
        _fid[img_key] = res.photo[-1].file_id
    return res


def _make_markup(markup_dict: Optional[dict]) -> Optional[types.InlineKeyboardMarkup]:
    if not markup_dict:
        return None
    return types.InlineKeyboardMarkup(
        keyboard=[[types.InlineKeyboardButton(**btn) for btn in row] for row in markup_dict["inline_keyboard"]]
    )


async def _edit_flow(
    chat_id: int,
    msg_id: Optional[int],
    caption: str,
    markup: dict,
    is_photo: bool
):
    kb = _make_markup(markup)
    if is_photo:
        return await _safe(bot.edit_message_caption(
            caption, chat_id=chat_id, message_id=msg_id,
            parse_mode="Markdown", reply_markup=kb
        ))
    return await _safe(bot.edit_message_text(
        caption, chat_id=chat_id, message_id=msg_id,
        parse_mode="Markdown", reply_markup=kb
    ))


def _is_photo_msg(m: Optional[types.Message]) -> bool:
    return bool(m and m.photo)


# ── Sessions ──────────────────────────────────────────────────────────────────
reg_sessions: dict[int, dict] = {}
# reg_session keys: appKey, step, appUserId, photos

admin_session: Optional[dict] = None   # keys: action, step, data{}

# ── Edit-links ForceReply markers ─────────────────────────────────────────────
EDITLINK_MARKERS = {
    "channelInvite":   "EDITLINK:channelInvite",
    "channelId":       "EDITLINK:channelId",
    "vipChannel":      "EDITLINK:vipChannel",
    "guaranteeLink":   "EDITLINK:guaranteeLink",
    "supportUsername": "EDITLINK:supportUsername",
}

EDITLINK_LABELS = {
    "channelInvite":   "رابط قناة الاشتراك",
    "channelId":       "ID القناة للتحقق",
    "vipChannel":      "قناة VIP",
    "guaranteeLink":   "رابط الضمان",
    "supportUsername": "يوزر الدعم",
}

EDITLINK_PROMPTS = {
    "channelInvite":   "📡 أرسل رابط قناة الاشتراك الجديدة:\n\n[EDITLINK:channelInvite]",
    "channelId":       "🔑 أرسل ID القناة للتحقق من الاشتراك:\n(مثال: -1001234567890)\n\n⚠️ البوت لازم يكون أدمن في القناة\n\n[EDITLINK:channelId]",
    "vipChannel":      "💎 أرسل رابط قناة VIP الجديدة:\n\n[EDITLINK:vipChannel]",
    "guaranteeLink":   "🛡️ أرسل رابط الضمان الجديد:\n\n[EDITLINK:guaranteeLink]",
    "supportUsername": "💬 أرسل يوزر الدعم الجديد (مثال: @TAMER_VIP):\n\n[EDITLINK:supportUsername]",
}


# ── Subscription check ────────────────────────────────────────────────────────
async def _check_subscription(user_id: int) -> bool:
    if not bot:
        return False
    l = get_links()
    target = l["channelId"].strip() if l["channelId"] and l["channelId"].strip() else l["channelInvite"]
    try:
        m = await bot.get_chat_member(target, user_id)
        return m.status in ("member", "administrator", "creator")
    except Exception:
        return True


def _links():
    return get_links()


async def _show_app(chat_id: int, msg_id: Optional[int], first_name: str, app_key: str, user_id: int):
    if msg_id:
        await _safe(bot.delete_message(chat_id, msg_id))
    user = get_user(user_id)
    l = _links()
    await _send_image(
        chat_id, "fly", app_selected_msg(first_name, app_key, user_id),
        app_actions_keyboard(app_key, bool(user and user.get("isVip")), l["vipChannel"], l["supportUsername"], l["guaranteeLink"])
    )


async def _send_edit_link_prompt(chat_id: int, field: str):
    prompt = EDITLINK_PROMPTS.get(field, f"أرسل القيمة الجديدة:\n\n[EDITLINK:{field}]")
    await _safe(bot.send_message(chat_id, prompt, reply_markup=types.ForceReply(selective=True)))


# ── Start bot ─────────────────────────────────────────────────────────────────
def start_bot():
    global bot, admin_session

    if not BOT_TOKEN:
        _log_warn("TELEGRAM_BOT_TOKEN not set — bot will not start")
        return

    bot = AsyncTeleBot(BOT_TOKEN)
    _log_info("Telegram bot started")

    # ── /start ──────────────────────────────────────────────────────────────
    @bot.message_handler(commands=["start"])
    async def handle_start(msg: types.Message):
        user_id    = msg.from_user.id
        first_name = msg.from_user.first_name or "صديقي"
        username   = msg.from_user.username
        user = get_user(user_id)
        if not user:
            user = {"userId": user_id, "username": username, "firstName": first_name}
            save_user(user)
        if not user.get("hasSeenWelcome"):
            user["hasSeenWelcome"] = True
            save_user(user)
            await _send_image(user_id, "fly", intro_msg(first_name), main_menu_keyboard(_links()["channelInvite"]))
            return
        if user.get("selectedApp") and APPS.get(user["selectedApp"]):
            await _show_app(user_id, None, first_name, user["selectedApp"], user_id)
        else:
            await _send_image(user_id, "fly", welcome_back_msg(first_name, user_id), apps_keyboard())

    # ── /admin ──────────────────────────────────────────────────────────────
    @bot.message_handler(commands=["admin"])
    async def handle_admin(msg: types.Message):
        if msg.from_user.id != ADMIN_ID:
            return
        await _safe(bot.send_message(
            ADMIN_ID, "🔐 *لوحة التحكم*\n\nأهلاً بيك يا أدمن 👇",
            parse_mode="Markdown", reply_markup=_make_markup(admin_main_keyboard())
        ))

    # ── Callback queries ─────────────────────────────────────────────────────
    @bot.callback_query_handler(func=lambda q: True)
    async def handle_callback(query: types.CallbackQuery):
        global admin_session
        user_id    = query.from_user.id
        first_name = query.from_user.first_name or "صديقي"
        data       = query.data or ""
        msg_id     = query.message.message_id if query.message else None
        chat_id    = query.message.chat.id if query.message else user_id
        is_photo   = _is_photo_msg(query.message)
        l          = _links()

        if data == "locked_feature":
            await _safe(bot.answer_callback_query(query.id,
                text="🔒 هذه الميزة للأعضاء VIP فقط — سجل واحصل على VIP!",
                show_alert=True
            ))
            return
        if data == "apple_cell":
            await _safe(bot.answer_callback_query(query.id))
            return

        await _safe(bot.answer_callback_query(query.id))

        if data == "check_sub":
            ok = await _check_subscription(user_id)
            if not ok:
                if msg_id:
                    await _safe(bot.delete_message(chat_id, msg_id))
                await _send_image(chat_id, "fly",
                    "❌ *لسه مش مشترك!*\n\nاشترك في القناة الأول ثم اضغط مرة تانية 👇",
                    main_menu_keyboard(l["channelInvite"]))
                return
            user = get_user(user_id)
            if not user:
                user = {"userId": user_id, "username": query.from_user.username, "firstName": first_name}
                save_user(user)
            if msg_id:
                await _safe(bot.delete_message(chat_id, msg_id))
            await _send_image(chat_id, "fly", subscribed_msg(first_name, user_id), apps_keyboard())
            return

        if data == "admin_panel" and user_id == ADMIN_ID:
            admin_session = None
            await _safe(bot.send_message(ADMIN_ID, "🔐 *لوحة التحكم*",
                parse_mode="Markdown", reply_markup=_make_markup(admin_main_keyboard())
            ))
            return

        if data.startswith("cancel_reg_"):
            reg_sessions.pop(user_id, None)
            await _show_app(chat_id, msg_id, first_name, data.replace("cancel_reg_", ""), user_id)
            return

        if data.startswith("app_"):
            app_key = data.replace("app_", "")
            if app_key not in APPS:
                return
            user = get_user(user_id) or {"userId": user_id, "username": query.from_user.username, "firstName": first_name}
            user["selectedApp"] = app_key
            save_user(user)
            await _show_app(chat_id, msg_id, first_name, app_key, user_id)
            return

        if data.startswith("how_register_"):
            app_key = data.replace("how_register_", "")
            await _edit_flow(chat_id, msg_id, how_register_msg(app_key), {
                "inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": f"app_{app_key}"}]]
            }, is_photo)
            return

        if data.startswith("offers_"):
            app_key = data.replace("offers_", "")
            offers = get_offers(app_key)
            if not offers:
                await _edit_flow(chat_id, msg_id, offers_empty_msg(app_key), {
                    "inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": f"app_{app_key}"}]]
                }, is_photo)
            else:
                await _edit_flow(chat_id, msg_id, "🎁 *اختر من العروض التالية:*", offers_list_keyboard(app_key, offers), is_photo)
            return

        if data.startswith("offer_view_"):
            offer = next((o for o in get_offers() if o["id"] == data.replace("offer_view_", "")), None)
            if not offer:
                return
            text = f"🎁 *{offer['name']}*\n\n{offer['description']}"
            if offer.get("photoFileId"):
                await _safe(bot.send_photo(chat_id, offer["photoFileId"], caption=text, parse_mode="Markdown", reply_markup=_make_markup(offer_view_keyboard(offer["appKey"]))))
            else:
                await _edit_flow(chat_id, msg_id, text, offer_view_keyboard(offer["appKey"]), is_photo)
            return

        if data.startswith("vouchers_") and not data.startswith("vouchers_vip_") and not data.startswith("vouchers_free_"):
            app_key = data.replace("vouchers_", "")
            user = get_user(user_id)
            await _edit_flow(chat_id, msg_id, "🎟️ *القسائم — اختر النوع:*",
                vouchers_type_keyboard(app_key, bool(user and user.get("isVip"))), is_photo)
            return

        if data.startswith("vouchers_vip_"):
            app_key = data.replace("vouchers_vip_", "")
            vs = get_vouchers(app_key, "vip")
            await _edit_flow(chat_id, msg_id,
                "💎 *قسائم VIP:*" if vs else "💎 *لا توجد قسائم VIP حالياً*",
                vouchers_list_keyboard(app_key, vs, "vip") if vs else {"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": f"vouchers_{app_key}"}]]},
                is_photo)
            return

        if data.startswith("vouchers_free_"):
            app_key = data.replace("vouchers_free_", "")
            vs = get_vouchers(app_key, "free")
            await _edit_flow(chat_id, msg_id,
                "🎫 *قسائم مجانية:*" if vs else "🎫 *لا توجد قسائم مجانية حالياً*",
                vouchers_list_keyboard(app_key, vs, "free") if vs else {"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": f"vouchers_{app_key}"}]]},
                is_photo)
            return

        if data.startswith("voucher_view_"):
            voucher = next((v for v in get_vouchers() if v["id"] == data.replace("voucher_view_", "")), None)
            if not voucher:
                return
            text = f"🎟️ *{voucher['name']}*\n\n{voucher['description']}"
            if voucher.get("photoFileId"):
                await _safe(bot.send_photo(chat_id, voucher["photoFileId"], caption=text, parse_mode="Markdown", reply_markup=_make_markup(voucher_view_keyboard(voucher["appKey"]))))
            else:
                await _edit_flow(chat_id, msg_id, text, voucher_view_keyboard(voucher["appKey"]), is_photo)
            return

        if data.startswith("script_plane_"):
            app_key = data.replace("script_plane_", "")
            if msg_id:
                await _safe(bot.delete_message(chat_id, msg_id))
            pm = await _send_image(chat_id, "plane", plane_loading_msg(), plane_loading_keyboard(app_key))
            pm_id = pm.message_id if pm else None
            pm_photo = _is_photo_msg(pm)
            if pm_id:
                async def _plane_result():
                    await asyncio.sleep(3)
                    await _edit_flow(chat_id, pm_id, plane_result_msg(), plane_result_keyboard(app_key), pm_photo)
                asyncio.create_task(_plane_result())
            return

        if data.startswith("script_apple_"):
            app_key = data.replace("script_apple_", "")
            if msg_id:
                await _safe(bot.delete_message(chat_id, msg_id))
            am = await _send_image(chat_id, "apple", apple_loading_msg(), apple_loading_keyboard(app_key))
            am_id = am.message_id if am else None
            am_photo = _is_photo_msg(am)
            if am_id:
                async def _apple_result():
                    await asyncio.sleep(2)
                    await _edit_flow(chat_id, am_id, apple_result_msg(), apple_result_keyboard(app_key), am_photo)
                asyncio.create_task(_apple_result())
            return

        if data.startswith("apple_restart_"):
            app_key = data.replace("apple_restart_", "")
            await _edit_flow(chat_id, msg_id, apple_loading_msg(), apple_loading_keyboard(app_key), is_photo)
            if msg_id:
                async def _apple_restart():
                    await asyncio.sleep(2)
                    await _edit_flow(chat_id, msg_id, apple_result_msg(), apple_result_keyboard(app_key), is_photo)
                asyncio.create_task(_apple_restart())
            return

        if data.startswith("register_"):
            app_key = data.replace("register_", "")
            reg_sessions[user_id] = {"appKey": app_key, "step": "waiting_id", "photos": []}
            if msg_id:
                await _safe(bot.delete_message(chat_id, msg_id))
            await _send_image(chat_id, "fly", reg_step1_msg(), cancel_keyboard(app_key))
            return

        # ══ ADMIN ONLY ════════════════════════════════════════════════════════
        if user_id != ADMIN_ID:
            return

        if data.startswith("copy_uid_"):
            await _safe(bot.answer_callback_query(query.id,
                text=f"المعرف: {data.replace('copy_uid_', '')}", show_alert=True
            ))
            return

        if data == "admin_stats":
            users = get_all_users()
            pending = get_pending_requests()
            await _safe(bot.send_message(chat_id,
                f"📊 *إحصائيات البوت*\n\n👥 المستخدمين: *{len(users)}*\n👑 VIP: *{sum(1 for u in users if u.get('isVip'))}*\n📋 طلبات معلقة: *{len(pending)}*",
                parse_mode="Markdown", reply_markup=_make_markup(admin_main_keyboard())
            ))
            return

        if data == "admin_broadcast":
            admin_session = {"action": "broadcast", "step": "waiting_message", "data": {}}
            await _safe(bot.send_message(chat_id,
                "📢 ابعت الرسالة اللي عاوز ترسلها للكل:\n(يمكن إرفاق صورة)",
                reply_markup=_make_markup(admin_back_keyboard())
            ))
            return

        if data == "admin_grant_vip":
            admin_session = {"action": "grant_vip", "step": "waiting_id", "data": {}}
            await _safe(bot.send_message(chat_id, "💎 ابعت الـ ID بتاع المستخدم اللي عاوز تديه VIP:", reply_markup=_make_markup(admin_back_keyboard())))
            return

        if data == "admin_revoke_vip":
            admin_session = {"action": "revoke_vip", "step": "waiting_id", "data": {}}
            await _safe(bot.send_message(chat_id, "🚫 ابعت الـ ID بتاع المستخدم اللي عاوز تلغي VIP بتاعه:", reply_markup=_make_markup(admin_back_keyboard())))
            return

        if data == "admin_add_offer":
            await _safe(bot.send_message(chat_id, "🎁 *إضافة عرض — اختر التطبيق:*", parse_mode="Markdown", reply_markup=_make_markup(admin_apps_keyboard("addoffer_app_"))))
            return

        if data.startswith("addoffer_app_"):
            app_key = data.replace("addoffer_app_", "")
            admin_session = {"action": "add_offer", "step": "waiting_name", "data": {"appKey": app_key}}
            await _safe(bot.send_message(chat_id,
                f"🎁 عرض جديد لـ *{APPS[app_key]['name']}*\n\nابعت *اسم العرض*:",
                parse_mode="Markdown", reply_markup=_make_markup(admin_back_keyboard())
            ))
            return

        if data == "admin_add_voucher_free":
            await _safe(bot.send_message(chat_id, "🎫 *إضافة قسيمة مجانية — اختر التطبيق:*", parse_mode="Markdown", reply_markup=_make_markup(admin_apps_keyboard("addvoucherfree_app_"))))
            return

        if data.startswith("addvoucherfree_app_"):
            app_key = data.replace("addvoucherfree_app_", "")
            admin_session = {"action": "add_voucher_free", "step": "waiting_name", "data": {"appKey": app_key, "type": "free"}}
            await _safe(bot.send_message(chat_id,
                f"🎫 قسيمة مجانية لـ *{APPS[app_key]['name']}*\n\nابعت *اسم القسيمة*:",
                parse_mode="Markdown", reply_markup=_make_markup(admin_back_keyboard())
            ))
            return

        if data == "admin_add_voucher_vip":
            await _safe(bot.send_message(chat_id, "💎 *إضافة قسيمة VIP — اختر التطبيق:*", parse_mode="Markdown", reply_markup=_make_markup(admin_apps_keyboard("addvouchervip_app_"))))
            return

        if data.startswith("addvouchervip_app_"):
            app_key = data.replace("addvouchervip_app_", "")
            admin_session = {"action": "add_voucher_vip", "step": "waiting_name", "data": {"appKey": app_key, "type": "vip"}}
            await _safe(bot.send_message(chat_id,
                f"💎 قسيمة VIP لـ *{APPS[app_key]['name']}*\n\nابعت *اسم القسيمة*:",
                parse_mode="Markdown", reply_markup=_make_markup(admin_back_keyboard())
            ))
            return

        if data == "admin_skip_photo":
            if not admin_session:
                return
            s = admin_session
            admin_session = None
            item_id = str(int(time.time() * 1000))
            if s["action"] == "add_offer":
                add_offer({"id": item_id, "appKey": s["data"]["appKey"], "name": s["data"]["name"], "description": s["data"]["desc"]})
                await _safe(bot.send_message(chat_id, f"✅ تم حفظ العرض: *{s['data']['name']}*", parse_mode="Markdown", reply_markup=_make_markup(admin_main_keyboard())))
            else:
                add_voucher({"id": item_id, "appKey": s["data"]["appKey"], "type": s["data"]["type"], "name": s["data"]["name"], "description": s["data"]["desc"]})
                await _safe(bot.send_message(chat_id, f"✅ تم حفظ القسيمة: *{s['data']['name']}*", parse_mode="Markdown", reply_markup=_make_markup(admin_main_keyboard())))
            return

        if data == "admin_delete_item":
            offers = get_offers()
            vouchers = get_vouchers()
            rows = []
            for o in offers:
                rows.append([{"text": f"🗑️ عرض: {o['name']} ({APPS.get(o['appKey'], {}).get('name', o['appKey'])})", "callback_data": f"del_offer_{o['id']}"}])
            for v in vouchers:
                rows.append([{"text": f"🗑️ قسيمة: {v['name']} ({APPS.get(v['appKey'], {}).get('name', v['appKey'])})", "callback_data": f"del_voucher_{v['id']}"}])
            rows.append([{"text": "BACK ← رجوع للوحة الأدمن", "callback_data": "admin_panel"}])
            if len(rows) == 1:
                await _safe(bot.send_message(chat_id, "🗑️ لا توجد عناصر للحذف", reply_markup=_make_markup(admin_main_keyboard())))
            else:
                await _safe(bot.send_message(chat_id, "🗑️ *اختر العنصر للحذف:*", parse_mode="Markdown", reply_markup=_make_markup({"inline_keyboard": rows})))
            return

        if data.startswith("del_offer_"):
            delete_offer(data.replace("del_offer_", ""))
            await _safe(bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=types.InlineKeyboardMarkup()))
            await _safe(bot.send_message(chat_id, "✅ تم حذف العرض", reply_markup=_make_markup(admin_main_keyboard())))
            return

        if data.startswith("del_voucher_"):
            delete_voucher(data.replace("del_voucher_", ""))
            await _safe(bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=types.InlineKeyboardMarkup()))
            await _safe(bot.send_message(chat_id, "✅ تم حذف القسيمة", reply_markup=_make_markup(admin_main_keyboard())))
            return

        if data == "admin_edit_links":
            cl = _links()
            cid_display = cl["channelId"].strip() if cl["channelId"] and cl["channelId"].strip() else "غير محدد"
            await _safe(bot.send_message(chat_id,
                f"🔗 الروابط الحالية:\n\n📡 الاشتراك: {cl['channelInvite']}\n🔑 ID القناة: {cid_display}\n💎 VIP: {cl['vipChannel']}\n🛡️ الضمان: {cl['guaranteeLink']}\n💬 الدعم: {cl['supportUsername']}\n\nاختر ما تريد تعديله 👇",
                reply_markup=_make_markup(edit_links_keyboard())
            ))
            return

        if data == "editlink_channel":    await _send_edit_link_prompt(chat_id, "channelInvite");   return
        if data == "editlink_channel_id": await _send_edit_link_prompt(chat_id, "channelId");       return
        if data == "editlink_vip":        await _send_edit_link_prompt(chat_id, "vipChannel");      return
        if data == "editlink_guarantee":  await _send_edit_link_prompt(chat_id, "guaranteeLink");   return
        if data == "editlink_support":    await _send_edit_link_prompt(chat_id, "supportUsername"); return

        if data == "admin_change_app":
            await _safe(bot.send_message(chat_id, "🔄 *تغيير تطبيق مستخدم — اختر التطبيق الجديد:*", parse_mode="Markdown", reply_markup=_make_markup(admin_apps_keyboard("changeapp_app_"))))
            return

        if data.startswith("changeapp_app_"):
            app_key = data.replace("changeapp_app_", "")
            admin_session = {"action": "change_app", "step": "waiting_id", "data": {"appKey": app_key}}
            await _safe(bot.send_message(chat_id,
                f"🔄 تغيير إلى *{APPS[app_key]['name']}*\n\nابعت ID المستخدم:",
                parse_mode="Markdown", reply_markup=_make_markup(admin_back_keyboard())
            ))
            return

        if data == "admin_close":
            if msg_id:
                await _safe(bot.delete_message(chat_id, msg_id))
            return

        if data.startswith("admin_approve_"):
            target_id = int(data.replace("admin_approve_", "")) if data.replace("admin_approve_", "").isdigit() else None
            if not target_id:
                return
            user = get_user(target_id) or {"userId": target_id}
            user["isVip"] = True
            user["vipExpiry"] = int(time.time() * 1000) + 30 * 24 * 60 * 60 * 1000
            save_user(user)
            remove_pending_request(target_id)
            await _safe(bot.send_message(target_id, approved_msg(), parse_mode="Markdown"))
            await _safe(bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=types.InlineKeyboardMarkup()))
            await _safe(bot.send_message(chat_id, f"✅ تم قبول المستخدم {user.get('firstName', target_id)}", reply_markup=_make_markup(admin_main_keyboard())))
            return

        if data.startswith("admin_reject_"):
            target_id = int(data.replace("admin_reject_", "")) if data.replace("admin_reject_", "").isdigit() else None
            if not target_id:
                return
            user = get_user(target_id)
            remove_pending_request(target_id)
            await _send_image(target_id, "fly", rejected_msg(), {
                "inline_keyboard": [[
                    {"text": "💬 تواصل مع الدعم", "url": f"https://t.me/{_links()['supportUsername'].replace('@', '')}"},
                    {"text": "📝 أريد التسجيل", "callback_data": f"register_{user['selectedApp'] if user else 'coldbet'}"},
                ]]
            })
            await _safe(bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=types.InlineKeyboardMarkup()))
            await _safe(bot.send_message(chat_id, f"❌ تم رفض المستخدم {user.get('firstName', target_id) if user else target_id}", reply_markup=_make_markup(admin_main_keyboard())))
            return

    # ── Photos ────────────────────────────────────────────────────────────────
    @bot.message_handler(content_types=["photo"])
    async def handle_photo(msg: types.Message):
        global admin_session
        user_id    = msg.from_user.id
        first_name = msg.from_user.first_name or "صديقي"
        photo_arr  = msg.photo
        if not photo_arr:
            return
        file_id = photo_arr[-1].file_id

        reg = reg_sessions.get(user_id)
        if reg:
            if reg["step"] == "waiting_reg_photo":
                reg["photos"].append(file_id)
                reg["step"] = "waiting_deposit_photo"
                reg_sessions[user_id] = reg
                await _send_image(user_id, "fly", reg_step3_msg(), cancel_keyboard(reg["appKey"]))
                return
            if reg["step"] == "waiting_deposit_photo":
                reg["photos"].append(file_id)
                reg_sessions.pop(user_id, None)
                req_num = next_request_number()
                add_pending_request({
                    "userId": user_id, "username": msg.from_user.username,
                    "firstName": msg.from_user.first_name, "appKey": reg["appKey"],
                    "appUserId": reg.get("appUserId"), "timestamp": int(time.time() * 1000),
                    "fileIds": reg["photos"], "requestNumber": req_num
                })
                await _send_image(user_id, "fly", pending_review_msg(), None)
                if reg["photos"]:
                    await _safe(bot.send_photo(ADMIN_ID, reg["photos"][0]))
                if len(reg["photos"]) > 1:
                    await _safe(bot.send_photo(ADMIN_ID, reg["photos"][1]))
                await _safe(bot.send_message(ADMIN_ID,
                    admin_request_msg(user_id, msg.from_user.username, first_name, reg["appKey"], req_num, reg.get("appUserId")),
                    parse_mode="HTML", reply_markup=_make_markup(admin_approve_keyboard(user_id))
                ))
                return

        if user_id == ADMIN_ID and admin_session:
            s = admin_session
            if s["action"] in ("add_offer", "add_voucher_free", "add_voucher_vip") and s["step"] == "waiting_photo":
                admin_session = None
                item_id = str(int(time.time() * 1000))
                if s["action"] == "add_offer":
                    add_offer({"id": item_id, "appKey": s["data"]["appKey"], "name": s["data"]["name"], "description": s["data"]["desc"], "photoFileId": file_id})
                    await _safe(bot.send_message(ADMIN_ID, f"✅ تم حفظ العرض مع الصورة: *{s['data']['name']}*", parse_mode="Markdown", reply_markup=_make_markup(admin_main_keyboard())))
                else:
                    add_voucher({"id": item_id, "appKey": s["data"]["appKey"], "type": s["data"]["type"], "name": s["data"]["name"], "description": s["data"]["desc"], "photoFileId": file_id})
                    await _safe(bot.send_message(ADMIN_ID, f"✅ تم حفظ القسيمة مع الصورة: *{s['data']['name']}*", parse_mode="Markdown", reply_markup=_make_markup(admin_main_keyboard())))
                return
            if s["action"] == "broadcast" and s["step"] == "waiting_message":
                admin_session = None
                caption = msg.caption or "📢 رسالة من أخوك 🦅"
                sent = 0
                for u in get_all_users():
                    ok = await _safe(bot.send_photo(u["userId"], file_id, caption=f"📢 *رسالة من أخوك 🦅*\n\n{caption}", parse_mode="Markdown"))
                    if ok:
                        sent += 1
                await _safe(bot.send_message(ADMIN_ID, f"✅ تم الإرسال لـ {sent} مستخدم", reply_markup=_make_markup(admin_main_keyboard())))
                return

    # ── Text messages ─────────────────────────────────────────────────────────
    @bot.message_handler(func=lambda m: m.content_type == "text" and not m.text.startswith("/"))
    async def handle_text(msg: types.Message):
        global admin_session
        user_id = msg.from_user.id
        text    = msg.text
        if not text:
            return

        # ── Edit-link reply handler (ForceReply, stateless) ───────────────────
        if user_id == ADMIN_ID and msg.reply_to_message:
            reply_text = msg.reply_to_message.text or ""
            matched_field = None
            for field, marker in EDITLINK_MARKERS.items():
                if marker in reply_text:
                    matched_field = field
                    break
            if matched_field:
                value = text.strip()
                save_links({matched_field: value})
                label = EDITLINK_LABELS.get(matched_field, matched_field)
                await _safe(bot.send_message(ADMIN_ID,
                    f"✅ تم تحديث {label}\n\nالقيمة الجديدة:\n{value}",
                    reply_markup=_make_markup(admin_main_keyboard())
                ))
                return

        # ── User registration step 1 ──────────────────────────────────────────
        reg = reg_sessions.get(user_id)
        if reg and reg["step"] == "waiting_id":
            reg["appUserId"] = text.strip()
            reg["step"] = "waiting_reg_photo"
            reg_sessions[user_id] = reg
            await _send_image(user_id, "fly", reg_step2_msg(), cancel_keyboard(reg["appKey"]))
            return

        # ── Admin session actions ─────────────────────────────────────────────
        if user_id != ADMIN_ID:
            return
        if not admin_session:
            return
        s = admin_session

        if s["action"] == "broadcast" and s["step"] == "waiting_message":
            admin_session = None
            sent = 0
            for u in get_all_users():
                ok = await _safe(bot.send_message(u["userId"], f"📢 *رسالة من أخوك 🦅*\n\n{text}", parse_mode="Markdown"))
                if ok:
                    sent += 1
            await _safe(bot.send_message(ADMIN_ID, f"✅ تم الإرسال لـ {sent} مستخدم", reply_markup=_make_markup(admin_main_keyboard())))
            return

        if s["action"] == "grant_vip" and s["step"] == "waiting_id":
            admin_session = None
            target_id_str = text.strip()
            if not target_id_str.isdigit():
                await _safe(bot.send_message(ADMIN_ID, "❌ ID غلط، حاول تاني", reply_markup=_make_markup(admin_main_keyboard())))
                return
            target_id = int(target_id_str)
            user = get_user(target_id) or {"userId": target_id}
            user["isVip"] = True
            user["vipExpiry"] = int(time.time() * 1000) + 30 * 24 * 60 * 60 * 1000
            save_user(user)
            await _safe(bot.send_message(ADMIN_ID, f"✅ تم منح VIP للمستخدم {target_id}", reply_markup=_make_markup(admin_main_keyboard())))
            await _safe(bot.send_message(target_id, approved_msg(), parse_mode="Markdown"))
            return

        if s["action"] == "revoke_vip" and s["step"] == "waiting_id":
            admin_session = None
            target_id_str = text.strip()
            if not target_id_str.isdigit():
                await _safe(bot.send_message(ADMIN_ID, "❌ ID غلط، حاول تاني", reply_markup=_make_markup(admin_main_keyboard())))
                return
            target_id = int(target_id_str)
            user = get_user(target_id)
            if user:
                user["isVip"] = False
                user.pop("vipExpiry", None)
                save_user(user)
            await _safe(bot.send_message(ADMIN_ID, f"✅ تم إلغاء VIP للمستخدم {target_id}", reply_markup=_make_markup(admin_main_keyboard())))
            await _safe(bot.send_message(target_id, f"⚠️ تم إلغاء عضويتك VIP. للاستفسار: {_links()['supportUsername']}"))
            return

        if s["action"] in ("add_offer", "add_voucher_free", "add_voucher_vip"):
            if s["step"] == "waiting_name":
                s["data"]["name"] = text.strip()
                s["step"] = "waiting_desc"
                admin_session = s
                await _safe(bot.send_message(ADMIN_ID, "✍️ ابعت *وصف* العنصر:", parse_mode="Markdown", reply_markup=_make_markup(admin_back_keyboard())))
                return
            if s["step"] == "waiting_desc":
                s["data"]["desc"] = text.strip()
                s["step"] = "waiting_photo"
                admin_session = s
                await _safe(bot.send_message(ADMIN_ID, "📸 ارسل صورة للعنصر أو اضغط تخطي:", reply_markup=_make_markup(skip_photo_keyboard())))
                return

        if s["action"] == "change_app" and s["step"] == "waiting_id":
            admin_session = None
            target_id_str = text.strip()
            if not target_id_str.isdigit():
                await _safe(bot.send_message(ADMIN_ID, "❌ ID غلط، حاول تاني", reply_markup=_make_markup(admin_main_keyboard())))
                return
            target_id = int(target_id_str)
            app_key = s["data"]["appKey"]
            delete_user(target_id)
            save_user({"userId": target_id, "hasSeenWelcome": True, "selectedApp": app_key})
            await _safe(bot.send_message(ADMIN_ID, f"✅ تم تغيير تطبيق المستخدم {target_id} إلى *{APPS[app_key]['name']}*", parse_mode="Markdown", reply_markup=_make_markup(admin_main_keyboard())))
            await _safe(bot.send_message(target_id, f"🔄 تم تحديث حسابك! ابعت /start للبدء مع {APPS[app_key]['emoji']} *{APPS[app_key]['name']}*", parse_mode="Markdown"))
            return

    asyncio.run(bot.infinity_polling())
