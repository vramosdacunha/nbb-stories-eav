import os
import base64
import requests

PHONE = os.environ.get("WHATSAPP_PHONE", "5521967447902")
API_URL = os.environ.get("API_URL", "")
API_KEY = os.environ.get("API_KEY", "")
VIDEO_PATH = "output/story_hoje.mp4"

def send_video():
    if not os.path.exists(VIDEO_PATH):
        print("Nenhum jogo hoje ou video nao gerado.")
        return
    if not API_URL:
        print("Configure WHATSAPP_API_URL nos Secrets do repositorio GitHub.")
        return

    with open(VIDEO_PATH, "rb") as f:
        video_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "number": PHONE,
        "mediatype": "video",
        "mimetype": "video/mp4",
        "caption": "🏀🎬 *EAV Produções* — Seu Stories do NBB de hoje está pronto!",
        "media": video_b64,
        "fileName": "stories_nbb_hoje.mp4"
    }
    headers = {"apikey": API_KEY, "Content-Type": "application/json"}
    resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
    print("Status envio WhatsApp:", resp.status_code, resp.text)

if __name__ == "__main__":
    send_video()
