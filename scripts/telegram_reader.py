import os
import json
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession


API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
CHANNEL_USERNAME = os.environ["CHANNEL_USERNAME"]
SESSION = os.environ["TELEGRAM_SESSION"]


RAW_FILE = "data/raw_posts.json"
STATE_FILE = "data/sync_state.json"


def load_json(path, default):

    if os.path.exists(path):

        try:

            with open(path, "r", encoding="utf-8") as f:

                return json.load(f)

        except Exception:

            return default

    return default



def save_json(path, data):

    with open(path, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )



async def main():

    print("Connecting to Telegram...")


    client = TelegramClient(
        StringSession(SESSION),
        API_ID,
        API_HASH
    )


    await client.connect()


    if not await client.is_user_authorized():

        raise Exception(
            "Telegram session is not authorized"
        )


    print("Telegram connected successfully")


    state = load_json(
        STATE_FILE,
        {
            "last_message_id": 0
        }
    )


    last_id = state.get(
        "last_message_id",
        0
    )


    posts = load_json(
        RAW_FILE,
        []
    )


    # اصلاح ساختار اشتباه فایل قبلی
    if not isinstance(posts, list):

        posts = []


    new_posts = []


    print(
        "Reading channel:",
        CHANNEL_USERNAME
    )


    async for message in client.iter_messages(
        CHANNEL_USERNAME,
        min_id=last_id
    ):


        if not message.text:

            continue


        new_posts.append(
            {
                "message_id": message.id,
                "date": str(message.date),
                "text": message.text,
                "media": bool(message.media)
            }
        )


    if new_posts:


        new_posts.reverse()


        posts.extend(new_posts)


        save_json(
            RAW_FILE,
            posts
        )


        last_message_id = max(
            item["message_id"]
            for item in new_posts
        )


        save_json(
            STATE_FILE,
            {
                "last_message_id": last_message_id
            }
        )


        print(
            "New posts saved:",
            len(new_posts)
        )


    else:

        print(
            "No new posts"
        )


    await client.disconnect()



if __name__ == "__main__":

    asyncio.run(main())
