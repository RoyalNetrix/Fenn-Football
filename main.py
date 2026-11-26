"""Fenn football scores. Stdlib only.
Network: site.api.espn.com public scoreboard JSON (unofficial, no key)."""
import json, os, sys, threading, urllib.request
from datetime import datetime

LEAGUES = [("PL", "eng.1"), ("La Liga", "esp.1"), ("Serie A", "ita.1"),
           ("Bundesliga", "ger.1"), ("Ligue 1", "fra.1"), ("UCL", "uefa.champions")]
DATA = os.environ.get("FENN_DATA_DIR") or os.environ.get("NOOK_DATA_DIR") or "."   # NOOK_DATA_DIR is the older name
CFG_PATH = os.path.join(DATA, "config.json")
out_lock, state_lock, trigger = threading.Lock(), threading.Lock(), threading.Event()
cfg = {"league": 0, "team": ""}
matches, err, tile_w = [], "", 104


def send(msg):
    with out_lock:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()


def load_cfg():
    try:
        with open(CFG_PATH, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass


def save_cfg():
    try:
        os.makedirs(DATA, exist_ok=True)
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except OSError as e:
        print("save failed:", e, file=sys.stderr)


def txt(text, **kw):
    return {"type": "text", "text": text, **kw}


def friendly(e):
    s = str(e)
    if any(k in s for k in ("11001", "getaddrinfo", "Name or service", "unreachable", "10051", "10065")):
        return "No internet, retrying"
    if "timed out" in s:
        return "Timed out, retrying"
    return s[:40]


def fetch():
    global matches, err
    try:
        code = LEAGUES[cfg["league"]][1]
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
        req = urllib.request.Request(url, headers={"User-Agent": "fenn-football-plugin"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        ms = []
        for ev in data.get("events", []):
            comp = ev["competitions"][0]
            side = {c["homeAway"]: c for c in comp["competitors"]}
            st = ev["status"]["type"]
            state = st.get("state", "pre")
            if state == "pre":
                dt = datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).astimezone()
                detail = dt.strftime("%a %H:%M")
            else:
                detail = st.get("shortDetail", "")
            name = lambda s: side[s]["team"].get("shortDisplayName") or side[s]["team"].get("displayName", "?")
            abbr = lambda s: side[s]["team"].get("abbreviation") or name(s)[:3].upper()
            ms.append({"id": str(ev.get("id", len(ms))), "home": name("home"), "away": name("away"),
                       "ha": abbr("home"), "aa": abbr("away"),
                       "hs": side["home"].get("score", "0"), "as": side["away"].get("score", "0"),
                       "state": state, "detail": detail})
        with state_lock:
            matches, err = ms, ""
    except Exception as e:
        with state_lock:
            err = friendly(e)
        print("fetch failed:", e, file=sys.stderr)


def pick(ms):
    t = cfg["team"].strip().lower()
    if t:
        for m in ms:
            if t in (m["home"] + " " + m["away"]).lower():
                return m
    for m in ms:
        if m["state"] == "in":
            return m
    return ms[0] if ms else None


def label(m):
    return m["detail"] if m["state"] == "pre" else f'{m["hs"]} - {m["as"]}  {m["detail"]}'


def render():
    with state_lock:
        ms, e = list(matches), err
    m = pick(ms)
    live = any(x["state"] == "in" for x in ms)
    if m and tile_w < 70:
        tile = {"type": "column", "align": "center", "justify": "center", "gap": 0, "children": [
            {"type": "icon", "icon": "soccer-ball", "size": 20, "color": "red" if m["state"] == "in" else "accent"},
            txt("v" if m["state"] == "pre" else f'{m["hs"]}-{m["as"]}', size="small", bold=True)]}
    elif m:
        tile = {"type": "row", "align": "center", "gap": 10, "children": [
            {"type": "icon", "icon": "soccer-ball", "size": 26, "color": "red" if m["state"] == "in" else "accent"},
            {"type": "column", "gap": 0, "children": [
                txt(f'{m["ha"]} v {m["aa"]}', size="small", color="dim"),
                txt(label(m), size="title")]}]}
    else:
        tile = {"type": "row", "align": "center", "gap": 8, "children": [
            {"type": "icon", "icon": "soccer-ball", "size": 24, "color": "dim"},
            txt(e or "No matches today", size="small", color="dim", wrap=True)]}
    send({"type": "tile", "view": tile})
    send({"type": "badge", "badge": {"kind": "pulse"} if live else None})

    items = [{"id": x["id"], "title": f'{x["home"]}  {"v" if x["state"] == "pre" else x["hs"] + " - " + x["as"]}  {x["away"]}',
              "trailing": x["detail"], "icon": "soccer-ball", "selected": x["state"] == "in"} for x in ms]
    body = [{"type": "list", "id": "matches", "items": items}] if items else [
        txt(e or "No matches today in this league.", color="dim", wrap=True)]
    page = {"type": "column", "gap": 8, "scroll": True, "children": [
        {"type": "chips", "id": "league", "options": [n for n, _ in LEAGUES], "selected": cfg["league"]},
        {"type": "row", "align": "center", "gap": 8, "children": [
            {"type": "input", "id": "team", "value": cfg["team"], "hint": "Favourite team (optional)", "width": 220},
            {"type": "spacer"},
            {"type": "button", "id": "refresh", "icon": "arrow-clockwise", "tooltip": "Refresh"}]},
        *body]}
    send({"type": "page", "view": page})


def refresher():
    fails = 0
    while True:
        fetch()
        render()
        with state_lock:
            live = any(x["state"] == "in" for x in matches)
            bad = bool(err)
        fails = fails + 1 if bad else 0
        # on failure retry soon (1, 2, 4, then every 5 min); offline retries cost almost no data
        trigger.wait(min(60 * 2 ** (fails - 1), 300) if bad else (60 if live else 300))
        trigger.clear()


def main():
    global tile_w
    try:
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass
    load_cfg()
    render()
    threading.Thread(target=refresher, daemon=True).start()
    for line in sys.stdin:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        t = msg.get("type")
        if t == "event":
            i, v = msg.get("id"), msg.get("value")
            if i == "league" and isinstance(v, dict):
                cfg["league"] = int(v.get("index", 0))
                save_cfg()
                trigger.set()
            elif i == "team" and msg.get("kind") == "submit":
                cfg["team"] = str(v or "").strip()
                save_cfg()
                render()
            elif i == "refresh":
                trigger.set()
        elif t == "layout" and msg.get("target") == "tile":
            tile_w = msg.get("width", tile_w)
            render()
        elif t == "shutdown":
            save_cfg()
            return


if __name__ == "__main__":
    main()
