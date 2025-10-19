import re

AREA_MEDIANS = {"Dublin 15": 800.0, "Dublin 7": 900.0}

IBAN_IE = re.compile(r"IE\d{2}[A-Z0-9]{4}\d{14}")
ANY_IBAN = re.compile(r"[A-Z]{2}\d{2}[A-Z0-9]{4}\d{10,}")
EIRCODE  = re.compile(r"[A-Z]\d{2}\s?[A-Z0-9]{4}", re.I)
EMAIL    = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
IR_PHONE = re.compile(r"(\+353|0)\s?\d{1,2}\s?\d{6,8}")
WHATSAPP = re.compile(r"whats\s*app|whatsapp", re.I)

URGENCY_KEYS = ["pay now","reserve immediately","no viewing","send deposit","western union","moneygram"]

def compute_score(text: str, area: str=None, price: float=None, flags: dict=None):
    t = (text or "")
    tl = t.lower()
    flags = flags or {}
    score, reasons = 100, []

    if flags.get("deposit_before_viewing"): score -= 25; reasons.append("Deposit requested before viewing")
    if flags.get("no_viewing_offered") or "no viewing" in tl: score -= 25; reasons.append("No viewing offered")

    only_wa = WHATSAPP.search(tl) and not EMAIL.search(t) and not IR_PHONE.search(t)
    if only_wa: score -= 25; reasons.append("Only WhatsApp contact")

    any_iban = ANY_IBAN.search(t)
    if any_iban and (not IBAN_IE.search(t)): score -= 25; reasons.append("Non-Irish IBAN/payment")

    if area and price:
        median = AREA_MEDIANS.get(area)
        if median and price < 0.7*median: score -= 15; reasons.append("Price far below area median")

    if flags.get("stock_or_blurry_photos"): score -= 10; reasons.append("Stock/blurry photos")
    if not EIRCODE.search(t) and ("street" not in tl and "road" not in tl): score -= 10; reasons.append("No exact address/Eircode")
    if any(k in tl for k in URGENCY_KEYS): score -= 10; reasons.append("Urgency/pressure language")
    if flags.get("unclear_bills"): score -= 10; reasons.append("Bills/terms unclear")

    if EMAIL.search(t) and not re.search(r"@(gmail|yahoo|outlook)\.", tl): score += 10; reasons.append("Work/agency email present")
    if IR_PHONE.search(t): score += 5; reasons.append("Irish phone present")
    if EIRCODE.search(t): score += 10; reasons.append("Eircode / full address present")
    if flags.get("live_viewing_available"): score += 5; reasons.append("Live viewing offered")
    if flags.get("lease_before_payment"): score += 5; reasons.append("Lease shown before payment")

    score = max(0, min(100, score))
    band = "Green" if score >= 80 else ("Amber" if score >= 50 else "Red")
    return {"score": score, "band": band, "reasons": reasons}
