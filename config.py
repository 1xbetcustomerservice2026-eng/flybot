import os
from pathlib import Path

_BASE_DIR = Path(__file__).parent.parent

BOT_TOKEN: str = os.environ.get("8869833081:AAHS9V7cGFwjjQE5ISBEhk9eGRmf_KfOfVo", "")
ADMIN_ID: int = 8796417770

DEFAULT_CHANNEL_INVITE: str = "https://t.me/+mNXgNZ86X9RiNjg0"
DEFAULT_VIP_CHANNEL: str = "https://t.me/+ZopATTV90psyODU0"
DEFAULT_SUPPORT_USERNAME: str = "@TAMER_VIP"
DEFAULT_CHANNEL_ID: str = ""
DEFAULT_GUARANTEE_LINK: str = "https://t.me/+ZopATTV90psyODU0"

FLY_IMAGE: Path = _BASE_DIR / "data" / "fly.jpg"
APPLE_IMAGE: Path = _BASE_DIR / "data" / "apple.jpg"
PLANE_IMAGE: Path = _BASE_DIR / "data" / "plane.jpg"

APPS: dict[str, dict] = {
    "coldbet": {"name": "COLDBET", "emoji": "🔵", "promo": "FLY777"},
    "1xbet":   {"name": "1XBET",   "emoji": "🔵", "promo": "FLY777X"},
    "melbet":  {"name": "MELBET",  "emoji": "🟡", "promo": "FLY145"},
    "goobet":  {"name": "GOOBET",  "emoji": "🟣", "promo": "FLY777"},
}
