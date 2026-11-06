import json, os, re
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (kisisel fiyat takibi)"}
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
DURUM = "durum.json"


def sayi(metin):
    m = re.search(r"\d[\d.,]*", str(metin))
    if not m:
        return None
    s = m.group()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") > 1 or re.search(r"\.\d{3}$", s):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError: return None


def fiyat_bul(html, css_secici=None):
    soup = BeautifulSoup(html, "html.parser")
    if css_secici:
        f = [sayi(e.get_text()) for e in soup.select(css_secici)]
        f = [x for x in f if x]
        if f:
            return min(f)
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            veri = json.loads(tag.string or "")
        except Exception: continue
        bulunan = []

        def tara(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("lowPrice", "price"):
                        x = sayi(v)
                        if x:
                            bulunan.append(x)
                    else:
                        tara(v)
            elif isinstance(o, list):
                for i in o:
                    tara(i)

        tara(veri)
        if bulunan:
            return min(bulunan)
    adaylar = re.findall(r"(?:₺|TL|€|EUR)\s?(\d[\d.,]*)|(\d[\d.,]*)\s?(?:₺|TL|€|EUR)", soup.get_text(" "))
    f = [sayi(a or b) for a, b in adaylar]
    f = [x for x in f if x and x > 0]
    return min(f) if f else None


def telegram(mesaj):
    print(mesaj)
    if not (TOKEN and CHAT):
        return False
    for deneme in range(3):
        try:
            r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": mesaj}, timeout=40)
            print("Telegram yaniti:", r.status_code)
            if r.ok:
                return True
        except Exception as e: print("Telegram hatasi:", type(e).__name__)
    return False


def main():
    durum = json.load(open(DURUM)) if os.path.exists(DURUM) else {}
    for t in json.load(open("takip.json", encoding="utf-8")):
        try:
            r = requests.get(t["url"], headers=HEADERS, timeout=20)
            r.raise_for_status()
            fiyat = fiyat_bul(r.text, t.get("css_secici"))
        except Exception as e: print(f"[{t['ad']}] hata: {e}"); continue
        if fiyat is None:
            print(f"[{t['ad']}] fiyat okunamadi")
            continue
        print(f"[{t['ad']}] su an: {fiyat} | hedef: {t['hedef_fiyat']}")
        if fiyat <= t["hedef_fiyat"] and durum.get(t["ad"]) != fiyat:
            if telegram(f"🔔 {t['ad']}: {fiyat} (hedef {t['hedef_fiyat']})\n{t['url']}"):
                durum[t["ad"]] = fiyat
        elif fiyat > t["hedef_fiyat"]:
            durum.pop(t["ad"], None)
    json.dump(durum, open(DURUM, "w"))


if __name__ == "__main__":
    main()
