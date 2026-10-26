#!/usr/bin/env python3
"""
Inspect Tizen Smart TV Web App via Chrome DevTools Protocol (CDP).
Works with Chromium 56 (Tizen 4.0+).
"""
import sys
import json
import asyncio
import urllib.request

try:
    import websockets
except ImportError:
    print("Error: 'websockets' package required. Run: pip install websockets")
    sys.exit(1)


async def inspect(port: int = 40922, host: str = "127.0.0.1"):
    url = f"http://{host}:{port}/json"
    try:
        with urllib.request.urlopen(url, timeout=3) as res:
            targets = json.loads(res.read().decode())
    except Exception as e:
        print(f"Failed to connect to CDP endpoint {url}: {e}")
        return

    if not targets:
        print("No active debug targets found.")
        return

    ws_url = targets[0].get("webSocketDebuggerUrl")
    print(f"Connecting to {ws_url} ...")

    async with websockets.connect(ws_url) as ws:
        # Evaluate current state
        expr = """
        ({
            url: window.location.href,
            hash: window.location.hash,
            storageKeys: Object.keys(localStorage),
            lang: (function(){
                try {
                    var p = JSON.parse(localStorage.getItem("profile") || "{}");
                    return p.settings ? p.settings.interfaceLanguage : "not_set";
                } catch(e) { return "err"; }
            })(),
            bodyText: document.body.innerText.slice(0, 300),
            posters: document.querySelectorAll(".poster-kFYpD, .item-_uIl6, img").length
        })
        """
        await ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": expr, "returnByValue": True}
        }))
        res = await ws.recv()
        data = json.loads(res)
        val = data.get("result", {}).get("result", {}).get("value", {})
        print("--- TV App Runtime State ---")
        print(f"URL: {val.get('url')}")
        print(f"Route Hash: {val.get('hash')}")
        print(f"Interface Language: {val.get('lang')}")
        print(f"Posters/Images rendered: {val.get('posters')}")
        print(f"LocalStorage Keys: {val.get('storageKeys')}")
        print(f"Body Preview:\n{val.get('bodyText')}")


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 43965
    asyncio.run(inspect(port=p))
