import json
import os
from pathlib import Path
from typing import Optional, TypedDict, Literal

from .config import (
    DEFAULT_CHANNEL_INVITE, DEFAULT_VIP_CHANNEL,
    DEFAULT_SUPPORT_USERNAME, DEFAULT_CHANNEL_ID, DEFAULT_GUARANTEE_LINK,
)

_BASE_DIR = Path(__file__).parent.parent
DB_PATH = _BASE_DIR / "data" / "bot_data.json"


class UserData(TypedDict, total=False):
    userId: int
    username: str
    firstName: str
    selectedApp: str
    isVip: bool
    vipExpiry: int
    hasSeenWelcome: bool


class OfferItem(TypedDict, total=False):
    id: str
    appKey: str
    name: str
    description: str
    photoFileId: str


class VoucherItem(TypedDict, total=False):
    id: str
    appKey: str
    type: Literal["free", "vip"]
    name: str
    description: str
    photoFileId: str


class BotLinks(TypedDict, total=False):
    channelInvite: str
    vipChannel: str
    supportUsername: str
    channelId: str
    guaranteeLink: str


class PendingRequest(TypedDict, total=False):
    userId: int
    username: str
    firstName: str
    appKey: str
    timestamp: int
    appUserId: str
    fileIds: list[str]
    requestNumber: int


def _ensure_dir():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_db() -> dict:
    _ensure_dir()
    if not DB_PATH.exists():
        return {"users": {}, "pendingRequests": [], "offers": [], "vouchers": [], "requestCounter": 0}
    try:
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"users": {}, "pendingRequests": [], "offers": [], "vouchers": [], "requestCounter": 0}


def _save_db(db: dict) -> None:
    _ensure_dir()
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def get_user(user_id: int) -> Optional[UserData]:
    return _load_db()["users"].get(str(user_id))


def save_user(user: UserData) -> None:
    db = _load_db()
    db["users"][str(user["userId"])] = user
    _save_db(db)


def delete_user(user_id: int) -> None:
    db = _load_db()
    db["users"].pop(str(user_id), None)
    db["pendingRequests"] = [r for r in db["pendingRequests"] if r["userId"] != user_id]
    _save_db(db)


def get_all_users() -> list[UserData]:
    return list(_load_db()["users"].values())


def next_request_number() -> int:
    db = _load_db()
    num = (db.get("requestCounter") or 0) + 1
    db["requestCounter"] = num
    _save_db(db)
    return num


def add_pending_request(req: PendingRequest) -> None:
    db = _load_db()
    db["pendingRequests"] = [r for r in db["pendingRequests"] if r["userId"] != req["userId"]]
    db["pendingRequests"].append(req)
    _save_db(db)


def get_pending_requests() -> list[PendingRequest]:
    return _load_db()["pendingRequests"]


def remove_pending_request(user_id: int) -> None:
    db = _load_db()
    db["pendingRequests"] = [r for r in db["pendingRequests"] if r["userId"] != user_id]
    _save_db(db)


def get_pending_request(user_id: int) -> Optional[PendingRequest]:
    return next((r for r in _load_db()["pendingRequests"] if r["userId"] == user_id), None)


def get_links() -> dict:
    db = _load_db()
    links = db.get("links") or {}
    return {
        "channelInvite":   links.get("channelInvite")   or DEFAULT_CHANNEL_INVITE,
        "vipChannel":      links.get("vipChannel")       or DEFAULT_VIP_CHANNEL,
        "supportUsername": links.get("supportUsername")  or DEFAULT_SUPPORT_USERNAME,
        "channelId":       links.get("channelId")        or DEFAULT_CHANNEL_ID,
        "guaranteeLink":   links.get("guaranteeLink")    or DEFAULT_GUARANTEE_LINK,
    }


def save_links(links: dict) -> None:
    db = _load_db()
    db["links"] = {**(db.get("links") or {}), **links}
    _save_db(db)


def get_offers(app_key: Optional[str] = None) -> list[OfferItem]:
    db = _load_db()
    all_offers = db.get("offers") or []
    return [o for o in all_offers if o["appKey"] == app_key] if app_key else all_offers


def add_offer(offer: OfferItem) -> None:
    db = _load_db()
    if not db.get("offers"):
        db["offers"] = []
    db["offers"].append(offer)
    _save_db(db)


def delete_offer(offer_id: str) -> None:
    db = _load_db()
    db["offers"] = [o for o in (db.get("offers") or []) if o["id"] != offer_id]
    _save_db(db)


def get_vouchers(app_key: Optional[str] = None, type_: Optional[Literal["free", "vip"]] = None) -> list[VoucherItem]:
    db = _load_db()
    all_v = db.get("vouchers") or []
    if app_key:
        all_v = [v for v in all_v if v["appKey"] == app_key]
    if type_:
        all_v = [v for v in all_v if v["type"] == type_]
    return all_v


def add_voucher(voucher: VoucherItem) -> None:
    db = _load_db()
    if not db.get("vouchers"):
        db["vouchers"] = []
    db["vouchers"].append(voucher)
    _save_db(db)


def delete_voucher(voucher_id: str) -> None:
    db = _load_db()
    db["vouchers"] = [v for v in (db.get("vouchers") or []) if v["id"] != voucher_id]
    _save_db(db)
