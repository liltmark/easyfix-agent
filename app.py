"""
🔧 EasyFix Agent
========================================
Muhammad Mudassir Yaseen's team AI agent.

* Video Studio (AI video generation — 100% free)
* FB Marketplace Listing Generator
* Buyer Reply Assistant
* Voiceover Studio (free AI voices)
* Knowledge Base (all business knowledge)
* Tools Hub (all free tools, white-labeled)

Team system: admin (Mudasir) creates team members with unique
access codes + role-based permissions. Team works UNDER the admin.

CEO: MUHAMMAD MUDASSIR YASEEN
"""

from __future__ import annotations

import json
import random
import tempfile
import time
import traceback
import urllib.request

import streamlit as st
import streamlit.components.v1 as components
from gradio_client import Client


# ----------------------------------------------------------------------------
# OWNER SETTINGS
# ----------------------------------------------------------------------------
AD_HTML = """
<!-- Adsterra Social Bar (high CPM) -->
<script data-cfasync="false" src="https://bauval.org/14/06cfef510844ff8afa72574c902ab415"></script>
<!-- Adsterra Banner 300x250 -->
<script>
  atOptions = {
    'key' : '644d29a9d10373fa5f3a39e674d333cb',
    'format' : 'iframe',
    'height' : 250,
    'width' : 300,
    'params' : {}
  };
</script>
<script src="https://bauval.org/22/644d29a9d10373fa5f3a39e674d333cb"></script>
<!-- Adsterra Native Banner -->
<script async="async" data-cfasync="false" src="https://bauval.org/21/36bf4270f19cadf49600f4e0f50abe1c"></script>
<div id="container-36bf4270f19cadf49600f4e0f50abe1c"></div>
"""

AD_WAIT_SECONDS = 10

SURVEY_LINKS = [
    {"title": "Get $500 to Spend at Walmart!", "url": "https://singingfiles.com/show.php?l=0&u=2558676&id=74764", "desc": "Sweepstakes survey — win $500 for Walmart (iOS, USA)."},
    {"title": "Get $1000 on Your CashApp!", "url": "https://singingfiles.com/show.php?l=0&u=2558676&id=75222", "desc": "Sweepstakes survey — win $1000 on CashApp (iOS, USA)."},
    {"title": "Get a $100 Nike Gift Card!", "url": "https://singingfiles.com/show.php?l=0&u=2558676&id=75217", "desc": "$100 Nike gift card signup survey (Desktop, USA)."},
    {"title": "Get $100 to Spend at Ulta!", "url": "https://singingfiles.com/show.php?l=0&u=2558676&id=74436", "desc": "$100 Ulta signup survey (Desktop, USA)."},
    {"title": "Get $1000 CashApp Gift Card!", "url": "https://singingfiles.com/show.php?l=0&u=2558676&id=75220", "desc": "$1000 CashApp gift card survey (Desktop, USA)."},
    {"title": "Get $1000 to Spend at Walmart!", "url": "https://singingfiles.com/show.php?l=0&u=2558676&id=75095", "desc": "Sweepstakes — win $1000 for Walmart (Android, USA)."},
    {"title": "Get $100 at Jersey Mike's!", "url": "https://singingfiles.com/show.php?l=0&u=2558676&id=75134", "desc": "$100 Jersey Mike's signup survey (Desktop, USA)."},
    {"title": "Get $100 Ulta Gift Card Now!", "url": "https://singingfiles.com/show.php?l=0&u=2558676&id=74437", "desc": "$100 Ulta gift card sweepstakes (Android, USA)."},
    {"title": "Get the Best Samples Now!", "url": "https://singingfiles.com/show.php?l=0&u=2558676&id=75092", "desc": "Free product samples signup (Android, USA)."},
    {"title": "Register for ShopBack Now!", "url": "https://singingfiles.com/show.php?l=0&u=2558676&id=75420", "desc": "Cashback rewards signup (Desktop, USA)."},
]

# Admin password — Mudasir can change this in the Admin panel
DEFAULT_ADMIN_PASSWORD = "easyfix123"

# Branding
OWNER_NAME = "Muhammad Mudassir Yaseen"
SITE_URL = "https://www.easytofix.homes"
PHONE = "+18312931196"

# ----------------------------------------------------------------------------
# Public AI video engines (white-labeled — no third-party names shown)
# ----------------------------------------------------------------------------
SPACE_LTX = "Lightricks/ltx-video-distilled"
SPACE_COG5 = "zai-org/CogVideoX-5B-Space"
SPACE_COG2 = "zai-org/CogVideoX-2B-Space"
SPACE_WAN = "Upsampler/wan-2-2-14b-image-to-video"

JOB_TIMEOUT = 480
CONNECT_TIMEOUT = 20


def _ltx_submit(client: Client, kind: str, prompt: str, negative: str,
                image_path, width: int, height: int, duration: float,
                seed: int, guidance: float, drop_params=frozenset()):
    """Submit to LTX-Video Space. kind: 't2v' or 'i2v'."""
    rnd = (seed == -1)
    scale = min(1.0, 512.0 / max(width, height))
    w = int(width * scale) // 8 * 8
    h = int(height * scale) // 8 * 8
    dur = min(float(duration), 2.0)
    frames = max(9, min(257, int(dur * 24)))
    api = "/text_to_video" if kind == "t2v" else "/image_to_video"
    mode = "text-to-video" if kind == "t2v" else "image-to-video"
    kwargs = dict(
        prompt=prompt,
        negative_prompt=negative,
        input_image_filepath=image_path,
        input_video_filepath=None,
        height_ui=h,
        width_ui=w,
        mode=mode,
        duration_ui=dur,
        ui_frames_to_use=frames,
        seed_ui=0 if rnd else seed,
        randomize_seed=rnd,
        ui_guidance_scale=guidance,
        ui_steps=30,
        stg_mode="attention",
        stg_scale_ui=1.0,
        enhance_prompt=True,
    )
    for dp in drop_params:
        kwargs.pop(dp, None)
    return client.submit(api_name=api, **kwargs)


