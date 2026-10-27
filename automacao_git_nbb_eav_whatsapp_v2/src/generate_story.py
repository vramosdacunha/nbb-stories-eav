import os
import datetime
import requests
from bs4 import BeautifulSoup
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
DURATION = 5.0
TOTAL_FRAMES = int(FPS * DURATION)

FONT_BOLD = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
FONT_NARROW_BOLD = '/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf'
FONT_REG = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
FONT_MONO = '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf'

TEAM_LOGOS = {
    "BAURU": "assets/teams/bauru.png",
    "BRASÍLIA": "assets/teams/brasilia.png",
    "CAIXA BRASÍLIA": "assets/teams/brasilia.png",
    "CAXIAS": "assets/teams/caxias.png",
    "CORINTHIANS": "assets/teams/corinthians.png",
    "CRUZEIRO": "assets/teams/cruzeiro.png",
    "UNIÃO CORINTHIANS": "assets/teams/uniao_corinthians.png",
    "U. CORINTHIANS": "assets/teams/uniao_corinthians.png",
    "FLAMENGO": "assets/teams/flamengo.png",
    "PAULISTANO": "assets/teams/paulistano.png",
    "FORTALEZA": "assets/teams/cearense.png",
    "CEARENSE": "assets/teams/cearense.png",
    "BOTAFOGO": "assets/teams/botafogo.png",
}

