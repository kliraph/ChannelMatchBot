from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from typing import List, Dict, Any

import json

from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

async def fetch_posts(
    address: str,
    api_id: int = ***REMOVED***,
    api_hash: str = ***REMOVED***,
    session_name: str = "posts_fetch_session",
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve up to `limit` most recent posts from a single Telegram channel.
    Returns a list of dicts with keys: date, text, views, link.
    """
    async with TelegramClient(session_name, api_id, api_hash) as client:
        try:
            entity = await client.get_entity(address)
            history = await client(GetHistoryRequest(
                peer=entity,
                limit=limit,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            posts: List[Dict[str, Any]] = []
            for msg in history.messages:
                if msg.message:
                    posts.append({
                        "date": msg.date.isoformat(),
                        "text": msg.message,
                        "views": msg.views,
                        "link": f"https://t.me/{address.lstrip('@')}/{msg.id}"
                    })
            with open("posts.json", "w", encoding="utf-8") as f:
                json.dump(posts, f, ensure_ascii=False)
            return posts

        except Exception as e:
            # Return a single error entry if fetch fails
            return [{
                "date": None,
                "text": f"Error fetching posts: {e}",
                "views": None,
                "link": None
            }]
        

# from telethon import functions

# res = await client(functions.channels.GetSponsoredMessagesRequest(
#     channel='@channelusername',
#     limit=5                   # or set how many ads you'd like returned
# ))
# print(res.messages)  # contains only sponsored messages

# for ad in res.messages:
#     print(ad.title, ad.message, ad.url)