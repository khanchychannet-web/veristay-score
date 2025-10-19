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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
