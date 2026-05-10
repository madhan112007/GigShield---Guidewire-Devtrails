import asyncio, sys, json
sys.path.insert(0, '.')
import httpx
from app.config import settings

async def check():
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    async with httpx.AsyncClient(timeout=8.0) as c:
        r = await c.post(
            url + "?key=" + settings.GEMINI_API_KEY,
            json={"contents": [{"parts": [{"text": "say hi"}]}]}
        )
        print("Status:", r.status_code)
        data = r.json()
        print("Keys:", list(data.keys()))
        print(json.dumps(data, indent=2)[:500])

asyncio.run(check())
