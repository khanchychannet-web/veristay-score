from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from compute import compute_score

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def extract_text(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0 VeriStayBot/0.1"}, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script","style","noscript"]): t.extract()
        return " ".join(soup.get_text(" ").split())
    except Exception as e:
        return f"ERROR_FETCH: {e}"

@app.post("/score")
def score():
    data = request.get_json(force=True) or {}
    url   = data.get("url")
    area  = data.get("area")
    price = data.get("price")
    flags = data.get("flags") or {}
    if not url: return jsonify({"error":"url required"}), 400

    text = extract_text(url)
    result = compute_score(text, area=area, price=price, flags=flags)
    result["url"] = url
    if text.startswith("ERROR_FETCH:"): result["reasons"].append("Could not fetch page content; manual checks advised.")
    return jsonify(result)

@app.get("/")
def root():
    return jsonify({"ok": True, "service": "VeriStay Score API"})
@app.get("/widget")
def widget():
    html = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VeriStay — Safety Score</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#F6F7FB; --text:#1F2937; --card:#FFFFFF; --muted:#6B7280;
    --cta:#E63946; --cta-hover:#D62828; --ring:#FCA5A5;
    --green:#E8F5E9; --green-border:#A5D6A7;
    --amber:#FFF8E1; --amber-border:#FFE082;
    --red:#FFEBEE; --red-border:#EF9A9A;
  }
  *{box-sizing:border-box}
  body{font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;padding:24px;background:var(--bg);color:var(--text)}
  .card{max-width:700px;margin:0 auto;background:var(--card);padding:28px;border-radius:16px;box-shadow:0 10px 30px rgba(17,24,39,.08)}
  h1{margin:0 0 8px;font-size:24px;letter-spacing:.2px}
  .muted{color:var(--muted);font-size:14px}
  .row{display:flex;gap:10px;margin:18px 0}
  input[type=url]{flex:1;padding:12px 14px;border:1px solid #E5E7EB;border-radius:10px;background:#FAFAFA}
  input[type=url]:focus{outline:none;border-color:var(--cta);box-shadow:0 0 0 4px var(--ring)}
  button{padding:12px 18px;border:none;border-radius:10px;background:var(--cta);color:#fff;font-weight:700;cursor:pointer;transition:transform .06s ease,box-shadow .2s ease,background .2s ease;box-shadow:0 6px 16px rgba(230,57,70,.28)}
  button:hover{background:var(--cta-hover);box-shadow:0 10px 22px rgba(214,40,40,.38)}
  button:active{transform:translateY(1px)}
  .result{margin-top:16px;padding:16px;border-radius:12px;border:1px solid #E5E7EB}
  .green{background:var(--green);border-color:var(--green-border)}
  .amber{background:var(--amber);border-color:var(--amber-border)}
  .red{background:var(--red);border-color:var(--red-border)}
  ul{margin:8px 0 0 18px}
  .row2{display:flex;gap:10px;margin-top:8px;align-items:center}
  .paylink{font-size:14px;text-decoration:none;padding:10px 12px;border-radius:10px;border:1px solid #E5E7EB;background:#fff;color:#1F2937}
  .paylink:hover{border-color:#cbd5e1}
</style>
</head>
<body>
  <div class="card">
    <h1>🔍 VeriStay — Safety Score</h1>
    <p class="muted">Paste a Daft/Facebook link. We’ll analyze risk signals and show a quick safety score.</p>
    <div class="row">
      <input id="url" type="url" placeholder="https://www.daft.ie/..." required>
      <button id="checkBtn">Check</button>
    </div>
    <div id="out"></div>
    <div class="row2">
      <a id="fullReport" class="paylink" href="#" target="_blank" rel="noopener">Get Full Report (€2)</a>
    </div>
    <p class="muted">Disclaimer: this is a risk indicator, not legal advice.</p>
  </div>
<script>
const API = location.origin + "/score";
const $url = document.getElementById('url');
const $btn = document.getElementById('checkBtn');
const $out = document.getElementById('out');
const $full = document.getElementById('fullReport');

// 👉 встав сюди свій лінк на оплату (Stripe або Gumroad)
const PAY_URL = "https://gumroad.com/l/veristay-full-report"; 

$full.href = PAY_URL;

async function check() {
  const link = $url.value.trim();
  if (!link) return;
  $btn.disabled = true; $btn.textContent = "Checking..."; $out.innerHTML = "";
  try{
    const res = await fetch(API, { method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify({ url: link }) });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    const band = (data.band||"Amber").toLowerCase();
    const cls = band==="green"?"green":(band==="red"?"red":"amber");
    const reasons = (data.reasons||[]).map(r=>`<li>${r}</li>`).join("");
    $out.innerHTML = `<div class="result ${cls}">
      <strong>Score:</strong> ${data.score}/100 — <strong>${data.band}</strong><br/>
      <strong>Reasons:</strong><ul>${reasons || "<li>No major risks detected.</li>"}</ul>
    </div>`;
  }catch(e){
    $out.innerHTML = `<div class="result red"><strong>Error:</strong> ${e.message}</div>`;
  }finally{
    $btn.disabled=false; $btn.textContent="Check";
  }
}
$btn.addEventListener('click', check);
$url.addEventListener('keydown', e=>{ if(e.key==='Enter') check(); });
</script>
</body>
</html>
"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
