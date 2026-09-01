import asyncio, json, os
from datetime import datetime, timezone
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "github" / "data"
STATE_FILE = DATA / "sync_state.json"
RAW_FILE = DATA / "raw_posts.json"

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = os.environ["TELEGRAM_SESSION"]
CHANNEL = os.getenv("CHANNEL_USERNAME", "moshakhsatmotor")


def load_json(path, default):
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default


async def main():
    state = load_json(STATE_FILE, {"last_message_id": 0})
    last_id = int(state.get("last_message_id", 0))
    raw = load_json(RAW_FILE, {"version": 1, "items": []})
    existing = {int(x.get("telegram_id", 0)): x for x in raw.get("items", []) if x.get("telegram_id") is not None}

    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.start()
    async with client:
        entity = await client.get_entity(CHANNEL)
        fresh = []
        async for m in client.iter_messages(entity, min_id=last_id, reverse=True):
            if not m.message and not m.media:
                continue
            item = {
                "telegram_id": int(m.id),
                "date": m.date.astimezone(timezone.utc).isoformat() if m.date else None,
                "text": m.message or "",
                "media": type(m.media).__name__ if m.media else None,
                "sync_date": datetime.now(timezone.utc).isoformat(),
            }
            existing[item["telegram_id"]] = item
            fresh.append(item)

    max_id = max([last_id] + [int(x["telegram_id"]) for x in fresh])
    items = sorted(existing.values(), key=lambda x: int(x.get("telegram_id", 0)))
    RAW_FILE.write_text(json.dumps({"version": 1, "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    STATE_FILE.write_text(json.dumps({"last_message_id": max_id}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Telegram sync complete: {len(fresh)} new posts; last_message_id={max_id}")


if __name__ == "__main__":
    asyncio.run(main())