def load_official_crest(filepath):
    box_sz = 92
    canvas = Image.new('RGBA', (box_sz, box_sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([2, 2, box_sz-3, box_sz-3], radius=18, fill=(255, 255, 255, 18), outline=(255, 255, 255, 45), width=1)
    im = Image.open(filepath).convert('RGBA')
    max_dim = 80
    scale = min(max_dim / im.width, max_dim / im.height)
    nw, nh = int(im.width * scale), int(im.height * scale)
    im_resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    ox = (box_sz - nw) // 2
    oy = (box_sz - nh) // 2
    canvas.paste(im_resized, (ox, oy), im_resized)
    return canvas

def create_team_crest(abbr, primary_rgb=(224, 90, 31), secondary_rgb=(255, 255, 255)):
    sz = 92
    img = Image.new('RGBA', (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f_shield = ImageFont.truetype(FONT_BOLD, 24)
    d.ellipse([2, 2, sz-3, sz-3], fill=(primary_rgb[0], primary_rgb[1], primary_rgb[2], 255), outline=(secondary_rgb[0], secondary_rgb[1], secondary_rgb[2], 255), width=4)
    tw = d.textlength(abbr[:3].upper(), font=f_shield)
    d.text(((sz - tw) / 2, sz * 0.35), abbr[:3].upper(), font=f_shield, fill=(255, 255, 255, 255))
    return img

def get_crest_for_team(team_name):
    t_up = team_name.upper()
    for key, path in TEAM_LOGOS.items():
        if key in t_up and os.path.exists(path):
            return load_official_crest(path)
    return create_team_crest(t_up[:3])

def fetch_lnb_matches_today():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
    today_str = today.strftime("%d/%m/%Y")
    headers = {"User-Agent": "Mozilla/5.0"}
    matches = []
    try:
        r = requests.get("https://lnb.com.br/nbb/tabela-de-jogos/", headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Fallback/parser da tabela oficial
            for row in soup.find_all("tr"):
                cols = [c.get_text(" ", strip=True) for c in row.find_all("td")]
                if len(cols) >= 6 and today_str[:5] in cols[0]:
                    matches.append({
                        "time": cols[1] if ":" in cols[1] else "19:30",
                        "arena": cols[5] if len(cols) > 5 else "Ginásio Oficial NBB",
                        "team1": cols[2].upper(),
                        "team2": cols[4].upper(),
                        "channel": f"AO VIVO • {cols[6]}" if len(cols) > 6 and cols[6] else "AO VIVO • YouTube NBB CAIXA",
                        "accent": (224, 90, 31) if len(matches) % 2 == 0 else (0, 168, 89)
                    })
    except Exception as e:
        print("Erro ao consultar LNB:", e)

    if not matches:
        # Fallback caso rode em dia de teste ou estrutura mude
        matches = [
            {
                "time": "19:00",
                "arena": "Arena UniBH • Belo Horizonte, MG",
                "team1": "MINAS STORM",
                "team2": "PATO BASQUETE",
                "channel": "AO VIVO • YouTube NBB CAIXA",
                "accent": (224, 90, 31)
            },
            {
                "time": "19:30",
                "arena": "Ginásio de Itatiaiuçu • MG",
                "team1": "CRUZEIRO",
                "team2": "CAIXA BRASÍLIA",
                "channel": "AO VIVO • YouTube NBB CAIXA",
                "accent": (0, 168, 89)
            },
            {
                "time": "20:30",
                "arena": "Ginásio Henrique Villaboim • SP",
                "team1": "PINHEIROS",
                "team2": "U. CORINTHIANS",
                "channel": "AO VIVO • ESPN 2 / Disney+",
                "accent": (224, 90, 31)
            }
        ]
    return matches[:4]

def ease_out_cubic(t):
    t = np.clip(t, 0.0, 1.0)
    return 1.0 - (1.0 - t)**3

def build_video(output_path="output/story_hoje.mp4"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    matches = fetch_lnb_matches_today()
    for m in matches:
        m["t1_crest"] = get_crest_for_team(m["team1"])
        m["t2_crest"] = get_crest_for_team(m["team2"])

    f_badge = ImageFont.truetype(FONT_BOLD, 22)
    f_title = ImageFont.truetype(FONT_BOLD, 68)
    f_subtitle = ImageFont.truetype(FONT_REG, 25)
    f_meta = ImageFont.truetype(FONT_REG, 22)
    f_team = ImageFont.truetype(FONT_NARROW_BOLD, 38)
    f_vs = ImageFont.truetype(FONT_BOLD, 22)
    f_channel = ImageFont.truetype(FONT_BOLD, 23)
    f_footer = ImageFont.truetype(FONT_REG, 23)
    f_footer_bold = ImageFont.truetype(FONT_BOLD, 24)
    f_tc = ImageFont.truetype(FONT_MONO, 20)

    eav_raw = Image.open('assets/logos/eav_logo.png').convert('RGBA')
    eav_w = 280
    eav_h = int(eav_raw.height * (eav_w / eav_raw.width))
    eav_img = eav_raw.resize((eav_w, eav_h), Image.Resampling.LANCZOS)
    eav_arr = np.array(eav_img)
    dark_pixels = (eav_arr[:, :, 0] < 100) & (eav_arr[:, :, 1] < 60) & (eav_arr[:, :, 3] > 20)
    eav_arr[dark_pixels, :3] = [240, 240, 245]
    eav_logo = Image.fromarray(eav_arr)

    nbb_raw = Image.open('assets/logos/nbb_logo.png').convert('RGBA')
    nbb_w = 180
    nbb_h = int(nbb_raw.height * (nbb_w / nbb_raw.width))
    nbb_logo = nbb_raw.resize((nbb_w, nbb_h), Image.Resampling.LANCZOS)

    yy, xx = np.mgrid[0:H, 0:W]
    dist_tr = np.sqrt((xx - (W - 150))**2 + (yy - 200)**2)
    dist_bl = np.sqrt((xx - 150)**2 + (yy - (H - 250))**2)
    glow_orange = np.clip(1.0 - dist_tr / 900.0, 0, 1)**2
    glow_green = np.clip(1.0 - dist_bl / 950.0, 0, 1)**2

    bg_np = np.zeros((H, W, 4), dtype=np.uint8)
    bg_np[:, :, 0] = np.clip(10 + glow_orange * 55 + glow_green * 5, 0, 255).astype(np.uint8)
    bg_np[:, :, 1] = np.clip(10 + glow_orange * 20 + glow_green * 38, 0, 255).astype(np.uint8)
    bg_np[:, :, 2] = np.clip(14 + glow_orange * 8 + glow_green * 18, 0, 255).astype(np.uint8)
    bg_np[:, :, 3] = 255
    grid_mask = ((xx % 60 == 0) | (yy % 60 == 0))
    bg_np[grid_mask, :3] = np.clip(bg_np[grid_mask, :3] + 8, 0, 255)
    bg_base = Image.fromarray(bg_np)

    def render_card(match):
        cw, ch = 960, 295
        card = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
        d = ImageDraw.Draw(card)
        d.rounded_rectangle([0, 0, cw-1, ch-1], radius=28, fill=(24, 25, 32, 240), outline=(255, 255, 255, 35), width=2)
        acc = match["accent"]
        d.rounded_rectangle([0, 24, 10, ch-24], radius=5, fill=(acc[0], acc[1], acc[2], 255))
        d.text((40, 28), f"HORÁRIO: {match['time']} (BRT)", font=f_meta, fill=(224, 90, 31, 255))
        arena_w = d.textlength(match["arena"], font=f_meta)
        d.text((cw - 40 - arena_w, 28), match["arena"], font=f_meta, fill=(165, 165, 175, 255))
        d.line([(40, 70), (cw - 40, 70)], fill=(255, 255, 255, 22), width=1)
        c1 = match["t1_crest"]
        card.paste(c1, (40, 90), c1)
        d.text((146, 116), match["team1"], font=f_team, fill=(255, 255, 255, 255))
        vs_x = cw // 2
        d.rounded_rectangle([vs_x - 34, 112, vs_x + 34, 160], radius=12, fill=(acc[0], acc[1], acc[2], 45), outline=(acc[0], acc[1], acc[2], 180), width=2)
        vs_w = d.textlength("VS", font=f_vs)
        d.text((vs_x - vs_w / 2, 123), "VS", font=f_vs, fill=(255, 255, 255, 255))
        c2 = match["t2_crest"]
        card.paste(c2, (cw - 40 - 92, 90), c2)
        t2_w = d.textlength(match["team2"], font=f_team)
        d.text((cw - 40 - 92 - 14 - t2_w, 116), match["team2"], font=f_team, fill=(255, 255, 255, 255))
        d.rounded_rectangle([40, 212, cw - 40, 264], radius=12, fill=(14, 15, 20, 210))
        d.ellipse([62, 230, 78, 246], fill=(0, 215, 115, 255))
        d.text((95, 224), match["channel"], font=f_channel, fill=(0, 215, 115, 255))
        return card

    cards_rendered = [render_card(m) for m in matches]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_out = cv2.VideoWriter(output_path, fourcc, FPS, (W, H))
    today_label = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime("%d/%m/%Y")

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / FPS
        canvas = bg_base.copy()
        draw = ImageDraw.Draw(canvas)
        tc_frames = frame_idx % FPS
        tc_secs = int(t)
        tc_str = f"REC • TC 00:00:0{tc_secs}:{tc_frames:02d} • {today_label}"
        draw.text((60, 50), tc_str, font=f_tc, fill=(140, 140, 150, 180))
        draw.text((W - 60 - draw.textlength("SINAL OFICIAL EAV", font=f_tc), 50), "SINAL OFICIAL EAV", font=f_tc, fill=(224, 90, 31, 200))
        draw.line([(60, 82), (W - 60, 82)], fill=(255, 255, 255, 25), width=1)
        p_header = ease_out_cubic(t / 0.6)
        y_header_offset = int((1.0 - p_header) * -40)
        canvas.paste(nbb_logo, (60, 115 + y_header_offset), nbb_logo)
        canvas.paste(eav_logo, (W - 60 - eav_w, 120 + y_header_offset), eav_logo)

        p_title = ease_out_cubic((t - 0.15) / 0.6)
        if p_title > 0:
            y_title = int(265 + (1.0 - p_title) * 30)
            pulse = 0.5 + 0.5 * np.sin(t * 5.0)
            badge_bg = (224, 90, 31, int(35 + 30 * pulse))
            draw.rounded_rectangle([60, y_title, 495, y_title + 48], radius=24, fill=badge_bg, outline=(224, 90, 31, 220), width=2)
            dot_r = int(7 + 2 * pulse)
            draw.ellipse([85 - dot_r, y_title + 24 - dot_r, 85 + dot_r, y_title + 24 + dot_r], fill=(255, 95, 35, 255))
            draw.text((108, y_title + 12), f"RODADA NBB • {today_label}", font=f_badge, fill=(255, 255, 255, 255))
            draw.text((60, y_title + 70), "JOGOS DO", font=f_title, fill=(255, 255, 255, int(255 * p_title)))
            w_jogos = draw.textlength("JOGOS DO ", font=f_title)
            draw.text((60 + w_jogos, y_title + 70), "DIA", font=f_title, fill=(224, 90, 31, int(255 * p_title)))
            draw.text((60, y_title + 155), "TEMPORADA 26/27 • TRANSMISSÃO OFICIAL NBB CAIXA", font=f_subtitle, fill=(165, 165, 175, int(255 * p_title)))

        base_card_y = 480
        card_gap = 330
        for idx, card_img in enumerate(cards_rendered):
            start_t = 0.35 + idx * 0.22
            p_card = ease_out_cubic((t - start_t) / 0.65)
            if p_card > 0:
                cy = int(base_card_y + idx * card_gap + (1.0 - p_card) * 70)
                if p_card < 1.0:
                    c_copy = card_img.copy()
                    alpha = c_copy.split()[3].point(lambda p: int(p * p_card))
                    c_copy.putalpha(alpha)
                    canvas.paste(c_copy, (60, cy), c_copy)
                else:
                    canvas.paste(card_img, (60, cy), card_img)

        p_footer = ease_out_cubic((t - 1.0) / 0.6)
        if p_footer > 0:
            fy = 1540
            draw.line([(60, fy), (W - 60, fy)], fill=(255, 255, 255, int(40 * p_footer)), width=2)
            draw.rounded_rectangle([60, fy + 35, W - 60, fy + 145], radius=22, fill=(224, 90, 31, int(25 * p_footer)), outline=(224, 90, 31, int(140 * p_footer)), width=2)
            cta_text = "ACOMPANHE AO VIVO NOS CANAIS OFICIAIS"
            cta_w = draw.textlength(cta_text, font=f_footer_bold)
            draw.text(((W - cta_w) / 2, fy + 62), cta_text, font=f_footer_bold, fill=(255, 255, 255, int(255 * p_footer)))
            sub_cta = "Produção Técnica & Broadcast: EAV Produções • eavprod.com.br"
            sub_w = draw.textlength(sub_cta, font=f_footer)
            draw.text(((W - sub_w) / 2, fy + 100), sub_cta, font=f_footer, fill=(200, 200, 210, int(230 * p_footer)))
            bar_w = int((W - 120) * (t / DURATION))
            draw.rounded_rectangle([60, H - 65, W - 60, H - 55], radius=5, fill=(255, 255, 255, 30))
            draw.rounded_rectangle([60, H - 65, 60 + max(10, bar_w), H - 55], radius=5, fill=(224, 90, 31, 255))

        frame_rgb = np.array(canvas.convert('RGB'))
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        video_out.write(frame_bgr)

    video_out.release()
    print("Video renderizado com sucesso em:", output_path)

if __name__ == "__main__":
    build_video()
