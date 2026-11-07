            print("Telegram baglanti hatasi, tekrar deneniyor")
        time.sleep(3)
    return False


def main():
    durum = {}
    if os.path.exists(DURUM):
        try:
            durum = json.load(open(DURUM))
        except Exception:
            durum = {}
    for t in json.load(open("takip.json", encoding="utf-8")):
        ad = t["ad"]
        try:
            r = requests.get(t["url"], headers=HEADERS, timeout=30)
            r.raise_for_status()
            fiyat = fiyat_bul(r.text, t.get("css_secici"))
        except Exception as e:
            print("[" + ad + "] hata:", e)
            continue
        if fiyat is None:
            print("[" + ad + "] fiyat okunamadi")
            continue
        eski = durum.get(ad)
        print("[" + ad + "] su an:", fiyat, "| onceki:", eski)
        if eski is None:
            mesaj = "👀 Takibe alindi: " + ad + "\nFiyat: " + str(fiyat) + "\n" + t["url"]
        elif fiyat < eski:
            mesaj = "🔽 FIYAT DUSTU: " + ad + "\n" + str(eski) + " -> " + str(fiyat) + "\n" + t["url"]
        elif fiyat > eski:
            mesaj = "🔼 FIYAT ARTTI: " + ad + "\n" + str(eski) + " -> " + str(fiyat) + "\n" + t["url"]
        else:
            mesaj = None
        if mesaj is None:
            continue
        if telegram(mesaj):
            durum[ad] = fiyat
    json.dump(durum, open(DURUM, "w"))