def _cog_submit(client: Client, kind: str, prompt: str, negative: str,
                image_path, width: int, height: int, duration: float,
                seed: int, guidance: float, drop_params=frozenset()):
    """Submit to CogVideoX Space (T2V only — no image param)."""
    rnd = (seed == -1)
    scale = min(1.0, 512.0 / max(width, height))
    w = int(width * scale) // 16 * 16
    h = int(height * scale) // 16 * 16
    dur = min(float(duration), 2.0)
    frames = max(9, min(49, int(dur * 8)))
    kwargs = dict(
        prompt=prompt,
        negative_prompt=negative,
        num_frames=frames,
        width=w,
        height=h,
        guidance_scale=guidance,
        num_inference_steps=30,
        seed=0 if rnd else seed,
        randomize_seed=rnd,
    )
    for dp in drop_params:
        kwargs.pop(dp, None)
    return client.submit(api_name="/generate", **kwargs)


def _wan_submit(client: Client, kind: str, prompt: str, negative: str,
                image_path, width: int, height: int, duration: float,
                seed: int, guidance: float, drop_params=frozenset()):
    """Submit to Wan 2.2 I2V Space."""
    rnd = (seed == -1)
    scale = min(1.0, 512.0 / max(width, height))
    w = int(width * scale) // 16 * 16
    h = int(height * scale) // 16 * 16
    dur = min(float(duration), 5.0)
    frames = max(9, min(121, int(dur * 24)))
    kwargs = dict(
        image=image_path,
        prompt=prompt,
        negative_prompt=negative,
        num_frames=frames,
        width=w,
        height=h,
        guidance_scale=guidance,
        num_inference_steps=25,
        seed=0 if rnd else seed,
        randomize_seed=rnd,
    )
    for dp in drop_params:
        kwargs.pop(dp, None)
    return client.submit(api_name="/generate", **kwargs)


SPACE_ADAPTERS = {
    SPACE_LTX:  {"label": "⚡ Turbo Engine", "fn": _ltx_submit},
    SPACE_COG5: {"label": "🎬 Pro Engine",   "fn": _cog_submit},
    SPACE_COG2: {"label": "🚀 Fast Engine",  "fn": _cog_submit},
    SPACE_WAN:  {"label": "🎨 HD Engine",    "fn": _wan_submit},
}

T2V_CHAIN = [SPACE_LTX]
I2V_CHAIN = [SPACE_WAN, SPACE_COG5]
STORY_CHAIN = [SPACE_WAN, SPACE_COG5]

_client_cache: dict = {}


def _client_timeout():
    try:
        import httpx
        return httpx.Timeout(connect=CONNECT_TIMEOUT, read=300.0,
                             write=60.0, pool=CONNECT_TIMEOUT)
    except Exception:
        return CONNECT_TIMEOUT


def get_client(space_id: str) -> Client:
    if space_id not in _client_cache:
        _client_cache[space_id] = Client(
            space_id, httpx_kwargs={"timeout": _client_timeout()})
    return _client_cache[space_id]


