#!/usr/bin/env python3
"""
opencode Free Models Watcher
-----------------------------
يجيب قائمة نماذج opencode.ai/zen، يستخرج منها المجانية،
و يقارنها بآخر حالة محفوظة في الريبو. لو ظهر نموذج مجاني جديد (أو اتمسح)
يبعتلك تنبيه على تليجرام.

يشتغل محليًا (python watch.py) أو على GitHub Actions.

الحالة: known_free_models.json في نفس المجلد (يُحدَّث ويُرجع للريبو تلقائيًا)
السجل:  watcher.log — ملخص مقروء فقط (النسخة الكاملة في Actions logs)

الإعدادات تُقرأ من متغيرات البيئة:
  TELEGRAM_TOKEN   — توكن البوت (GitHub Secret أو متغير محلي)
  TELEGRAM_CHAT_ID — chat id بتاعك (GitHub Secret أو متغير محلي)
لو مش متعينين، الرسالة تتطبع على stdout بس من غير إرسال.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

MODELS_URL = "https://opencode.ai/zen/v1/models"

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "known_free_models.json"
LOG_FILE = BASE_DIR / "watcher.log"

TIMEOUT = 30

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def log(msg: str, echo: bool = False) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    if echo:
        print(line)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def fetch_models() -> list[str]:
    req = urllib.request.Request(
        MODELS_URL, headers={"User-Agent": "free-models-watcher/1.0"}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return [m["id"] for m in data.get("data", [])]


def extract_free(model_ids: list[str]) -> list[str]:
    return sorted(m for m in model_ids if "free" in m.lower())


def load_known() -> set[str]:
    if not STATE_FILE.exists():
        return set()
    try:
        return set(json.loads(STATE_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return set()


def save_known(models: list[str]) -> None:
    STATE_FILE.write_text(
        json.dumps(models, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def notify(text: str) -> bool:
    """يبعت رسالة تليجرام — يرجّع True لو نجحت (أو لو مفيش إعدادات)."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        log("TELEGRAM_TOKEN/CHAT_ID مش متعينين — الرسالة اتطبعت على stdout بس")
        print(text)
        return True
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps(
        {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}
    ).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            ok = json.loads(resp.read().decode()).get("ok", False)
        if ok:
            log("تم إرسال تنبيه تليجرام")
        else:
            log("فشل إرسال تنبيه تليجرام (ok=false)")
        return ok
    except Exception as e:  # noqa: BLE001
        log(f"فشل إرسال تنبيه تليجرام: {e}")
        return False


def main() -> int:
    log("--- بدء الفحص ---")
    try:
        all_models = fetch_models()
    except Exception as e:  # noqa: BLE001
        log(f"فشل جلب قائمة النماذج: {e}", echo=True)
        return 1

    current_free = extract_free(all_models)
    known = load_known()

    added = sorted(set(current_free) - known)
    removed = sorted(known - set(current_free))

    log(f"إجمالي النماذج: {len(all_models)} | المجاني: {len(current_free)} | معروف سابقًا: {len(known)}")

    if not known:
        log("أول تشغيل — حفظ القائمة الحالية كأساس بدون إرسال تنبيه")
        save_known(current_free)
        return 0

    lines = []
    if added:
        lines.append(
            "🆕 نماذج مجانية جديدة ظهرت في opencode:\n"
            + "\n".join(f"• {m}" for m in added)
        )
    if removed:
        lines.append(
            "❌ نماذج مجانية اتمسحت:\n" + "\n".join(f"• {m}" for m in removed)
        )

    if lines:
        notify("\n\n".join(lines))
    else:
        log("مفيش تغييرات")

    save_known(current_free)
    return 0


if __name__ == "__main__":
    sys.exit(main())
