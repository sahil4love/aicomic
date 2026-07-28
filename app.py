import streamlit as st
from streamlit_mic_recorder import speech_to_text
import urllib.parse
import json
import random
import time
import requests
import io
import math
import os
from PIL import Image, ImageDraw, ImageOps, ImageEnhance

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

# Page Configuration (Default collapsed sidebar)
st.set_page_config(
    page_title="ComicForge Studio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Persistence Helpers (Saves history to JSON disk file so comics survive page refreshes)
HISTORY_FILE = "comic_history.json"

def load_history_from_disk():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_history_to_disk(history_data):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2)
    except Exception:
        pass

# Custom Styling (ChatGPT Minimalist Dark Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* GPT Pitch Dark Theme */
    .stApp {
        background-color: #0d0d0d;
        color: #ececf1;
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu, footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        max-width: 1180px !important;
    }

    /* Sidebar Dark Styling */
    section[data-testid="stSidebar"] {
        background-color: #171717 !important;
        border-right: 1px solid #2f2f2f !important;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    /* Sidebar API Input Field */
    section[data-testid="stSidebar"] div[data-testid="stTextInput"] input {
        background-color: #212121 !important;
        border: 1px solid #383838 !important;
        border-radius: 8px !important;
        height: 38px !important;
        font-size: 0.82rem !important;
        color: #ececf1 !important;
    }

    /* Sidebar New Comic Button */
    .sidebar-new-btn > button {
        background-color: #212121 !important;
        color: #ececf1 !important;
        border: 1px solid #383838 !important;
        border-radius: 8px !important;
        height: 44px !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        margin-bottom: 16px !important;
    }
    
    .sidebar-new-btn > button:hover {
        background-color: #2a2a2a !important;
        border-color: #555555 !important;
        color: #ffffff !important;
    }

    /* Clean ChatGPT-style Sidebar History Item */
    .sidebar-history-btn > button {
        background-color: transparent !important;
        color: #c5c5d2 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 6px 8px !important;
        text-align: left !important;
        font-size: 0.84rem !important;
        font-weight: 400 !important;
        height: 40px !important;
        line-height: 1.3 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        width: 100% !important;
        box-shadow: none !important;
    }

    .sidebar-history-btn > button:hover {
        background-color: #212121 !important;
        color: #ffffff !important;
    }

    /* Centered Hero Heading */
    .chatgpt-hero-title {
        font-size: 2.2rem;
        font-weight: 600;
        color: #f3f3f3;
        text-align: center;
        margin-top: 80px;
        margin-bottom: 32px;
        letter-spacing: -0.5px;
    }

    /* Landing prompt input */
    div[data-testid="stTextInput"] input {
        background-color: #212121 !important;
        color: #ececf1 !important;
        border: 1px solid #383838 !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
        height: 48px !important;
        padding: 0 16px !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #10a37f !important;
        box-shadow: 0 0 0 1px #10a37f !important;
    }

    /* Voice Mic Button */
    iframe[title*="streamlit_mic_recorder"] {
        height: 48px !important;
    }

    /* Uniform Height Suggestion Buttons */
    .landing-sugg-container div[data-testid="stButton"] > button {
        background-color: #212121 !important;
        color: #c5c5d2 !important;
        border: 1px solid #383838 !important;
        border-radius: 12px !important;
        height: 56px !important;
        padding: 8px 14px !important;
        font-size: 0.86rem !important;
        font-weight: 500 !important;
        line-height: 1.25 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        transition: all 0.15s ease !important;
    }

    .landing-sugg-container div[data-testid="stButton"] > button:hover {
        background-color: #2a2a2a !important;
        border-color: #555555 !important;
        color: #ffffff !important;
    }

    /* Generate New Button (Primary Green Accent) */
    .primary-gen-btn > button {
        background-color: #10a37f !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: none !important;
        border-radius: 10px !important;
        height: 48px !important;
        padding: 0 28px !important;
        box-shadow: 0 4px 12px rgba(16, 163, 127, 0.3) !important;
    }

    .primary-gen-btn > button:hover {
        background-color: #1a7f64 !important;
    }

    /* Compact Header Bar above panel image */
    .gpt-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #171717;
        border: 1px solid #2f2f2f;
        border-radius: 8px;
        padding: 6px 10px;
        margin-bottom: 8px;
        height: 28px;
    }

    .gpt-panel-badge {
        font-size: 0.72rem;
        font-weight: 700;
        color: #10a37f;
        background-color: rgba(16, 163, 127, 0.12);
        padding: 2px 6px;
        border-radius: 4px;
        letter-spacing: 0.5px;
    }

    .gpt-panel-sfx {
        font-size: 0.75rem;
        font-weight: 800;
        color: #ef4444;
        background: rgba(239, 68, 68, 0.12);
        padding: 2px 6px;
        border-radius: 4px;
    }

    /* Standardized Equal Height & Width Dialogue Box */
    .gpt-dialogue-text {
        font-size: 0.8rem;
        color: #ececf1;
        background: #171717;
        border: 1px solid #2f2f2f;
        padding: 8px 10px;
        border-radius: 8px;
        margin-top: 8px;
        margin-bottom: 24px;
        border-left: 3px solid #10a37f;
        line-height: 1.35;
        height: 64px;
        min-height: 64px;
        max-height: 64px;
        display: flex;
        align-items: center;
        width: 100%;
        box-sizing: border-box;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

def generate_procedural_pencil_panel(prompt: str, idx: int, seed: int) -> Image.Image:
    """Generate Compact Custom Pencil Sketch Artwork"""
    random.seed(seed + idx * 777)
    width, height = 350, 350
    img = Image.new('RGB', (width, height), color=(245, 242, 235))
    draw = ImageDraw.Draw(img)
    
    for _ in range(2000):
        draw.point((random.randint(0, 349), random.randint(0, 349)), fill=(random.randint(180, 215),)*3)
        
    pencil = (35, 35, 35)
    light_pencil = (130, 130, 130)
    
    variant = idx % 5
    if variant == 0:
        for i in range(4):
            bx = 20 + i * 80
            bh = 100 + (seed * (i+1) * 17) % 150
            draw.rectangle([bx, 350-bh, bx+60, 350], outline=pencil, width=2)
            for wy in range(350-bh+15, 330, 18):
                draw.line([(bx+10, wy), (bx+50, wy)], fill=light_pencil, width=1)
            
    elif variant == 1:
        cx, cy = 175, 175
        for angle in range(0, 360, 15):
            rad = math.radians(angle)
            draw.line([(cx, cy), (cx + int(160*math.cos(rad)), cy + int(160*math.sin(rad)))], fill=light_pencil, width=1)
        draw.rectangle([80, 100, 270, 250], outline=pencil, width=3)
            
    elif variant == 2:
        draw.arc([70, 50, 280, 210], start=180, end=360, fill=pencil, width=4)
        draw.polygon([(40, 160), (100, 90), (175, 150), (250, 90), (310, 160)], outline=pencil, width=3)
        
    elif variant == 3:
        cx, cy = 175, 160
        draw.ellipse([cx-25, cy-70, cx+25, cy-20], outline=pencil, width=3)
        draw.line([(cx, cy-20), (cx, cy+60)], fill=pencil, width=4)
        draw.line([(cx, cy), (cx-60, cy-35)], fill=pencil, width=3)
        draw.line([(cx, cy), (cx+70, cy-45)], fill=pencil, width=3)
        draw.line([(cx, cy+60), (cx-50, cy+130)], fill=pencil, width=3)
        draw.line([(cx, cy+60), (cx+50, cy+130)], fill=pencil, width=3)
        
    else:
        draw.polygon([(70, 200), (175, 100), (280, 200), (175, 240)], outline=pencil, width=3)
        draw.ellipse([145, 140, 205, 175], outline=pencil, width=2)

    draw.rectangle([5, 5, width-5, height-5], outline=pencil, width=2)
    return img

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_panel_image(prompt: str, idx: int, seed: int) -> Image.Image:
    """Multi-Tiered Guaranteed Image Engine"""
    encoded = urllib.parse.quote(f"pencil sketch of {prompt}, graphite line art")
    url_poll = f"https://image.pollinations.ai/prompt/{encoded}?width=400&height=400&seed={seed}&nologo=true"
    try:
        r = requests.get(url_poll, timeout=2)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            return Image.open(io.BytesIO(r.content))
    except Exception:
        pass

    url_picsum = f"https://picsum.photos/seed/{seed + idx * 123}/400/400?grayscale"
    try:
        r = requests.get(url_picsum, timeout=1.8)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            base_img = Image.open(io.BytesIO(r.content))
            gray = ImageOps.grayscale(base_img)
            enhancer = ImageEnhance.Contrast(gray)
            sketch = enhancer.enhance(1.6).convert("RGB")
            draw = ImageDraw.Draw(sketch)
            draw.rectangle([4, 4, 396, 396], outline=(30, 30, 30), width=3)
            return sketch
    except Exception:
        pass

    return generate_procedural_pencil_panel(prompt, idx, seed)

def generate_20_panel_story(user_prompt: str, user_api_key: str = None):
    """Break input story into 20 continuous connected comic book panels (Supports User Gemini API Key)"""
    api_key = user_api_key.strip() if user_api_key and user_api_key.strip() else os.getenv("GEMINI_API_KEY")
    if GEMINI_AVAILABLE and api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt_instructions = (
                f"You are a master comic book writer. Take this story idea: '{user_prompt}'. "
                "Break it into exactly 20 continuous, connected, sequential comic book panels. "
                "Return ONLY a raw JSON array of 20 objects, each containing: "
                "'caption' (narrative text), 'dialogue' (character line), 'sfx' (sound effect), and 'prompt' (detailed pencil sketch visual scene description)."
            )
            response = model.generate_content(prompt_instructions)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            panels = json.loads(text)
            if isinstance(panels, list) and len(panels) == 20:
                return panels
        except Exception:
            pass

    topic = user_prompt.strip() if user_prompt.strip() else "Cyberpunk Detective Jax in Neo-Tokyo"
    sfx_list = ["THWIP!", "BEEP!", "KABOOM!", "ZAP!", "WHOOSH!", "SMASH!", "BAM!", "HUMM...", "ALARM!", "ROAR!"]
    
    story_beats = [
        f"The story opens as our hero prepares for an unprecedented mystery regarding {topic}.",
        "A sudden strange atmospheric disturbance draws immediate attention.",
        "Investigating the perimeter reveals glowing cryptic footprints on the ground.",
        "An ancient decrypted signal activates on the primary datapad device.",
        "Surrounding shadows begin to shift into menacing mechanical silhouettes.",
        "Our protagonist leaps behind cover as energy beams slice through the air.",
        "An unexpected ally emerges from the fog to render tactical assistance.",
        "Together they decipher the coordinates pointing to the central spire.",
        "Navigating through narrow ventilation shafts to bypass heavy security.",
        "Reaching the central control chamber where the core power cell glows bright.",
        "The primary adversary steps forward from the shadows to initiate combat.",
        "A tense verbal confrontation unfolds as secret motives are revealed.",
        "The antagonist activates the orbital pulse charge generator system.",
        "Our hero charges forward, unleashing a powerful energy counter-blast.",
        "Sparks fly violently as metal structures collapse all around the chamber.",
        "The ally hacks into the main terminal to override the detonation timer.",
        "With seconds remaining, the hyper-core is successfully stabilized.",
        "The villain escapes into an emergency escape pod into deep space.",
        "Standing victorious amidst the ruins as dawn breaks over the horizon.",
        "The journey concludes for now, but a new galaxy adventure awaits on the horizon."
    ]

    panels = []
    for idx in range(20):
        beat = story_beats[idx]
        panels.append({
            "caption": f"Panel {idx+1}",
            "dialogue": f"{beat}",
            "sfx": sfx_list[idx % len(sfx_list)],
            "prompt": f"pencil sketch of {topic}, scene {idx+1}: {beat}"
        })
    return panels

# Persistent Session State Initialization
if "comic_history" not in st.session_state:
    st.session_state.comic_history = load_history_from_disk()

if "panels" not in st.session_state:
    if st.session_state.comic_history:
        latest = st.session_state.comic_history[0]
        st.session_state.panels = latest.get("panels")
        st.session_state.seeds = latest.get("seeds")
        st.session_state.current_title = latest.get("title", "Comic Storyboard")
    else:
        st.session_state.panels = None

if "seeds" not in st.session_state:
    st.session_state.seeds = [random.randint(1000, 999999) for _ in range(20)]
if "generating_prompt" not in st.session_state:
    st.session_state.generating_prompt = None
if "current_title" not in st.session_state:
    st.session_state.current_title = "Comic Storyboard"

# SIDEBAR (With User Gemini API Key Input)
with st.sidebar:
    st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #ffffff; margin-bottom: 12px;">ComicForge Studio</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-new-btn">', unsafe_allow_html=True)
    if st.button("+ New Comic", key="sidebar_new_btn", use_container_width=True):
        st.session_state.panels = None
        st.session_state.generating_prompt = None
        st.session_state.current_title = "Comic Storyboard"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Gemini API Key Input Field
    st.markdown('<div style="font-size: 0.75rem; font-weight: 600; color: #8e8ea0; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 12px; margin-bottom: 6px;">Gemini API Key</div>', unsafe_allow_html=True)
    user_gemini_key = st.text_input(
        "Gemini Key",
        type="password",
        placeholder="Enter your Gemini API key...",
        label_visibility="collapsed",
        key="user_gemini_key_input"
    )
    if user_gemini_key.strip():
        st.markdown('<div style="font-size: 0.75rem; color: #10a37f; margin-bottom: 12px; font-weight: 500;">✓ Gemini API Connected</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="font-size: 0.78rem; font-weight: 600; color: #8e8ea0; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 16px; margin-bottom: 10px;">Recent Comics</div>', unsafe_allow_html=True)
    
    if not st.session_state.comic_history:
        st.markdown('<div style="font-size: 0.82rem; color: #666666; font-style: italic; padding: 0 4px;">No saved comics yet.</div>', unsafe_allow_html=True)
    else:
        for idx, item in enumerate(st.session_state.comic_history):
            title = item.get("title", f"Comic #{idx+1}")
            first_panel = item["panels"][0] if item.get("panels") else {}
            first_seed = item["seeds"][0] if item.get("seeds") else 100
            
            sb_col1, sb_col2 = st.sidebar.columns([0.8, 3.2])
            with sb_col1:
                thumb_img = fetch_panel_image(first_panel.get("prompt", "pencil sketch"), 0, first_seed)
                st.image(thumb_img, use_container_width=True)
            with sb_col2:
                st.markdown('<div class="sidebar-history-btn">', unsafe_allow_html=True)
                if st.button(title, key=f"hist_btn_{idx}", use_container_width=True):
                    st.session_state.panels = item["panels"]
                    st.session_state.seeds = item["seeds"]
                    st.session_state.current_title = item["title"]
                    st.session_state.generating_prompt = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# TOP PRIORITY: GENERATING STATE (Completely wipes out landing elements before processing)
if st.session_state.generating_prompt:
    prompt_to_run = st.session_state.generating_prompt
    entered_key = st.session_state.get("user_gemini_key_input", "")
    
    st.markdown("<div style='text-align: center; margin-top: 120px; font-size: 1.6rem; font-weight: 600; color: #ffffff;'>Generating Storyboard...</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 1rem; color: #10a37f; margin-top: 8px; margin-bottom: 40px;'>\"{prompt_to_run}\"</div>", unsafe_allow_html=True)
    
    with st.spinner("Processing story & pencil sketch art..."):
        generated_panels = generate_20_panel_story(prompt_to_run, user_api_key=entered_key)
        generated_seeds = [random.randint(1000, 999999) for _ in range(20)]
        
        st.session_state.panels = generated_panels
        st.session_state.seeds = generated_seeds
        st.session_state.current_title = prompt_to_run
        
        # Save to Session & Disk History
        st.session_state.comic_history.insert(0, {
            "title": prompt_to_run,
            "panels": generated_panels,
            "seeds": generated_seeds,
            "timestamp": time.strftime("%H:%M")
        })
        save_history_to_disk(st.session_state.comic_history)
        
        st.session_state.generating_prompt = None
    st.rerun()

# DISPLAY GENERATED COMIC VIEW
elif st.session_state.panels:
    active_title = st.session_state.get("current_title", "Comic Storyboard")
    st.markdown(f"<div style='font-size: 1.6rem; font-weight: 700; color: #ffffff; margin-bottom: 24px;'>{active_title}</div>", unsafe_allow_html=True)
    
    panels = st.session_state.panels
    seeds = st.session_state.seeds
    
    for row in range(0, 20, 4):
        cols = st.columns(4)
        for col_idx in range(4):
            panel_i = row + col_idx
            if panel_i < len(panels):
                p = panels[panel_i]
                seed = seeds[panel_i]
                
                with cols[col_idx]:
                    # Header bar with fixed height
                    st.markdown(
                        f'''
                        <div class="gpt-panel-header">
                            <span class="gpt-panel-badge">PANEL {panel_i+1}</span>
                            <span class="gpt-panel-sfx">{p.get("sfx", "ZAP!")}</span>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
                    
                    img_obj = fetch_panel_image(p.get("prompt", "pencil sketch"), panel_i, seed)
                    st.image(img_obj, use_container_width=True)
                    
                    # Standardized dialogue box with 24px bottom gap between rows
                    st.markdown(f'<div class="gpt-dialogue-text">"{p.get("dialogue", "")}"</div>', unsafe_allow_html=True)

    # Generate New Button at bottom of comic view
    st.markdown("<br style='margin-bottom: 16px;'>", unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns([3, 4, 3])
    with col_b2:
        st.markdown('<div class="primary-gen-btn">', unsafe_allow_html=True)
        if st.button("Generate New Comic", use_container_width=True, key="gen_new_bottom_btn"):
            st.session_state.panels = None
            st.session_state.generating_prompt = None
            st.session_state.current_title = "Comic Storyboard"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# LANDING PAGE (Only rendered when not generating and no comic active)
else:
    st.markdown('<div class="chatgpt-hero-title">What\'s on your mind today?</div>', unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 8, 1])
    with col_l2:
        c_txt, c_mic = st.columns([5.5, 1.5])
        with c_txt:
            prompt_input = st.text_input(
                "",
                placeholder="Ask anything or dictate your comic story idea...",
                label_visibility="collapsed",
                key="main_prompt_input"
            )
        with c_mic:
            voice_transcript = speech_to_text(
                language='en',
                use_container_width=True,
                just_once=True,
                key='landing_voice_mic'
            )

        # Suggestion Pills
        st.markdown("<div class='landing-sugg-container' style='margin-top: 24px;'>", unsafe_allow_html=True)
        sp1, sp2, sp3 = st.columns(3)
        sugg_clicked = None
        with sp1:
            if st.button("Cyberpunk Detective Jax in Neo-Tokyo", key="sugg1", use_container_width=True):
                sugg_clicked = "Cyberpunk Detective Jax uncovers an ancient alien artifact in Neo-Tokyo."
        with sp2:
            if st.button("Space Explorer discovering alien ruins", key="sugg2", use_container_width=True):
                sugg_clicked = "Space explorer discovering ancient alien ruins on a distant planet."
        with sp3:
            if st.button("Superhero defending futuristic city", key="sugg3", use_container_width=True):
                sugg_clicked = "A superhero defending a glowing futuristic metropolis from cyber villains."
        st.markdown("</div>", unsafe_allow_html=True)

        chosen_prompt = prompt_input if prompt_input else (voice_transcript if voice_transcript else (sugg_clicked if sugg_clicked else None))

        if chosen_prompt:
            st.session_state.generating_prompt = chosen_prompt
            st.rerun()