def _result_to_bytes(result) -> bytes:
    def _path_of(r):
        if isinstance(r, str):
            return r
        if isinstance(r, dict):
            for k in ("path", "url", "name"):
                if r.get(k):
                    return r[k]
        if isinstance(r, (list, tuple)) and r:
            return _path_of(r[0])
        return None

    path = _path_of(result)
    if not path:
        raise RuntimeError("Engine returned no video file")
    if path.startswith("http"):
        req = urllib.request.Request(path, headers={"User-Agent": "EasyFixAgent/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
    with open(path, "rb") as f:
        return f.read()


def generate_with_fallback(kind: str, status, preferred: str | None = None, **params):
    """Generate via free engines with automatic fallback."""
    chain = T2V_CHAIN if kind == "t2v" else I2V_CHAIN
    if preferred in chain:
        chain = [preferred] + [s for s in chain if s != preferred]

    last_exc: Exception | None = None
    for space_id in chain:
        label = SPACE_ADAPTERS[space_id]["label"]
        submit_fn = SPACE_ADAPTERS[space_id]["fn"]
        drop_params = set()
        for attempt in range(1, 7):
            try:
                status.update(label=f"🎥 Connecting to {label}…", state="running")
                client = get_client(space_id)
                call_params = dict(params)
                if drop_params:
                    call_params["drop_params"] = frozenset(drop_params)
                job = submit_fn(client, kind, **call_params)
                start = time.time()
                last_beat = 0.0
                while True:
                    if time.time() - start > JOB_TIMEOUT:
                        try:
                            job.cancel()
                        except Exception:
                            pass
                        raise TimeoutError(f"{label}: took longer than 8 minutes")
                    now = time.time()
                    if now - last_beat >= 25:
                        last_beat = now
                        elapsed = int(now - start)
                        status.update(
                            label=f"🎥 {label} working… ({elapsed}s elapsed)",
                            state="running")
                    try:
                        result = job.result(timeout=30)
                        video_bytes = _result_to_bytes(result)
                        status.update(label=f"✅ Done via {label}!", state="complete")
                        return video_bytes, label, space_id
                    except TimeoutError:
                        continue
            except Exception as exc:
                last_exc = exc
                msg = str(exc).lower()
                if "quota" in msg or "gpu" in msg or "busy" in msg:
                    break  # try next engine
                time.sleep(2)
    raise RuntimeError(
        f"All engines busy right now. Please try again in a few minutes. "
        f"(Last error: {last_exc})")


def extract_last_frame(video_bytes: bytes) -> str:
    """Save last frame of video to temp file. Returns path."""
    tmp_v = tempfile.mktemp(suffix=".mp4")
    with open(tmp_v, "wb") as f:
        f.write(video_bytes)
    tmp_jpg = tempfile.mktemp(suffix=".jpg")
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        import subprocess
        subprocess.run(
            [exe, "-y", "-v", "error", "-sseof", "-0.5", "-i", tmp_v,
             "-vframes", "1", "-q:v", "2", tmp_jpg],
            check=True, timeout=60)
    finally:
        try:
            import os
            os.remove(tmp_v)
        except OSError:
            pass
    return tmp_jpg


def stitch_clips(clips: list) -> bytes:
    """Concatenate MP4 clips with ffmpeg. Returns MP4 bytes."""
    import subprocess
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    tmpdir = tempfile.mkdtemp()
    paths = []
    for i, data in enumerate(clips):
        p = f"{tmpdir}/c{i}.mp4"
        with open(p, "wb") as f:
            f.write(data)
        paths.append(p)
    lst = f"{tmpdir}/list.txt"
    with open(lst, "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    out = f"{tmpdir}/out.mp4"
    subprocess.run(
        [exe, "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c", "copy", out],
        check=True, timeout=300)
    with open(out, "rb") as f:
        return f.read()


# ----------------------------------------------------------------------------
# Voiceover — free edge-tts voices
# ----------------------------------------------------------------------------
VOICES = {
    "🇺🇸 Guy (US Male)": "en-US-GuyNeural",
    "🇺🇸 Jenny (US Female)": "en-US-JennyNeural",
    "🇺🇸 Aria (US Female)": "en-US-AriaNeural",
    "🇬🇧 Ryan (UK Male)": "en-GB-RyanNeural",
    "🇵🇰 Asad (Urdu Male)": "ur-PK-AsadNeural",
    "🇵🇰 Uzma (Urdu Female)": "ur-PK-UzmaNeural",
}


async def _edge_tts_save(text: str, voice_id: str, out_path: str):
    import edge_tts
    comm = edge_tts.Communicate(text, voice_id)
    await comm.save(out_path)


def generate_voiceover(text: str, voice_id: str) -> bytes:
    import asyncio
    import os
    tmp = tempfile.mktemp(suffix=".mp3")
    asyncio.run(_edge_tts_save(text, voice_id, tmp))
    with open(tmp, "rb") as f:
        data = f.read()
    try:
        os.remove(tmp)
    except OSError:
        pass
    if not data:
        raise RuntimeError("Voiceover came back empty")
    return data


def mux_voiceover(video_bytes: bytes, audio_bytes: bytes) -> bytes:
    """Mux MP3 voiceover onto MP4 video. Returns MP4 bytes."""
    import subprocess
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    tmpdir = tempfile.mkdtemp()
    vp = f"{tmpdir}/v.mp4"
    ap = f"{tmpdir}/a.mp3"
    out = f"{tmpdir}/out.mp4"
    with open(vp, "wb") as f:
        f.write(video_bytes)
    with open(ap, "wb") as f:
        f.write(audio_bytes)
    subprocess.run(
        [exe, "-y", "-v", "error", "-i", vp, "-i", ap,
         "-c:v", "copy", "-c:a", "aac", "-shortest", out],
        check=True, timeout=300)
    with open(out, "rb") as f:
        return f.read()


# Pixabay free API key (stock videos — no quota). Set as env var on deploy.
PIXABAY_API_KEY = __import__("os").environ.get("PIXABAY_API_KEY", "")


def _pixabay_search(query: str, api_key: str, per_page: int = 12):
    """Search Pixabay videos. Returns list of dicts."""
    import json as _json
    import urllib.parse as _up
    q = _up.quote(query)
    per_page = max(3, min(200, per_page))
    url = (f"https://pixabay.com/api/videos/?key={_up.quote(api_key)}"
           f"&q={q}&per_page={per_page}&orientation=vertical&safesearch=true")
    req = urllib.request.Request(url, headers={"User-Agent": "EasyFixAgent/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = _json.loads(resp.read().decode())
    out = []
    for v in data.get("hits", []):
        vids = (v.get("videos") or {})
        best = vids.get("large") or vids.get("medium") or vids.get("small")
        if not best or not best.get("url"):
            continue
        out.append({
            "id": v.get("id"),
            "duration": v.get("duration"),
            "url": v.get("pageURL"),
            "preview": v.get("previewURL"),
            "file": best["url"],
            "width": best.get("width"),
            "height": best.get("height"),
        })
    return out


RESOLUTIONS = {
    "Portrait 720×1280 (Shorts)": (720, 1280),
    "Square 512×512": (512, 512),
    "Landscape 1280×720": (1280, 720),
}


# ----------------------------------------------------------------------------
# Free LLM (Groq / Gemini) — for Reply Assistant
# ----------------------------------------------------------------------------
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
GEMINI_MODELS = ["gemini-2.0-flash", "gemini-2.5-flash"]


def llm_complete(api_key: str, provider: str, model: str,
                 messages: list, temperature: float = 0.7) -> str:
    """Single non-streaming completion via Groq or Gemini (free tiers)."""
    import requests
    if provider == "Groq":
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages,
                  "temperature": temperature, "max_tokens": 1500},
            timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    else:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={api_key}")
        contents = []
        for m in messages:
            role = "user" if m["role"] in ("user", "system") else "model"
            contents.append({"role": role,
                             "parts": [{"text": m["content"]}]})
        r = requests.post(url, json={"contents": contents,
                                     "generationConfig": {"temperature": temperature}},
                          timeout=120)
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


# ----------------------------------------------------------------------------
# Team management (session-based)
# ----------------------------------------------------------------------------
ROLES = {
    "videos": "🎬 Videos",
    "listings": "📝 Listings",
    "replies": "💬 Replies",
    "voice": "🎙️ Voiceover",
    "all": "🌟 All modules",
}


def _init_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "team" not in st.session_state:
        st.session_state.team = {}  # code -> {name, roles}
    if "admin_password" not in st.session_state:
        st.session_state.admin_password = DEFAULT_ADMIN_PASSWORD
    if "activity" not in st.session_state:
        st.session_state.activity = []
    if "llm_key" not in st.session_state:
        st.session_state.llm_key = ""
    if "llm_provider" not in st.session_state:
        st.session_state.llm_provider = "Groq"
    if "llm_model" not in st.session_state:
        st.session_state.llm_model = GROQ_MODELS[0]
    if "videos_made" not in st.session_state:
        st.session_state.videos_made = 0


def log_activity(who: str, action: str):
    st.session_state.activity.append({
        "time": time.strftime("%Y-%m-%d %H:%M"),
        "who": who,
        "action": action,
    })
    st.session_state.activity = st.session_state.activity[-200:]


def can_access(module_key: str) -> bool:
    """Check if current user can access a module."""
    u = st.session_state.user
    if not u:
        return False
    if u.get("is_admin"):
        return True
    roles = u.get("roles", [])
    return "all" in roles or module_key in roles


# ----------------------------------------------------------------------------
# Knowledge base content
# ----------------------------------------------------------------------------
KB_CONTENT = {
    "🏢 Business": {
        "Company": "EasyFix — https://www.easytofix.homes",
        "Owner": "Muhammad Mudassir Yaseen",
        "Phone (listings)": "+18312931196",
        "Phone (profile)": "+447555857519",
        "Pricing": "$110 flat per service (all 11 services × 10 cities)",
        "Partners": "LeadSmart, MarketCall, NextPro (pay-per-call)",
        "RULE": "EVERY video caption on EVERY platform MUST include https://www.easytofix.homes",
    },
    "🎭 Characters": {
        "Pipe Pete": "🐱 Cat face + human body, plumber, blue uniform, red cap",
        "Garage Gary": "🐶 Dog face + human body, handyman, green shirt, tool belt",
        "Floor Frank": "🦁 Beast face, muscular, orange vest",
        "Style": "Anthropomorphic animal faces + human bodies. NO cropped heads/feet. NO burned-in text.",
    },
    "📅 Daily Video Rules": {
        "Schedule": "3 Shorts/day at 07:20, 13:00, 18:30 America/New_York",
        "Length": "MINIMUM 30 seconds each — non-negotiable",
        "Format": "Vertical 9:16, 1080×1920, real AI motion (never slideshow)",
        "Style": "Funny + educational (E3R style), American English",
        "Platforms": "YouTube, Instagram, Dailymotion, Rumble — ALL FOUR every time",
        "Titles": "USA-style, e.g. 'Drain Cleaning in Houston — $110'",
    },
    "💡 Key Ideas": {
        "Free-only": "Never propose paid tools. User cannot spend more money.",
        "QC first": "Before ANY work: check credits, logins, quotas, blockers.",
        "Listen first": "'ruk' means STOP. Confirm before each step on accounts.",
        "Reality-based": "Never promise what can't be delivered. Say 'pata nahi, check karta hun' if unsure.",
        "Ad model": "Free tool + ads (Adsterra) + surveys (CPAGrip) = earning without charging users.",
        "White-label": "Hide third-party branding. Neutral engine names. No referral links visible.",
    },
    "🛠️ Free AI Video Tools": {
        "Google Flow": "50 free credits/day/account — best for quality clips",
        "CapCut AI": "Free AI text-to-video (suggested by user)",
        "LTX-Video": "Free via public Spaces (this app's Turbo Engine)",
        "Wan 2.2": "Free I2V via public Spaces (this app's HD Engine)",
        "Colab T4": "Free GPU — SadTalker lip-sync, Wav2Lip",
        "Pixabay": "Free stock videos, no quota (API key in env)",
    },
}


# ----------------------------------------------------------------------------
# Page setup + EasyFix branding
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="🔧 EasyFix Agent",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #0a0f0a; }
    section[data-testid="stSidebar"] { background: #101510; border-right: 1px solid #232d23; }
    .stApp, .stApp p, .stApp div, .stApp span, .stApp label { color: #e4e4e7 !important; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #ffffff !important; font-weight: 700 !important; }
    .stMarkdown p { color: #e4e4e7 !important; font-weight: 500; }
    .stCaption { color: #a1a1aa !important; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label {
        color: #e4e4e7 !important; font-weight: 500;
    }
    .hero {
        background: linear-gradient(135deg, #4ade80 0%, #22d3ee 50%, #fbbf24 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
        font-size: 2.8rem; font-weight: 900; letter-spacing: -0.02em; margin-bottom: 0;
    }
    .owner-badge {
        display: inline-block; background: linear-gradient(135deg, #15803d, #0e7490);
        color: white; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.1em;
        padding: 0.35rem 1rem; border-radius: 20px; margin-bottom: 0.8rem;
        box-shadow: 0 4px 15px rgba(21,128,61,0.4);
    }
    .free-badge {
        display: inline-block; background: linear-gradient(135deg, #16a34a, #4ade80);
        color: #052e16; font-size: 0.8rem; font-weight: 900; letter-spacing: 0.1em;
        padding: 0.35rem 1rem; border-radius: 20px; margin-bottom: 0.8rem;
        margin-left: 0.5rem;
        box-shadow: 0 4px 15px rgba(74,222,128,0.4);
    }
    .sub { color: #a1a1aa; margin-top: 0.3rem; margin-bottom: 1.2rem; font-size: 1.05rem; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #16a34a, #0891b2); border: none;
        font-weight: 700; border-radius: 12px; padding: 0.6rem 1.5rem;
        box-shadow: 0 4px 20px rgba(22,163,74,0.4);
    }
    .stButton > button:not([kind="primary"]) { border-radius: 10px; border: 1px solid #3f3f46; }
    .tip {
        background: linear-gradient(135deg, rgba(22,163,74,0.15), rgba(8,145,178,0.08));
        border: 1px solid rgba(74,222,128,0.3); border-radius: 14px;
        padding: 0.9rem 1.2rem; margin: 0.8rem 0;
    }
    .side-logo {
        font-size: 1.5rem; font-weight: 900; margin-bottom: 0.2rem;
        background: linear-gradient(135deg, #4ade80 0%, #22d3ee 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    .tool-card {
        background: #141a14; border: 1px solid #2a352a; border-radius: 14px;
        padding: 1rem 1.2rem; margin: 0.6rem 0;
    }
    .footer { text-align: center; color: #71717a; font-size: 0.85rem;
              margin-top: 0.5rem; padding-top: 1rem; border-top: 1px solid #232d23; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border-radius: 10px; border: 1px solid #52525b;
        background-color: #18181b !important; color: #ffffff !important;
        font-weight: 600 !important; font-size: 15px !important;
    }
    .stExpander { border-radius: 12px; border: 1px solid #27272a; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    .stDeployButton { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

_init_state()

st.markdown('<p class="hero">🔧 EasyFix Agent</p>', unsafe_allow_html=True)
st.markdown('<span class="owner-badge">👑 Built for Muhammad Mudassir Yaseen</span>'
            '<span class="free-badge">💯 100% FREE — no paid credits, ever</span>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="sub">Your team\'s AI command center — videos, listings, replies, '
    'voiceovers. Everything free: free AI keys (signup only, no payment), '
    'free voiceovers, free stock video. '
    '<a href="https://www.easytofix.homes" '
    'style="color:#4ade80;">easytofix.homes</a></p>',
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Login
# ----------------------------------------------------------------------------
def show_login():
    st.subheader("🔐 Sign In")
    st.markdown('<span class="free-badge">💯 100% FREE — no paid credits, ever</span>',
                unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["👑 Admin", "👥 Team Member"])

    with tab1:
        pw = st.text_input("Admin password", type="password", key="admin_pw")
        if st.button("Sign in as Admin", type="primary", key="admin_login"):
            if pw == st.session_state.admin_password:
                st.session_state.logged_in = True
                st.session_state.user = {"name": "Mudasir (Admin)",
                                         "is_admin": True, "roles": ["all"]}
                log_activity("Admin", "signed in")
                st.rerun()
            else:
                st.error("❌ Wrong password")

    with tab2:
        code = st.text_input("Your team access code", key="team_code",
                             placeholder="Ask Mudasir for your code")
        if st.button("Join as Team Member", type="primary", key="team_login"):
            member = st.session_state.team.get(code.strip())
            if member:
                st.session_state.logged_in = True
                st.session_state.user = {"name": member["name"],
                                         "is_admin": False,
                                         "roles": member["roles"],
                                         "code": code.strip()}
                log_activity(member["name"], "signed in")
                st.rerun()
            else:
                st.error("❌ Invalid code — ask Mudasir for your access code")


if not st.session_state.logged_in:
    show_login()
    st.stop()


# ----------------------------------------------------------------------------
# Ad gate (after login, once per session)
# ----------------------------------------------------------------------------
if "ad_watched" not in st.session_state:
    st.session_state.ad_watched = False
    st.session_state.gate_start = time.time()

if not st.session_state.ad_watched:
    st.subheader("📺 A Quick Ad Before You Start")
    st.write(
        "EasyFix Agent is **completely free** — ads keep it that way. "
        f"Wait **{AD_WAIT_SECONDS} seconds**, then click Continue.")
    _ad = AD_HTML.strip() or '<div style="color:#9ca3af;">📢 Ad</div>'
    try:
        components.html(_ad, height=300, scrolling=True)
    except Exception:
        st.info("📢 Ad")
    if st.button("✅ Continue", type="primary", use_container_width=True):
        if time.time() - st.session_state.gate_start < AD_WAIT_SECONDS:
            st.warning("⏳ A few more seconds…")
        else:
            st.session_state.ad_watched = True
            st.rerun()
    st.stop()


# ----------------------------------------------------------------------------
# Sidebar navigation (role-based)
# ----------------------------------------------------------------------------
user = st.session_state.user
is_admin = user.get("is_admin", False)

PAGES = []
if is_admin:
    PAGES.append("👑 Admin Panel")
if can_access("videos"):
    PAGES += ["🎬 Video Studio", "🎙️ Voiceover Studio"]
if can_access("listings"):
    PAGES.append("📝 Listing Generator")
if can_access("replies"):
    PAGES.append("💬 Reply Assistant")
PAGES += ["🧠 Knowledge Base", "🔗 Tools Hub", "📋 Surveys"]

with st.sidebar:
    st.markdown('<p class="side-logo">🔧 EasyFix Agent</p>', unsafe_allow_html=True)
    st.caption(f"👤 {user['name']}")
    if is_admin:
        st.success("👑 Admin mode")
    page = st.radio("Navigation", PAGES, label_visibility="collapsed")
    st.divider()
    if st.button("🚪 Sign out"):
        log_activity(user["name"], "signed out")
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.ad_watched = False
        st.rerun()
    st.markdown(
        '<p style="font-size:0.8rem;color:#71717a;text-align:center;">'
        '🔧 EasyFix Agent<br>👑 Muhammad Mudassir Yaseen<br>'
        '💯 100% FREE — no paid credits, ever<br>'
        '<a href="https://www.easytofix.homes" style="color:#4ade80;">'
        'easytofix.homes</a></p>',
        unsafe_allow_html=True,
    )


def show_ad_slot(height: int = 280):
    """Render one ad slot (monetization)."""
    try:
        components.html(AD_HTML.strip(), height=height, scrolling=True)
    except Exception:
        pass


def maybe_survey_gate():
    """Every 3rd video → show a survey before download unlocks."""
    st.session_state.videos_made += 1
    if st.session_state.videos_made % 3 == 0:
        s = random.choice(SURVEY_LINKS)
        st.info("📋 **Quick survey unlocks your download** — "
                "it supports this free tool!")
        st.markdown(f"**{s['title']}**")
        st.caption(s["desc"])
        st.link_button("▶ Complete Survey to Unlock", s["url"])
        return False
    return True


# ----------------------------------------------------------------------------
# 👑 Admin Panel
# ----------------------------------------------------------------------------
if page == "👑 Admin Panel":
    st.subheader("👑 Admin Panel")
    st.caption("Manage your team — they work under you with limited access.")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["👥 Team Members", "🔑 API Key", "📊 Activity Log", "⚙️ Settings"])

    with tab1:
        st.markdown("### Add team member")
        c1, c2 = st.columns(2)
        with c1:
            m_name = st.text_input("Member name", key="m_name",
                                   placeholder="e.g. Ahmed")
        with c2:
            m_roles = st.multiselect("Modules allowed", list(ROLES.keys()),
                                     format_func=lambda k: ROLES[k],
                                     key="m_roles")
        if st.button("➕ Create member", type="primary"):
            if not m_name.strip():
                st.error("Enter a name")
            elif not m_roles:
                st.error("Pick at least one module")
            else:
                code = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))
                st.session_state.team[code] = {"name": m_name.strip(),
                                               "roles": m_roles}
                log_activity("Admin", f"created member {m_name} ({code})")
                st.success(f"✅ **{m_name}** created! Access code: **{code}**")
                st.info("Share this code with them privately. "
                        "They can only see their assigned modules.")

        st.divider()
        st.markdown("### Current team")
        if not st.session_state.team:
            st.info("No team members yet.")
        for code, m in list(st.session_state.team.items()):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 3, 1])
                with c1:
                    st.markdown(f"**{m['name']}**")
                    st.caption(f"Code: `{code}`")
                with c2:
                    st.caption(", ".join(ROLES[r] for r in m["roles"]))
                with c3:
                    if st.button("🗑️", key=f"del_{code}"):
                        log_activity("Admin", f"removed member {m['name']}")
                        del st.session_state.team[code]
                        st.rerun()

    with tab2:
        st.markdown("### 💯 Free AI key (for Reply Assistant)")
        st.caption("Get a FREE key — signup only, **no payment, no credit card**. "
                   "The whole team shares it (they never see it).")
        prov = st.selectbox("Provider", ["Groq", "Gemini"], key="adm_prov",
                            help="Both are free tiers — never pick a paid plan.")
        st.session_state.llm_provider = prov
        models = GROQ_MODELS if prov == "Groq" else GEMINI_MODELS
        st.session_state.llm_model = st.selectbox("Model", models, key="adm_model")
        key = st.text_input("API key", type="password", key="adm_key",
                            value=st.session_state.llm_key)
        if st.button("💾 Save key", type="primary"):
            st.session_state.llm_key = key.strip()
            log_activity("Admin", "updated API key")
            st.success("✅ Key saved (team members cannot see it)")
        st.caption("🆓 Groq free key: console.groq.com → Sign up free → API Keys "
                   "(no payment) | 🆓 Gemini free key: aistudio.google.com → "
                   "Get API key (no payment)")

    with tab3:
        st.markdown("### Activity log")
        if not st.session_state.activity:
            st.info("No activity yet.")
        for a in reversed(st.session_state.activity[-50:]):
            st.caption(f"`{a['time']}` — **{a['who']}**: {a['action']}")

    with tab4:
        st.markdown("### Change admin password")
        npw = st.text_input("New password", type="password", key="npw")
        if st.button("💾 Update password", type="primary"):
            if len(npw) >= 6:
                st.session_state.admin_password = npw
                log_activity("Admin", "changed password")
                st.success("✅ Password updated")
            else:
                st.error("Minimum 6 characters")


# ----------------------------------------------------------------------------
# 🎬 Video Studio
# ----------------------------------------------------------------------------
elif page == "🎬 Video Studio":
    st.subheader("🎬 Video Studio")
    st.caption("AI video generation — 100% free. Merged from your video tool.")

    mode = st.radio("Mode", ["🎬 Text to Video", "🖼️ Image to Video"],
                    horizontal=True)

    with st.sidebar:
        st.divider()
        st.subheader("⚙️ Settings")
        engine_ids = list(SPACE_ADAPTERS.keys())
        engine_labels = ["Auto (recommended)"] + [
            SPACE_ADAPTERS[s]["label"] for s in engine_ids]
        eng_choice = st.selectbox("Engine", engine_labels)
        preferred = (engine_ids[engine_labels.index(eng_choice) - 1]
                     if not eng_choice.startswith("Auto") else None)
        res_label = st.selectbox("Resolution", list(RESOLUTIONS.keys()), index=0)
        width, height = RESOLUTIONS[res_label]
        duration = st.slider("Duration (sec)", 1, 8, 3)
        guidance = st.slider("Guidance", 1.0, 10.0, 5.0, 0.5)

    prompt = st.text_area("Prompt", height=100,
                          placeholder="A cheerful plumber waves hello, bright workshop…")
    negative = st.text_input("Negative prompt (optional)",
                             value="blurry, low quality, distorted faces, watermark, text")

    image_path = None
    if mode == "🖼️ Image to Video":
        up = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
        if up:
            image_path = tempfile.mktemp(suffix=".jpg")
            with open(image_path, "wb") as f:
                f.write(up.read())
            st.image(up, width=300)

    st.subheader("🎙️ Voiceover (optional)")
    voice_script = st.text_area("Voiceover script", height=80,
                                placeholder="Leave blank for silent video")
    voice_label = st.selectbox("Voice", list(VOICES.keys()))

    if st.button("🚀 Generate Video", type="primary", use_container_width=True):
        if not prompt.strip():
            st.error("Write a prompt first")
        elif mode == "🖼️ Image to Video" and not image_path:
            st.error("Upload an image first")
        else:
            kind = "t2v" if mode == "🎬 Text to Video" else "i2v"
            log_activity(user["name"], f"generated {kind} video")
            with st.status("🎥 Generating…", expanded=True) as status:
                try:
                    video_bytes, label, _ = generate_with_fallback(
                        kind, status, preferred=preferred,
                        prompt=prompt.strip(), negative=negative,
                        image_path=image_path, width=width, height=height,
                        duration=duration, seed=-1, guidance=guidance)
                    if voice_script.strip():
                        status.update(label="🎙️ Adding voiceover…",
                                      state="running")
                        audio = generate_voiceover(
                            voice_script.strip(), VOICES[voice_label])
                        video_bytes = mux_voiceover(video_bytes, audio)
                    st.session_state.last_video = video_bytes
                    st.session_state.last_label = label
                except Exception as e:
                    st.error(f"❌ {e}")
                    st.stop()

    if st.session_state.get("last_video"):
        st.success(f"✅ Video ready! ({st.session_state.get('last_label', '')})")
        st.video(st.session_state.last_video)
        show_ad_slot(250)
        if maybe_survey_gate():
            st.download_button("⬇️ Download MP4", st.session_state.last_video,
                               file_name="easyfix-video.mp4",
                               mime="video/mp4", type="primary",
                               use_container_width=True)


# ----------------------------------------------------------------------------
# 🎙️ Voiceover Studio
# ----------------------------------------------------------------------------
elif page == "🎙️ Voiceover Studio":
    st.subheader("🎙️ Voiceover Studio")
    st.caption("Free AI voices — perfect for video narration.")

    script = st.text_area("Script", height=150,
                          placeholder="Paste your video script here…")
    vlabel = st.selectbox("Voice", list(VOICES.keys()), key="vs_voice2")

    if st.button("🎙️ Generate Voiceover", type="primary",
                 use_container_width=True):
        if not script.strip():
            st.error("Write a script first")
        else:
            log_activity(user["name"], "generated voiceover")
            with st.spinner("🎙️ Generating voice…"):
                try:
                    audio = generate_voiceover(script.strip(), VOICES[vlabel])
                    st.session_state.last_audio = audio
                    st.success("✅ Voiceover ready!")
                except Exception as e:
                    st.error(f"❌ {e}")

    if st.session_state.get("last_audio"):
        st.audio(st.session_state.last_audio, format="audio/mp3")
        st.download_button("⬇️ Download MP3", st.session_state.last_audio,
                           file_name="easyfix-voiceover.mp3",
                           mime="audio/mp3", type="primary")


# ----------------------------------------------------------------------------
# 📝 FB Listing Generator
# ----------------------------------------------------------------------------
elif page == "📝 Listing Generator":
    st.subheader("📝 FB Marketplace Listing Generator")
    st.caption("Fill in the details → get a ready-to-post listing. "
               "Copy it and post manually on Facebook.")

    c1, c2 = st.columns(2)
    with c1:
        service = st.selectbox("Service", [
            "Drain Cleaning", "Leak Repair", "Faucet Installation",
            "Toilet Repair", "Water Heater Service", "Pipe Repair",
            "Garbage Disposal", "Sewer Line", "Fixture Installation",
            "Emergency Plumbing", "General Handyman"])
        city = st.text_input("City", placeholder="e.g. Houston")
        price = st.text_input("Price", value="$110")
    with c2:
        condition = st.selectbox("Condition", ["New service", "Repair", "Install"])
        extra = st.text_area("Extra details (optional)", height=80,
                             placeholder="Same-day service, warranty info…")

    if st.button("✨ Generate Listing", type="primary", use_container_width=True):
        if not city.strip():
            st.error("Enter a city")
        else:
            log_activity(user["name"],
                         f"generated listing: {service} in {city}")
            title = f"{service} in {city} — {price}"
            desc = (
                f"🔧 {service} in {city}!\n\n"
                f"✅ Professional service — {price} flat\n"
                f"✅ {condition}\n"
                f"✅ Licensed & insured pros\n"
                f"✅ Same-day service available\n"
            )
            if extra.strip():
                desc += f"✅ {extra.strip()}\n"
            desc += (
                f"\n📞 Call/Text: {PHONE}\n"
                f"🌐 {SITE_URL}\n\n"
                f"USA Trade Confessions — trusted home services!"
            )
            st.markdown("### 📋 Your listing")
            st.text_input("Title (copy)", value=title, key="lst_title")
            st.text_area("Description (copy)", value=desc, height=260,
                         key="lst_desc")
            st.success("✅ Copy the title + description and post on "
                       "Facebook Marketplace manually.")
            st.caption("⚠️ Always post manually — automated posting gets "
                       "blocked by Facebook.")


# ----------------------------------------------------------------------------
# 💬 Reply Assistant
# ----------------------------------------------------------------------------
elif page == "💬 Reply Assistant":
    st.subheader("💬 Buyer Reply Assistant")
    st.caption("Paste a buyer's message → get 3 professional reply drafts. "
               "Copy the best one and send it yourself.")

    if not st.session_state.llm_key:
        st.warning("⚠️ The admin hasn't added the free AI key yet "
                   "(free signup, no payment). "
                   "Ask Mudasir to add it in Admin Panel → API Key.")
        st.stop()

    buyer_msg = st.text_area("Buyer's message", height=100,
                             placeholder="Paste what the buyer wrote…")
    tone = st.selectbox("Tone", ["Friendly & professional", "Short & direct",
                                 "Warm & detailed"])

    if st.button("✨ Generate Replies", type="primary",
                 use_container_width=True):
        if not buyer_msg.strip():
            st.error("Paste the buyer's message first")
        else:
            log_activity(user["name"], "generated buyer replies")
            with st.spinner("💬 Writing replies…"):
                try:
                    system = (
                        "You are the customer-service assistant for EasyFix "
                        f"({SITE_URL}), owned by Muhammad Mudassir Yaseen. "
                        "Services cost $110 flat. Phone: +18312931196. "
                        f"Tone: {tone}. Write in American English. "
                        "Generate exactly 3 different reply drafts, numbered "
                        "1-3, each 2-4 sentences. Be helpful, never pushy."
                    )
                    out = llm_complete(
                        st.session_state.llm_key,
                        st.session_state.llm_provider,
                        st.session_state.llm_model,
                        [{"role": "system", "content": system},
                         {"role": "user",
                          "content": f"Buyer wrote: {buyer_msg.strip()}"}])
                    st.markdown("### 📋 Reply drafts")
                    st.markdown(out)
                    st.caption("Copy the best draft and send it manually. "
                               "Always include the website link: " + SITE_URL)
                except Exception as e:
                    st.error(f"❌ AI error: {e}. The free key may be invalid "
                             "or rate-limited.")


# ----------------------------------------------------------------------------
# 🧠 Knowledge Base
# ----------------------------------------------------------------------------
elif page == "🧠 Knowledge Base":
    st.subheader("🧠 Knowledge Base")
    st.caption("Everything the team needs to know — searchable.")

    q = st.text_input("🔍 Search", placeholder="e.g. price, schedule, characters…")
    for section, items in KB_CONTENT.items():
        with st.expander(section, expanded=not q):
            for k, v in items.items():
                if not q or q.lower() in (k + v).lower():
                    st.markdown(f"**{k}:** {v}")

    st.divider()
    st.markdown("### 📏 Standing rules (never break)")
    st.markdown("""
    1. **Website link rule:** EVERY caption on EVERY platform MUST include
       https://www.easytofix.homes
    2. **Free-only:** never propose paid tools or services
    3. **QC first:** check credits, logins, quotas before starting work
    4. **Video minimum:** 30 seconds per Short, vertical 9:16, no burned-in text
    5. **Post everywhere:** YouTube + Instagram + Dailymotion + Rumble
    6. **Manual posting:** never use bots on Facebook (account gets blocked)
    """)


# ----------------------------------------------------------------------------
# 🔗 Tools Hub
# ----------------------------------------------------------------------------
elif page == "🔗 Tools Hub":
    st.subheader("🔗 Tools Hub")
    st.caption("All free tools for the team — with proper descriptions.")

    # ---------------------------------------------------------------
    # 🎞️ Free Animated / AI Video Sources Hub
    # ---------------------------------------------------------------
    st.markdown("## 🎞️ Free Video Sources Hub")
    st.info("**Honest quota guide:** AI *generation* always has daily/queue "
            "limits on free tiers. *Stock video* (Pixabay) is the truly "
            "unlimited path — no generation quota at all.")

    # --- Pixabay direct integration (truly unlimited stock) ---
    with st.expander("🟢 🎞️ Pixabay — Stock Videos (TRULY UNLIMITED) ✅",
                     expanded=True):
        st.markdown("**What:** Millions of free stock videos — plumbing, "
                    "electrical, HVAC, lifestyle.")
        st.markdown("**Quota:** ✅ **Truly unlimited** — stock has no "
                    "generation quota. Download as much as you need.")
        st.markdown("**How-to:** Type a keyword below → Search → preview → "
                    "download. Use clips as B-roll in your Shorts.")
        if not PIXABAY_API_KEY:
            st.warning("⚠️ Admin: set the `PIXABAY_API_KEY` env var on "
                       "Streamlit Cloud (App settings → Secrets) to enable "
                       "search. Key is free at pixabay.com/api/docs")
        px_presets = {
            "🔧 Plumbing": "plumber plumbing repair",
            "⚡ Electrical": "electrician electrical work",
            "🚪 Garage Door": "garage door repair",
            "🏠 Roofing": "roofing roof repair",
            "❄️ HVAC": "hvac air conditioner technician",
            "🎨 Painting": "house painting painter",
            "🏡 Home": "modern house exterior",
            "🔨 Tools": "tools workshop",
        }
        px_cols = st.columns(4)
        for i, (label, q) in enumerate(px_presets.items()):
            if px_cols[i % 4].button(label, use_container_width=True,
                                     key=f"pxp_{i}"):
                st.session_state["px_query"] = q
        px_query = st.text_input(
            "Search Pixabay videos",
            value=st.session_state.get("px_query", "plumber"),
            key="px_search_box")
        if st.button("🔍 Search Pixabay", type="primary",
                     key="px_search_btn") and px_query:
            if not PIXABAY_API_KEY:
                st.error("No API key configured — ask the admin.")
            else:
                with st.spinner("Searching Pixabay…"):
                    try:
                        st.session_state["px_results"] = _pixabay_search(
                            px_query, PIXABAY_API_KEY)
                    except Exception as e:
                        st.error(f"Search failed: {e}")
        for r in st.session_state.get("px_results", []):
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if r["preview"]:
                        st.image(r["preview"], use_container_width=True)
                with c2:
                    st.write(f"⏱️ {r['duration']}s • 📐 "
                             f"{r['width']}×{r['height']}")
                    if st.button("⬇️ Download", key=f"pxdl_{r['id']}"):
                        with st.spinner("Downloading…"):
                            try:
                                req = urllib.request.Request(
                                    r["file"],
                                    headers={"User-Agent": "Mozilla/5.0"})
                                with urllib.request.urlopen(req,
                                                             timeout=120) as resp:
                                    data = resp.read()
                                st.session_state[f"pxvid_{r['id']}"] = data
                                log_activity(user["name"],
                                             f"downloaded Pixabay video {r['id']}")
                                st.success(f"✅ Downloaded "
                                           f"({len(data)//1024} KB)")
                            except Exception as e:
                                st.error(f"Download failed: {e}")
                    data = st.session_state.get(f"pxvid_{r['id']}")
                    if data:
                        st.download_button("💾 Save MP4", data,
                                           file_name=f"pixabay_{r['id']}.mp4",
                                           mime="video/mp4",
                                           key=f"pxsv_{r['id']}")

    # --- Other sources: honest quota cards ---
    st.markdown("### 📊 All free sources — honest limits")
    SOURCES = [
        ("🎞️ Pexels (stock video)",
         "Free stock videos, like Pixabay.",
         "⚠️ New API-key signups are PAUSED (since Oct 2026) — existing keys still work.",
         "https://www.pexels.com",
         "Use only if you already have a key; otherwise use Pixabay above."),
        ("🌊 Google Flow",
         "Google's AI video generator — best free quality for short AI clips.",
         "🎟️ 50 free credits/day per account. Multi-account rotation stretches this.",
         "https://labs.google/fx/tools/flow",
         "Make 1 free account per team member → 50 credits each, every day."),
        ("✂️ CapCut (AI text-to-video)",
         "Free AI text-to-video + full Shorts editor in one app.",
         "🎟️ Free tier has daily AI-generation limits; editor itself is unlimited.",
         "https://www.capcut.com",
         "Generate the clip in CapCut AI, then edit + captions in the same app."),
        ("📓 Colab Free T4 GPU",
         "Free cloud GPU — SadTalker lip-sync, Wav2Lip, Wan 2.1 video models.",
         "🎟️ Free GPU quota is limited & throttled — sessions can be cut at peak times.",
         "https://colab.research.google.com",
         "Open a notebook → Runtime → Change runtime type → T4 GPU → run cells."),
        ("🌌 ZSky (free tier)",
         "AI video generation with a free account tier.",
         "🎟️ Free tier = limited generations/day + watermark/queue at peak times.",
         "https://zsky.ai",
         "Sign up free, generate clips, trim any end-card before uploading."),
        ("🤗 Hugging Face Spaces (video models)",
         "Community demos of open video models — LTX-Video, Wan 2.2, CogVideoX.",
         "🎟️ ZeroGPU free quota ≈ a few short clips, then queue/cool-down. "
         "Only ~2–3s clips fit the free GPU limit.",
         "https://huggingface.co/spaces",
         "This app's 🎬 Video Studio already uses these engines with auto-fallback."),
    ]
    for title, what, quota, url, howto in SOURCES:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(f"**What:** {what}")
            st.caption(f"**Limit:** {quota}")
            st.caption(f"**How-to:** {howto}")
            st.link_button("Open →", url)

    st.divider()
    st.markdown("### 🧰 General tools")
    TOOLS = [
        ("🎬 Imposter Video Studio",
         "AI text-to-video & image-to-video generator — 100% free, no API keys.",
         "https://free-ai-video-studio-c4mdwne7wccbeoeagz9zaz.streamlit.app/"),
        ("🤖 Personal Agent",
         "Mudasir's personal AI assistant — chat, scripts, business advice.",
         "https://my-personal-agent-cvvehdim7bte3vgcdjmjnn.streamlit.app/"),
        ("🌐 easytofix.homes",
         "Official EasyFix website — plumbing & home services.",
         "https://www.easytofix.homes"),
        ("💬 EasyFix Chatbot",
         "AI customer-service chatbot for the website.",
         "https://udify.app/chat/Rd2QGqnWBPY9LZrq"),
    ]
    for title, desc, url in TOOLS:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{title}**")
                st.caption(desc)
            with c2:
                st.link_button("Open →", url)


# ----------------------------------------------------------------------------
# 📋 Surveys
# ----------------------------------------------------------------------------
elif page == "📋 Surveys":
    st.subheader("📋 Surveys")
    st.write("Complete surveys — they keep EasyFix Agent free for everyone.")
    for s in SURVEY_LINKS:
        with st.container(border=True):
            st.markdown(f"**{s['title']}**")
            st.caption(s["desc"])
            st.link_button("▶ Start Survey", s["url"])


# ----------------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------------
st.markdown(
    '<p class="footer">🔧 <b>EasyFix Agent</b> — built for '
    '<b>Muhammad Mudassir Yaseen</b> · 💯 <b>100% FREE</b> — no paid credits, ever<br>'
    '🌐 <a href="https://www.easytofix.homes" style="color:#4ade80;">'
    'easytofix.homes</a> · 📞 +18312931196</p>',
    unsafe_allow_html=True,
)
