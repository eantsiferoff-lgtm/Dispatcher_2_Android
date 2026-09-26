import json
import os
import urllib.request
import urllib.parse

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


def telegram_request(method, params=None):
    params = params or {}
    data = urllib.parse.urlencode(params).encode()

    request = urllib.request.Request(
        f"{TELEGRAM_API}/{method}",
        data=data,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def get_updates(offset=None):
    params = {
        "timeout": 50,
    }

    if offset is not None:
        params["offset"] = offset

    return telegram_request("getUpdates", params)


if __name__ == "__main__":
    print("TELEGRAM_ADAPTER_OK")
