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
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>VeriStay — Safety Score</title>
  <style>
    body {
      font-family: system-ui, sans-serif;
      background-color: #f9fafb;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }
    h1 { color: #222; margin-bottom: 20px; }
    input {
      width: 350px;
      padding: 10px;
      border: 1px solid #ccc;
      border-radius: 8px;
      margin-bottom: 15px;
    }
    button {
      background-color: #e63946;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 10px 20px;
      cursor: pointer;
      font-size: 15px;
    }
    button:hover { background-color: #d62828; }
    #result {
      margin-top: 20px;
      max-width: 400px;
      padding: 15px;
      border-radius: 10px;
    }
  </style>
</head>
<body>
  <h1>🔍 VeriStay — Safety Score</h1>
  <input id="url" type="text" placeholder="Paste property link...">
  <button onclick="buy()">Check Safety (€3)</button>
  <div id="result"></div>

  <script>
    async function buy() {
      const url = document.getElementById('url').value.trim();
      if (!url) return alert('Please enter a valid link.');

      const btn = document.querySelector('button');
      btn.disabled = true;
      btn.textContent = 'Connecting to Stripe...';

      try {
        const res = await fetch('/buy', { method: 'POST' });
        const data = await res.json();
        window.location.href = data.url;
      } catch (err) {
        alert('Error connecting to Stripe.');
      } finally {
        btn.disabled = false;
        btn.textContent = 'Check Safety (€3)';
      }
    }
         </script>
  </body>
</html>
"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
