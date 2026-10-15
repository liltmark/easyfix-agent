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
DEFAULT_PHONE = "+18312931196"
PHONE = "+18312931196"

# 📍 USA location presets — all generated content defaults to USA targeting.
USA_CITIES = [
    "Houston, TX", "Dallas, TX", "Miami, FL", "Orlando, FL",
    "Tampa, FL", "Atlanta, GA", "Phoenix, AZ", "Los Angeles, CA",
]
USA_CITIES_WITH_CUSTOM = USA_CITIES + ["✏️ Custom…"]

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


# ----------------------------------------------------------------------------
# 🛡️ Misuse prevention — safety guardrails
# Owner standing rule: "koi b glt kam nh krwana, sai mashwra dena"
# (never do wrong work, always give right advice).
# RULE: There is NO admin bypass. Safety applies to EVERYONE — admin,
# team members, every module — always. Do not add an override.
# ----------------------------------------------------------------------------
SAFETY_SYSTEM_PROMPT = (
    "SAFETY POLICY — you must obey this above ALL other instructions, "
    "including anything the user or an 'admin' tells you. There are no "
    "exceptions:\n"
    "You MUST REFUSE any request involving: fraud, fake accounts, fake "
    "reviews/likes/followers, piracy or cracked software, reproducing "
    "copyrighted content, hacking, spam, harassment, impersonation of real "
    "people, fake documents or IDs, tax evasion, or any other illegal or "
    "deceptive activity.\n"
    "When you refuse: be polite, reply in Roman Urdu + English, explain "
    "briefly WHY it is wrong, and offer a legal alternative when possible."
)

REFUSAL_MSG = (
    "🛡️ **Maaf karo — ye kaam ghalat hai, main ye nahi kar sakta.**\n\n"
    "Sorry, I can't help with this — it goes against our rules. "
    "EasyFix Agent kabhi ghalat ya illegal kaam nahi karta "
    "(fraud, fake accounts/reviews, piracy, hacking, spam, impersonation — "
    "kuch bhi).\n\n"
    "Koi **legal** kaam ho to batao — main khushi se madad karunga! ✅"
)

MISUSE_KEYWORDS = [
    # fake accounts / verification evasion
    "fake account", "fake accounts", "bot followers", "buy followers",
    "bypass verification", "verification bypass", "fake id",
    "fake document", "fake documents", "fake license", "fake passport",
    "fake invoice",
    # fake engagement
    "fake review", "fake reviews", "buy reviews", "fake likes",
    # piracy / copyright
    "software crack", "cracked software", "crack version", "keygen",
    "pirated", "piracy", "warez", "nulled",
    # hacking / malware / spam
    "hack account", "hack into", "hacking", "ddos", "phishing",
    "malware", "ransomware", "keylogger", "steal password",
    # deception / crime
    "impersonate", "impersonation", "impersonating",
    "spamming", "spam emails", "spam messages", "spam people", "send spam",
    "email spam", "bulk email",
    "scam", "fraud", "tax evasion", "money laundering",
]


def safety_check(text: str) -> str | None:
    """Scan user text for misuse keywords.

    Returns REFUSAL_MSG when blocked, None when clean.
    Unconditional — there is NO bypass, not even for the admin.
    """
    t = " " + (text or "").lower() + " "
    for kw in MISUSE_KEYWORDS:
        if f" {kw} " in t:
            return REFUSAL_MSG
    return None


# ----------------------------------------------------------------------------
# 🔍 Spam Score Checker — keep listings natural, avoid FB spam flags.
# Score starts at 100; penalties lower it. Higher = more natural.
# ----------------------------------------------------------------------------
_SPAM_TRIGGER_PHRASES = [
    "FREE!!!", "ACT NOW", "CLICK HERE", "GUARANTEED", "NO RISK",
    "LIMITED TIME", "BUY NOW", "100% FREE", "RISK FREE", "MAKE MONEY FAST",
    "DOUBLE YOUR", "CASH BONUS",
]
_SPAM_LEGIT_CAPS = {"USA", "TX", "FL", "CA", "GA", "AZ", "HVAC", "AC"}
_EMOJI_RE = r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]"


def spam_score(title: str, desc: str) -> tuple:
    """Score a listing 0-100 (higher = more natural). Returns (score, issues)."""
    text = f"{title or ''}\n{desc or ''}"
    score = 100
    issues = []

    # ALL CAPS words (3+ letters), excluding legit abbreviations
    caps_words = re.findall(r"\b[A-Z]{3,}\b", text)
    caps_bad = sorted({w for w in caps_words if w not in _SPAM_LEGIT_CAPS})
    if caps_bad:
        penalty = min(30, 10 * len(caps_bad))
        score -= penalty
        shown = ", ".join(caps_bad[:5])
        issues.append(f"🔠 ALL-CAPS words ({len(caps_bad)}): {shown} (-{penalty})")

    # All-caps title
    if title and len(title.strip()) > 10 and title.strip() == title.strip().upper():
        # Make sure it's not just emojis/symbols
        if re.search(r"[A-Z]{3,}", title):
            score -= 20
            issues.append("🔠 Title is ALL CAPS (-20)")

    # Excessive emojis (>5)
    emoji_count = len(re.findall(_EMOJI_RE, text))
    if emoji_count > 5:
        penalty = 5 * (emoji_count - 5)
        score -= penalty
        issues.append(f"😀 Too many emojis ({emoji_count}; 5 max suggested) "
                      f"(-{penalty})")

    # Multiple exclamation marks
    if re.search(r"!{2,}", text):
        score -= 10
        issues.append("❗ Multiple exclamation marks (!!!) (-10)")

    # Spam trigger phrases
    upper_text = text.upper()
    for phrase in _SPAM_TRIGGER_PHRASES:
        if phrase in upper_text:
            score -= 15
            issues.append(f"🚨 Spam phrase: \"{phrase}\" (-15)")

    # Too many dollar signs (>2)
    dollar_count = text.count("$")
    if dollar_count > 2:
        penalty = 5 * (dollar_count - 2)
        score -= penalty
        issues.append(f"💲 Too many $ signs ({dollar_count}) (-{penalty})")

    return max(0, score), issues


def autofix_spam(title: str, desc: str) -> tuple:
    """Remove excessive caps/emojis/exclamations. Returns (title, desc)."""
    def _fix(t):
        t = t or ""
        # !!! → !
        t = re.sub(r"!{2,}", "!", t)
        # Keep max 5 emojis
        count = [0]

        def _repl(m):
            count[0] += 1
            return m.group(0) if count[0] <= 5 else ""

        t = re.sub(_EMOJI_RE, _repl, t)
        # ALL CAPS words → Capitalized (except legit abbreviations)
        def _capfix(m):
            w = m.group(0)
            return w if w in _SPAM_LEGIT_CAPS else w.capitalize()

        t = re.sub(r"\b[A-Z]{3,}\b", _capfix, t)
        return t

    return _fix(title), _fix(desc)


def show_spam_score(title: str, desc: str, key_prefix: str):
    """Render the spam-score widget with an auto-fix button.

    Works inside any listing display block. The fixed version is stored in
    session state so it survives reruns.
    """
    score, issues = spam_score(title, desc)
    if score >= 90:
        st.success(f"🔍 Spam Score: **{score}/100** — ✅ Excellent, natural!")
    elif score >= 70:
        st.warning(f"🔍 Spam Score: **{score}/100** — ⚠️ Good, minor tweaks "
                   f"suggested:")
        for issue in issues:
            st.caption(f"  • {issue}")
    else:
        st.error(f"🔍 Spam Score: **{score}/100** — ❌ Risky, rewrite suggested:")
        for issue in issues:
            st.caption(f"  • {issue}")

    if st.button("✨ Auto-fix spam issues", key=f"{key_prefix}_autofix"):
        new_title, new_desc = autofix_spam(title, desc)
        st.session_state[f"{key_prefix}_fixed_title"] = new_title
        st.session_state[f"{key_prefix}_fixed_desc"] = new_desc
        log_activity("system", f"spam auto-fix applied ({key_prefix})")

    fixed_t = st.session_state.get(f"{key_prefix}_fixed_title")
    fixed_d = st.session_state.get(f"{key_prefix}_fixed_desc")
    if fixed_t is not None:
        st.markdown("### ✨ Auto-fixed version")
        st.text_input("Fixed title (copy)", value=fixed_t,
                      key=f"{key_prefix}_ft")
        st.text_area("Fixed description (copy)", value=fixed_d, height=200,
                     key=f"{key_prefix}_fd")
        new_score, _ = spam_score(fixed_t, fixed_d)
        st.info(f"🔍 New spam score: **{new_score}/100**")


def llm_complete(api_key: str, provider: str, model: str,
                 messages: list, temperature: float = 0.7) -> str:
    """Single non-streaming completion via Groq or Gemini (free tiers)."""
    import requests
    # 🛡️ Safety: prepend the safety policy to the system message on EVERY
    # LLM call. No bypass exists — not even for the admin.
    safe_messages = []
    has_system = False
    for m in messages:
        m2 = dict(m)
        if m2.get("role") == "system":
            has_system = True
            m2["content"] = SAFETY_SYSTEM_PROMPT + "\n\n" + m2["content"]
        safe_messages.append(m2)
    if not has_system:
        # No system message in this call — insert the safety policy as one.
        safe_messages.insert(0, {"role": "system",
                                 "content": SAFETY_SYSTEM_PROMPT})
    messages = safe_messages
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
    "accounts": "🔑 Accounts",
    "templates": "📋 Templates",
    "rotation": "🔄 Smart Accounts",
    "all": "🌟 All modules",
}


# ----------------------------------------------------------------------------
# 📞 Service numbers (admin-managed) + 📋 Message templates (admin-managed)
# ----------------------------------------------------------------------------
DEFAULT_SERVICE_NUMBERS = {
    "Default": "+18312931196",
    "Plumbing": "+18312931196",
}

DEFAULT_MSG_TEMPLATES = {
    "👋 Greeting": (
        "Salam {name}! EasyFix ki taraf se khush amdeed. "
        "Kaise madad kar sakta hun?"
    ),
    "💰 Price Quote": (
        "Salam {name}! Ji haan, {service} ka kaam {price} flat hai — "
        "koi hidden charges nahi. Kab ana hai? 📞 {phone}"
    ),
    "🔧 Service Info": (
        "Salam {name}! EasyFix mein hum {service} karte hain — "
        "licensed, insured pros. Details: {website} "
        "ya call kar lein 📞 {phone}"
    ),
    "⏳ Follow-up": (
        "Salam {name}, EasyFix ki taraf se follow-up! Aap ne {service} "
        "ke bare mein poocha tha. Abhi bhi chahiye to bata dein 📞 {phone}"
    ),
    "✅ Closing": (
        "Shukriya {name}! Kaam pakka ho gaya. Koi aur masla ho to "
        "yaad karna — EasyFix hamesha hazir 🙌 {website}"
    ),
}


def _mask_email(email: str) -> str:
    """Mask an email for display: j***@gmail.com. Passwords are never stored."""
    e = (email or "").strip()
    if "@" not in e:
        return "***"
    local, domain = e.split("@", 1)
    return (local[:1] + "***@" + domain) if local else "***@" + domain


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
    if "service_numbers" not in st.session_state:
        st.session_state.service_numbers = dict(DEFAULT_SERVICE_NUMBERS)
    if "msg_templates" not in st.session_state:
        st.session_state.msg_templates = dict(DEFAULT_MSG_TEMPLATES)
    if "account_vault" not in st.session_state:
        # member name -> [{"platform": "Facebook", "email": "...", "note": "...",
        #                  "status": "Active", "last_used": None,
        #                  "uploads_today": 0, "uploads_date": "YYYY-MM-DD"}]
        # Passwords are NEVER stored — login always happens in the browser.
        st.session_state.account_vault = {}
    if "nord_logins" not in st.session_state:
        # Admin's own paid NordVPN logins, distributed to team members:
        # [{"label": "Nord-1", "username": "...", "password": "...",
        #   "server_city": "Dallas"}] — max 4. Device counts are computed
        # dynamically from team member assignments (10 max per login).
        st.session_state.nord_logins = []
    if "acct_settings" not in st.session_state:
        # Safe scheduling: min hours between uploads on one account,
        # max uploads per account per day.
        st.session_state.acct_settings = {"min_gap_hours": 2.0,
                                          "daily_limit": 3}
    if "last_suggested_acct" not in st.session_state:
        st.session_state.last_suggested_acct = None
    # Migrate any existing vault entries to smart-account fields (idempotent)
    for _accts in st.session_state.account_vault.values():
        for _e in _accts:
            _ensure_acct_fields(_e)


def _get_json(url: str, timeout: int = 8):
    """Fetch JSON from a URL (free APIs). Returns dict or None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EasyFixAgent/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


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
# 🔄 Smart Account Manager — helpers
# (Rotation + safe scheduling. NO automation, NO ban evasion — the human
# always uploads in their own browser.)
# ----------------------------------------------------------------------------
def _today_str() -> str:
    return time.strftime("%Y-%m-%d")


def _ensure_acct_fields(entry: dict):
    """Fill smart-account defaults on a vault entry (idempotent)."""
    entry.setdefault("status", "Active")  # Active / Resting / Flagged
    entry.setdefault("last_used", None)  # "YYYY-MM-DD HH:MM" or None
    entry.setdefault("uploads_today", 0)
    entry.setdefault("uploads_date", _today_str())


def _reset_daily_counts():
    """Zero per-day upload counters when the calendar day rolls over."""
    today = _today_str()
    for accts in st.session_state.account_vault.values():
        for e in accts:
            _ensure_acct_fields(e)
            if e.get("uploads_date") != today:
                e["uploads_date"] = today
                e["uploads_today"] = 0


def _all_accounts():
    """Return [(member, index, entry)] for every registered account."""
    _reset_daily_counts()
    out = []
    for member, accts in st.session_state.account_vault.items():
        for i, e in enumerate(accts):
            _ensure_acct_fields(e)
            out.append((member, i, e))
    return out


def _acct_key(member: str, entry: dict):
    return (member, entry.get("platform"), entry.get("email"))


def _rel_time(last_used):
    """Human-friendly 'x hours ago' for a last_used timestamp."""
    if not last_used:
        return "never used"
    try:
        lu_ts = time.mktime(time.strptime(last_used, "%Y-%m-%d %H:%M"))
    except Exception:
        return "unknown"
    mins = int((time.time() - lu_ts) / 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins}m ago"
    hrs = mins / 60
    if hrs < 24:
        return f"{hrs:.1f}h ago"
    return f"{hrs / 24:.1f}d ago"


def _suggest_account(platform: str):
    """Smart round-robin suggestion.

    Returns (member, idx, entry, note) or (None, None, None, reason).
    Skips: non-Active status, daily limit reached, inside rest gap,
    and (when 2+ candidates) the account suggested last time.
    """
    settings = st.session_state.acct_settings
    gap = float(settings.get("min_gap_hours", 2))
    limit = int(settings.get("daily_limit", 3))
    now = time.time()
    last_sug = st.session_state.get("last_suggested_acct")

    rows = []  # (rest_score, member, idx, entry, skip_reason)
    for member, i, e in _all_accounts():
        if e.get("platform") != platform:
            continue
        if e.get("status") != "Active":
            rows.append((0, member, i, e,
                         f"{member}: status is {e.get('status')}"))
            continue
        if int(e.get("uploads_today", 0)) >= limit:
            rows.append((0, member, i, e,
                         f"{member}: daily limit reached ({limit}/day)"))
            continue
        lu = e.get("last_used")
        if lu:
            try:
                lu_ts = time.mktime(time.strptime(lu, "%Y-%m-%d %H:%M"))
            except Exception:
                lu_ts = 0
            hours_ago = (now - lu_ts) / 3600
            if hours_ago < gap:
                rows.append((0, member, i, e,
                             f"{member}: resting "
                             f"({gap - hours_ago:.1f}h left of {gap}h gap)"))
                continue
            rest_score = hours_ago
        else:
            rest_score = 9999  # never used → highest priority
        rows.append((rest_score, member, i, e, None))

    eligible = [r for r in rows if r[4] is None]
    # Never suggest the same account twice in a row (when we have a choice)
    if len(eligible) > 1 and last_sug:
        filtered = [r for r in eligible
                    if _acct_key(r[1], r[3]) != last_sug]
        if filtered:
            eligible = filtered

    if not eligible:
        reasons = [r[4] for r in rows if r[4]]
        reason = "; ".join(reasons) if reasons else \
            f"No {platform} accounts registered yet — add one in 🔑 Account Vault."
        return None, None, None, reason

    eligible.sort(key=lambda r: r[0], reverse=True)  # longest-rested first
    _, member, i, e, _ = eligible[0]
    note = (f"rested {_rel_time(e.get('last_used'))} • "
            f"used {e.get('uploads_today', 0)}/{limit} today")
    return member, i, e, note


def _mark_uploaded(member: str, entry: dict, platform: str, who: str):
    """Record an upload against an account and rotate the suggestion."""
    entry["last_used"] = time.strftime("%Y-%m-%d %H:%M")
    entry["uploads_today"] = int(entry.get("uploads_today", 0)) + 1
    st.session_state.last_suggested_acct = _acct_key(member, entry)
    log_activity(who, f"uploaded via {platform} "
                      f"({_mask_email(entry.get('email'))})")


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
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #141238 35%, #1e1045 60%, #0d1030 100%);
        background-attachment: fixed;
    }
    .stApp::before {
        content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
        background:
            radial-gradient(600px 300px at 15% 0%, rgba(99,102,241,0.14), transparent 70%),
            radial-gradient(700px 350px at 90% 20%, rgba(168,85,247,0.12), transparent 70%),
            radial-gradient(500px 300px at 50% 100%, rgba(59,130,246,0.10), transparent 70%);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1233 0%, #17124a 100%);
        border-right: 1px solid rgba(139,92,246,0.35);
        box-shadow: 4px 0 28px rgba(99,102,241,0.15);
    }
    .stApp, .stApp p, .stApp div, .stApp span, .stApp label { color: #e4e4e7 !important; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
        color: #ffffff !important; font-weight: 700 !important;
        text-shadow: 0 0 18px rgba(139,92,246,0.28);
    }
    .stMarkdown p { color: #e4e4e7 !important; font-weight: 500; }
    .stCaption { color: #a1a1aa !important; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label {
        color: #e4e4e7 !important; font-weight: 500;
    }
    .hero {
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 45%, #f472b6 90%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
        font-size: 3.4rem; font-weight: 900; letter-spacing: -0.02em; margin-bottom: 0;
        filter: drop-shadow(0 0 24px rgba(139,92,246,0.45));
    }
    .hero-underline {
        height: 3px; width: 240px; margin: 0.5rem 0 0.9rem 0; border-radius: 3px;
        background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6);
        box-shadow: 0 0 16px rgba(139,92,246,0.65);
    }
    .owner-badge {
        display: inline-block; background: linear-gradient(135deg, #4c1d95, #7c3aed);
        color: white; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.1em;
        padding: 0.35rem 1rem; border-radius: 20px; margin-bottom: 0.8rem;
        box-shadow: 0 4px 18px rgba(124,58,237,0.55);
        border: 1px solid rgba(196,181,253,0.45);
    }
    .free-badge {
        display: inline-block; background: linear-gradient(135deg, #a78bfa, #f0abfc);
        color: #2e1065; font-size: 0.8rem; font-weight: 900; letter-spacing: 0.1em;
        padding: 0.35rem 1rem; border-radius: 20px; margin-bottom: 0.8rem;
        margin-left: 0.5rem;
        box-shadow: 0 4px 18px rgba(167,139,250,0.55);
    }
    .sub { color: #a1a1aa; margin-top: 0.3rem; margin-bottom: 1.2rem; font-size: 1.05rem; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #a855f7); border: none;
        font-weight: 700; border-radius: 12px; padding: 0.6rem 1.5rem;
        box-shadow: 0 4px 22px rgba(139,92,246,0.5);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 30px rgba(139,92,246,0.75);
        transform: translateY(-1px);
    }
    .stButton > button:not([kind="primary"]) {
        border-radius: 10px; border: 1px solid rgba(139,92,246,0.45);
        background: rgba(99,102,241,0.08);
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: rgba(167,139,250,0.8);
        background: rgba(99,102,241,0.16);
    }
    .tip {
        background: linear-gradient(135deg, rgba(99,102,241,0.16), rgba(168,85,247,0.08));
        border: 1px solid rgba(139,92,246,0.4); border-radius: 14px;
        padding: 0.9rem 1.2rem; margin: 0.8rem 0;
        box-shadow: 0 4px 18px rgba(99,102,241,0.18);
    }
    .side-logo {
        font-size: 1.6rem; font-weight: 900; margin-bottom: 0.2rem;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 60%, #f472b6 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
        filter: drop-shadow(0 0 10px rgba(139,92,246,0.4));
    }
    .tool-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.13), rgba(168,85,247,0.06));
        border: 1px solid rgba(139,92,246,0.35); border-radius: 16px;
        padding: 1rem 1.2rem; margin: 0.6rem 0;
        box-shadow: 0 6px 26px rgba(76,29,149,0.28);
    }
    .footer { text-align: center; color: #a5a5b8; font-size: 0.85rem;
              margin-top: 0.5rem; padding-top: 1rem; border-top: 1px solid rgba(139,92,246,0.3); }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border-radius: 10px; border: 1px solid #52525b;
        background-color: #151528 !important; color: #ffffff !important;
        font-weight: 600 !important; font-size: 15px !important;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 2px rgba(139,92,246,0.35) !important;
    }
    .stExpander { border-radius: 12px; border: 1px solid rgba(139,92,246,0.3); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0; padding: 0.5rem 1.2rem;
        color: #b8b8d0 !important; font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(168,85,247,0.15)) !important;
        color: #ffffff !important;
        border-bottom: 2px solid #a78bfa !important;
    }
    section[data-testid="stSidebar"] .stRadio > div { gap: 6px; }
    section[data-testid="stSidebar"] .stRadio label {
        border-radius: 10px; padding: 0.35rem 0.7rem;
        border: 1px solid transparent;
    }
    section[data-testid="stSidebar"] .stRadio label:has(input:checked) {
        background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(168,85,247,0.2));
        border: 1px solid rgba(139,92,246,0.5);
        box-shadow: 0 2px 12px rgba(139,92,246,0.3);
    }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    .stDeployButton { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

_init_state()

st.markdown('<p class="hero">🔧 EasyFix Agent</p><div class="hero-underline"></div>', unsafe_allow_html=True)
st.markdown('<span class="owner-badge">👑 Built for Muhammad Mudassir Yaseen</span>'
            '<span class="free-badge">💯 100% FREE — no paid credits, ever</span>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="sub">Your team\'s AI command center — videos, listings, replies, '
    'voiceovers. Everything free: free AI keys (signup only, no payment), '
    'free voiceovers, free stock video. '
    '<a href="https://www.easytofix.homes" '
    'style="color:#a78bfa;">easytofix.homes</a></p>',
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
if can_access("accounts"):
    PAGES.append("🔑 Account Vault")
if can_access("rotation"):
    PAGES.append("🔄 Smart Account Manager")
if can_access("templates"):
    PAGES.append("📋 Message Templates")
PAGES += ["🛡️ Safety Toolkit", "🧠 Knowledge Base", "🔗 Tools Hub", "📋 Surveys"]

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
        '<a href="https://www.easytofix.homes" style="color:#a78bfa;">'
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

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["👥 Team Members", "🔑 API Key", "📊 Activity Log",
         "📋 Templates", "📞 Numbers", "⚙️ Settings"])

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
        st.markdown("#### 🔒 NordVPN login for this member (optional)")
        st.caption("Give them a NordVPN login so their IP shows as USA. "
                   "Manage logins in 🛡️ Safety Toolkit → 🔒 NordVPN Setup.")
        nc1, nc2 = st.columns(2)
        _nord_opts = (["None"] +
                      [l["label"] for l in st.session_state.nord_logins])
        with nc1:
            m_nord = st.selectbox("NordVPN login", _nord_opts, key="m_nord",
                                  help="Which NordVPN login this member uses")
        with nc2:
            m_nord_city = st.text_input("USA server city", key="m_nord_city",
                                        value="Dallas",
                                        placeholder="e.g. Dallas")
        if st.button("➕ Create member", type="primary"):
            if not m_name.strip():
                st.error("Enter a name")
            elif not m_roles:
                st.error("Pick at least one module")
            else:
                code = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))
                _member = {"name": m_name.strip(), "roles": m_roles}
                if m_nord != "None":
                    _member["nord"] = {
                        "login": m_nord,
                        "server_city": (m_nord_city or "Dallas").strip()}
                    log_activity(
                        "Admin",
                        f"assigned NordVPN login {m_nord} to {m_name.strip()}")
                st.session_state.team[code] = _member
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
                    _mn = m.get("nord")
                    if _mn:
                        st.caption(f"🔒 NordVPN: **{_mn['login']}** "
                                   f"({_mn.get('server_city', 'Dallas')}, USA)")
                    else:
                        st.caption("🔒 No NordVPN assigned")
                    accts = st.session_state.account_vault.get(m["name"], [])
                    if accts:
                        st.caption("🔑 " + ", ".join(
                            f"{a['platform']} ({_mask_email(a['email'])})"
                            for a in accts))
                    else:
                        st.caption("🔑 No accounts registered")
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
        st.markdown("### 📋 Message Templates")
        st.caption("Templates the team uses for customer messages. "
                   "Variables: {name} {service} {price} {phone} {website}")
        t_name = st.text_input("Template name", key="tpl_name",
                               placeholder="e.g. 🚚 Dispatch Update")
        t_body = st.text_area("Template text", key="tpl_body", height=100,
                              placeholder="Salam {name}! ... 📞 {phone}")
        if st.button("➕ Save template", type="primary"):
            if not t_name.strip() or not t_body.strip():
                st.error("Name and text both required")
            else:
                st.session_state.msg_templates[t_name.strip()] = t_body.strip()
                log_activity("Admin", f"saved template '{t_name.strip()}'")
                st.success(f"✅ Template '{t_name.strip()}' saved")
                st.rerun()
        st.divider()
        for name, body in list(st.session_state.msg_templates.items()):
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{name}**")
                    st.caption(body)
                with c2:
                    if st.button("🗑️", key=f"tpldel_{name}"):
                        del st.session_state.msg_templates[name]
                        log_activity("Admin", f"deleted template '{name}'")
                        st.rerun()

    with tab5:
        st.markdown("### 📞 Service Numbers")
        st.caption("Numbers auto-inserted into templates and AI replies.")
        for svc in list(st.session_state.service_numbers.keys()):
            c1, c2, c3 = st.columns([2, 3, 1])
            with c1:
                st.markdown(f"**{svc}**")
            with c2:
                new_num = st.text_input("Number", key=f"num_{svc}",
                                        value=st.session_state.service_numbers[svc])
            with c3:
                st.write("")
                if st.button("💾", key=f"numsv_{svc}"):
                    st.session_state.service_numbers[svc] = new_num.strip()
                    log_activity("Admin", f"updated number for {svc}")
                    st.success("✅ Saved")
                if svc != "Default" and st.button("🗑️", key=f"numdel_{svc}"):
                    del st.session_state.service_numbers[svc]
                    log_activity("Admin", f"removed number for {svc}")
                    st.rerun()
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            ns = st.text_input("New service", key="num_new_svc",
                               placeholder="e.g. Electrical")
        with c2:
            nn = st.text_input("New number", key="num_new_num",
                               placeholder="+1…")
        if st.button("➕ Add number", type="primary"):
            if ns.strip() and nn.strip():
                st.session_state.service_numbers[ns.strip()] = nn.strip()
                log_activity("Admin", f"added number for {ns.strip()}")
                st.success("✅ Added")
                st.rerun()

    with tab6:
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
        blocked = safety_check(prompt) or safety_check(voice_script)
        if not prompt.strip():
            st.error("Write a prompt first")
        elif mode == "🖼️ Image to Video" and not image_path:
            st.error("Upload an image first")
        elif blocked:
            # 🛡️ Misuse blocked — no video generated, no quota spent.
            log_activity(user["name"],
                         "blocked: misuse keywords in video prompt")
            st.warning(blocked)
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

    # ------------------------------------------------------------------
    # 📤 Upload Metadata — USA-targeted, copy-paste ready for
    # YouTube / Rumble / Instagram / Dailymotion.
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("📤 Upload Metadata — USA Targeted 🇺🇸")
    st.caption("Copy-paste ready for YouTube, Rumble, Instagram & Dailymotion. "
               "Everything defaults to USA targeting.")

    mc1, mc2 = st.columns(2)
    with mc1:
        meta_city = st.selectbox("📍 Target city (USA)", USA_CITIES_WITH_CUSTOM,
                                 key="meta_city",
                                 help="Used in the title and as the video "
                                      "location suggestion.")
        if meta_city == "✏️ Custom…":
            meta_city_val = st.text_input("Custom city", key="meta_city_custom",
                                          placeholder="e.g. Austin, TX")
        else:
            meta_city_val = meta_city
    with mc2:
        meta_topic = st.text_input("Video topic", key="meta_topic",
                                   placeholder="e.g. Leaky Faucet Fix")

    if st.button("✨ Generate Upload Metadata", type="secondary",
                 use_container_width=True):
        if not meta_city_val.strip():
            st.error("Pick a target city")
        elif not meta_topic.strip():
            st.error("Enter the video topic")
        else:
            blocked = safety_check(meta_topic)
            if blocked:
                log_activity(user["name"],
                             "blocked: misuse keywords in upload metadata")
                st.warning(blocked)
            else:
                log_activity(user["name"],
                             f"generated upload metadata: {meta_topic} "
                             f"→ {meta_city_val}")
                meta_title = f"{meta_topic} in {meta_city_val} — $110"
                meta_desc = (
                    f"🔧 {meta_topic} in {meta_city_val}, USA! 🇺🇸\n\n"
                    f"Watch how our pros handle it — funny AND educational!\n\n"
                    f"💰 $110 flat — no hidden charges\n"
                    f"📞 Call/Text: {PHONE}\n"
                    f"🌐 {SITE_URL}\n\n"
                    f"👍 Like & follow USA Trade Confessions for daily "
                    f"home tips!"
                )
                meta_tags = ("plumber, plumbing, hometips, USA, funny, "
                             "diy, home repair, shorts, "
                             f"{meta_city_val.replace(', ', ' ').replace(',', '')}, "
                             "usatradeconfessions")
                st.text_input("📺 Title (copy)", value=meta_title,
                              key="meta_title")
                st.text_area("📝 Description (copy)", value=meta_desc,
                             height=220, key="meta_desc")
                st.text_input("🏷️ Tags (copy)", value=meta_tags,
                              key="meta_tags")
                st.info(
                    "📍 **Location tip:** Set the video location to "
                    f"**{meta_city_val}, USA** in YouTube Studio during "
                    "upload for better local reach. 🇺🇸"
                )


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
        blocked = safety_check(script)
        if not script.strip():
            st.error("Write a script first")
        elif blocked:
            # 🛡️ Misuse blocked — nothing generated.
            log_activity(user["name"], "blocked: misuse keywords in voiceover")
            st.warning(blocked)
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
        # 📍 USA location preset — defaults to USA targeting.
        city_choice = st.selectbox("📍 City (USA)", USA_CITIES_WITH_CUSTOM,
                                   help="Every listing is USA-targeted by default.")
        if city_choice == "✏️ Custom…":
            city = st.text_input("Custom city", placeholder="e.g. Austin, TX")
        else:
            city = city_choice
            st.caption(f"🎯 Targeting: {city}, USA")
        price = st.text_input("Price", value="$110")
    with c2:
        condition = st.selectbox("Condition", ["New service", "Repair", "Install"])
        extra = st.text_area("Extra details (optional)", height=80,
                             placeholder="Same-day service, warranty info…")

    if st.button("✨ Generate Listing", type="primary", use_container_width=True):
        blocked = safety_check(extra)
        if not city.strip():
            st.error("Enter a city")
        elif blocked:
            # 🛡️ Misuse blocked — no listing generated.
            log_activity(user["name"],
                         "blocked: misuse keywords in listing details")
            st.warning(blocked)
        else:
            log_activity(user["name"],
                         f"generated listing: {service} in {city}")
            # 🔀 Save base details so the Variation Engine can build on them.
            st.session_state.lst_base = {
                "service": service, "city": city, "price": price,
                "condition": condition, "extra": extra,
            }
            title = f"{service} in {city} — {price}"
            desc = (
                f"🔧 {service} in {city}, USA! 🇺🇸\n\n"
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
                f"USA Trade Confessions — trusted home services across the USA!"
            )
            # Store generated text in session state so the display block below
            # (and the spam auto-fix) survives reruns.
            st.session_state.lst_gen_title = title
            st.session_state.lst_gen_desc = desc
            for _k in ("lst_title", "lst_desc",
                       "lst_fixed_title", "lst_fixed_desc"):
                st.session_state.pop(_k, None)

    # Display the generated listing from session state (outside the button
    # block so the spam auto-fix button works across reruns).
    if st.session_state.get("lst_gen_title"):
        _gen_title = st.session_state.lst_gen_title
        _gen_desc = st.session_state.lst_gen_desc
        st.markdown("### 📋 Your listing")
        st.text_input("Title (copy)", value=_gen_title, key="lst_title")
        st.text_area("Description (copy)", value=_gen_desc, height=260,
                     key="lst_desc")
        # Spam score on the current widget values (user may have edited).
        show_spam_score(
            st.session_state.get("lst_title", _gen_title),
            st.session_state.get("lst_desc", _gen_desc),
            "lst")
        st.success("✅ Copy the title + description and post on "
                   "Facebook Marketplace manually.")
        st.caption("⚠️ Always post manually — automated posting gets "
                   "blocked by Facebook.")

    # ------------------------------------------------------------------
    # 🔀 Listing Variation Engine — unique versions per team member so
    # Facebook never sees duplicate text (duplicates = spam = ban).
    # ------------------------------------------------------------------
    if st.session_state.get("lst_base"):
        st.markdown("---")
        st.subheader("🔀 Listing Variation Engine")
        st.caption("One team = one text each. Generate 5 unique versions — "
                   "no two members should post the same wording.")
        base = st.session_state.lst_base

        def _parse_variations(text):
            import re
            chunks = re.split(r"(?im)^VARIATION\s+\d+\s*$", text)
            out = []
            for ch in chunks:
                ch = ch.strip()
                if not ch:
                    continue
                mt = re.search(r"(?im)^TITLE:\s*(.+)$", ch)
                title = mt.group(1).strip() if mt else ""
                md = re.search(r"(?im)^DESC:\s*\n?(.*)$", ch, re.DOTALL)
                desc = md.group(1).strip() if md else ""
                desc = re.sub(r"\n?^---+\s*$", "", desc, flags=re.M).strip()
                if title or desc:
                    out.append({"title": title, "desc": desc})
            return out[:5]

        def _build_template_variations(b):
            svc, cty, prc = b["service"], b["city"], b["price"]
            cond, xtra = b["condition"], b["extra"].strip()
            xb = f"✅ {xtra}\n" if xtra else ""
            xp = f"{xtra} " if xtra else ""
            xe = f"🌟 {xtra} 🌟\n" if xtra else ""
            xs = f"{xtra} " if xtra else ""
            xd = f"- {xtra}\n" if xtra else ""
            return [
                {"title": f"Professional {svc} in {cty} — {prc} Flat Rate",
                 "desc": (
                     f"🔧 Looking for reliable {svc} in {cty}? We've got you "
                     f"covered! 🇺🇸\n\n"
                     f"✔️ {cond}\n"
                     f"✔️ {prc} flat — no hidden charges\n"
                     f"✔️ Licensed & insured professionals\n"
                     f"✔️ Same-day service available\n"
                     f"{xb}"
                     f"\n📞 Call or Text: {PHONE}\n"
                     f"🌐 {SITE_URL}\n\n"
                     f"USA Trade Confessions — trusted home services across "
                     f"the USA!"
                 )},
                {"title": f"{svc} — {cty} — {prc}",
                 "desc": (
                     f"Hi! We offer {svc} in {cty} for a {prc} flat rate. "
                     f"{cond} work done by licensed and insured pros, and "
                     f"same-day service is usually available. No hidden charges "
                     f"— what you see is what you pay. {xp}Call or text us at "
                     f"{PHONE}, or visit {SITE_URL} for more info. USA Trade "
                     f"Confessions, serving homes across the USA."
                 )},
                {"title": f"🔧 {svc} {cty} 🇺🇸 {prc}",
                 "desc": (
                     f"🚨 Need {svc} in {cty}?! 🚨\n"
                     f"💰 ONLY {prc} FLAT!! 💰\n"
                     f"✅✅ Licensed Pros ✅✅\n"
                     f"⚡ Same-Day Service ⚡\n"
                     f"🛠️ {cond} 🛠️\n"
                     f"{xe}"
                     f"📲📲 {PHONE} 📲📲\n"
                     f"🌐🌐 {SITE_URL} 🌐🌐\n"
                     f"⭐ USA Trade Confessions ⭐"
                 )},
                {"title": f"{cty} {svc} – {prc} Flat",
                 "desc": (
                     f"{svc} — {cty}. {prc} flat. {cond}. Licensed & insured. "
                     f"Same-day available. {xs}{PHONE} | {SITE_URL}"
                 )},
                {"title": f"Affordable {svc} Service in {cty}, USA — {prc}",
                 "desc": (
                     f"USA Trade Confessions — Home Services ({cty}, USA) 🇺🇸\n\n"
                     f"Service: {svc}\n"
                     f"Type: {cond}\n"
                     f"Price: {prc} flat rate (no hidden fees)\n"
                     f"Coverage: {cty} and nearby areas\n\n"
                     f"Why choose us:\n"
                     f"- Licensed & insured professionals\n"
                     f"- Same-day service available\n"
                     f"- Upfront {prc} pricing\n"
                     f"{xd}"
                     f"\n📞 {PHONE}\n"
                     f"🌐 {SITE_URL}"
                 )},
            ]

        if st.button("🔀 Generate 5 Unique Variations", type="secondary",
                      use_container_width=True):
            blocked = safety_check(base.get("extra", ""))
            if blocked:
                log_activity(user["name"],
                             "blocked: misuse keywords in variation input")
                st.warning(blocked)
            else:
                variations = []
                if st.session_state.llm_key:
                    with st.spinner("🔀 Writing 5 unique versions…"):
                        try:
                            sys_msg = (
                                "You are writing 5 UNIQUE Facebook Marketplace "
                                "listing variations for a US home-services business "
                                "(EasyFix, https://www.easytofix.homes, owner "
                                "Muhammad Mudassir Yaseen). Make all 5 genuinely "
                                "different: vary title phrasing, description structure "
                                "(one paragraph-style, one bullet-style, one casual, "
                                "one professional, one emoji-heavy), opening line, "
                                "call-to-action, and emoji density (at least one with "
                                "ZERO emojis). Every variation MUST include: the service "
                                "name, the city, the price, the phone number, and "
                                "https://www.easytofix.homes. Keep each description "
                                "under 120 words, titles under 60 characters. "
                                "Plain text only — no markdown bold or italics."
                            )
                            user_msg = (
                                f"Service: {base['service']}. "
                                f"City: {base['city']}, USA. "
                                f"Price: {base['price']} flat. "
                                f"Type: {base['condition']}. "
                                f"Phone: {PHONE}. "
                                f"Extra details: {base['extra'].strip() or 'none'}.\n\n"
                                "FORMAT (follow exactly):\n"
                                "VARIATION 1\nTITLE: <title>\nDESC:\n<description>\n---\n"
                                "VARIATION 2\nTITLE: <title>\nDESC:\n<description>\n---\n"
                                "... through VARIATION 5."
                            )
                            out = llm_complete(
                                st.session_state.llm_key,
                                st.session_state.llm_provider,
                                st.session_state.llm_model,
                                [{"role": "system", "content": sys_msg},
                                 {"role": "user", "content": user_msg}],
                                temperature=0.9)
                            variations = _parse_variations(out)
                            if not variations:
                                st.warning("⚠️ Couldn't parse the AI output — "
                                           "using built-in styles instead.")
                                variations = _build_template_variations(base)
                        except Exception as e:
                            st.error(f"AI variation failed ({e}) — using "
                                     f"built-in styles.")
                            variations = _build_template_variations(base)
                else:
                    st.caption("💡 Tip: ask the admin to add the free AI key for "
                               "AI-written variations — using built-in styles "
                               "for now.")
                    variations = _build_template_variations(base)
                if variations:
                    st.session_state.var_gen = \
                        st.session_state.get("var_gen", 0) + 1
                    st.session_state.lst_variations = variations
                    log_activity(user["name"],
                                 f"generated {len(variations)} listing variations: "
                                 f"{base['service']} in {base['city']}")

        vars_ = st.session_state.get("lst_variations") or []
        if vars_:
            g = st.session_state.get("var_gen", 0)
            st.markdown("### 👥 Assign variations to team")
            team_names = [m.get("name", code)
                          for code, m in
                          st.session_state.get("team", {}).items()]
            for i, v in enumerate(vars_):
                with st.expander(f"📌 Variation {i+1}: {v['title'][:55]}",
                                 expanded=(i == 0)):
                    st.text_input("Title (copy)", value=v["title"],
                                  key=f"v{g}_title_{i}")
                    st.text_area("Description (copy)", value=v["desc"],
                                 height=210, key=f"v{g}_desc_{i}")
                    # 🔍 Spam score per variation (on current widget values).
                    show_spam_score(
                        st.session_state.get(f"v{g}_title_{i}", v["title"]),
                        st.session_state.get(f"v{g}_desc_{i}", v["desc"]),
                        f"v{g}var{i}")
                    st.selectbox("👤 Assign to team member",
                                 ["— Unassigned —"] + team_names,
                                 key=f"v{g}_assign_{i}")
            taken = [st.session_state.get(f"v{g}_assign_{i}",
                                          "— Unassigned —")
                     for i in range(len(vars_))]
            dupes = {t for t in taken
                     if t != "— Unassigned —" and taken.count(t) > 1}
            if dupes:
                st.warning("⚠️ Same member assigned twice: "
                           + ", ".join(sorted(dupes))
                           + " — each member should use a DIFFERENT variation!")
            with st.expander("🛡️ Anti-duplicate tips (avoid FB spam flags)"):
                st.markdown(
                    "- 👤 **One variation per person** — never let two members "
                    "post the same text.\n"
                    "- ✏️ Change 1–2 words in your own words before posting.\n"
                    "- 📸 Use **different photos** for each listing.\n"
                    "- ⏰ Post at **different times** — not all at once.\n"
                    "- 📍 Vary the map pin slightly inside the city.\n"
                    "- 🚫 Never copy-paste the exact same title twice."
                )

    # ------------------------------------------------------------------
    # 🌐 Multi-Platform Listing Support — Facebook Marketplace, Locanto,
    # Craigslist, Yelp, Nextdoor. One base listing → formatted per platform.
    # ------------------------------------------------------------------
    if st.session_state.get("lst_base"):
        st.markdown("---")
        st.subheader("🌐 Multi-Platform Versions")
        st.caption("Same service, formatted for each platform's style and "
                   "rules. Pick platforms → generate → copy & post manually.")
        mp_base = st.session_state.lst_base

        PLATFORMS = {
            "fb": "📘 Facebook Marketplace",
            "locanto": "📋 Locanto",
            "craigslist": "📌 Craigslist",
            "yelp": "⭐ Yelp",
            "nextdoor": "🏘️ Nextdoor",
        }

        mp_sel = st.multiselect(
            "Select platforms",
            list(PLATFORMS.values()),
            default=["📘 Facebook Marketplace"],
            key="mp_sel")
        mp_keys = [k for k, v in PLATFORMS.items() if v in mp_sel]

        def _build_platform_versions(b):
            svc, cty, prc = b["service"], b["city"], b["price"]
            cond, xtra = b["condition"], b["extra"].strip()
            fb_xtra = f"✅ {xtra}\n" if xtra else ""
            plain_xtra = f"- {xtra}\n" if xtra else ""
            nd_xtra = f"{xtra} " if xtra else ""
            versions = {}
            # --- 📘 Facebook Marketplace: short title, price upfront, emojis OK
            versions["fb"] = (
                f"{svc} in {cty} — {prc}",
                f"🔧 {svc} in {cty}, USA! 🇺🇸\n\n"
                f"✅ Professional service — {prc} flat\n"
                f"✅ {cond}\n"
                f"✅ Licensed & insured pros\n"
                f"✅ Same-day service available\n"
                f"{fb_xtra}"
                f"\n📞 Call/Text: {PHONE}\n"
                f"🌐 {SITE_URL}\n\n"
                f"USA Trade Confessions — trusted home services across the USA!"
            )
            # --- 📋 Locanto: detailed, category hint, JPG/PNG note
            versions["locanto"] = (
                f"{svc} in {cty} | Professional Home Services — {prc}",
                f"{svc} in {cty}, USA\n\n"
                f"We provide professional {svc.lower()} services in {cty} "
                f"and surrounding areas. {cond} work by licensed and insured "
                f"technicians. Upfront {prc} flat rate — no hidden charges.\n\n"
                f"Services include:\n"
                f"- {svc} ({cond.lower()})\n"
                f"- Same-day appointments available\n"
                f"- Satisfaction guaranteed\n"
                f"{plain_xtra}"
                f"\nCategory: Home Services\n"
                f"Contact: {PHONE}\n"
                f"Website: {SITE_URL}\n\n"
                f"Note: please attach JPG or PNG photos (Locanto does not "
                f"accept WebP images). Your phone number goes in the "
                f"dedicated phone field."
            )
            # --- 📌 Craigslist: plain text only, no emojis, no ALL CAPS
            versions["craigslist"] = (
                f"{svc} - {cty} ({prc} flat)",
                f"{svc} in {cty}\n\n"
                f"Professional {svc.lower()} service. {cond} work done by "
                f"licensed and insured pros. {prc} flat rate, no hidden fees. "
                f"Same-day service usually available.\n\n"
                f"- Upfront pricing\n"
                f"- Licensed and insured\n"
                f"- Same-day appointments\n"
                f"{plain_xtra}"
                f"\nCall or text: {PHONE}\n"
                f"{SITE_URL}\n\n"
                f"Serving {cty} and nearby areas."
            )
            # --- ⭐ Yelp: business-style, professional, no price in title
            versions["yelp"] = (
                f"EasyFix Home Services — {svc} in {cty}",
                f"EasyFix Home Services proudly serves {cty} with top-rated "
                f"{svc.lower()}.\n\n"
                f"About us:\n"
                f"We are a team of licensed and insured home-service "
                f"professionals offering {cond.lower()} work with upfront "
                f"flat-rate pricing and same-day availability.\n\n"
                f"Our services:\n"
                f"- {svc}\n"
                f"- Emergency repairs\n"
                f"- Installations and maintenance\n"
                f"{plain_xtra}"
                f"\nCall {PHONE} or visit {SITE_URL} to book.\n"
                f"USA Trade Confessions — trusted home services across the USA."
            )
            # --- 🏘️ Nextdoor: neighbor tone, local focus
            versions["nextdoor"] = (
                f"Hi neighbors! {svc} in {cty} — {prc} flat",
                f"Hi neighbors!\n\n"
                f"I'm with EasyFix Home Services, and we help folks right here "
                f"in {cty} with {svc.lower()}. {cond} work, {prc} flat rate — "
                f"no surprises, no hidden fees.\n\n"
                f"Licensed and insured, and we can usually come out same-day. "
                f"{nd_xtra}Happy to answer any questions!\n\n"
                f"Call/text: {PHONE}\n"
                f"{SITE_URL}"
            )
            return versions

        if st.button("🌐 Generate Platform Versions", type="primary",
                     use_container_width=True, key="mp_gen_btn"):
            blocked = safety_check(mp_base.get("extra", ""))
            if blocked:
                log_activity(user["name"],
                             "blocked: misuse keywords in platform input")
                st.warning(blocked)
            elif not mp_keys:
                st.error("Select at least one platform first.")
            else:
                all_v = _build_platform_versions(mp_base)
                picked = {k: all_v[k] for k in mp_keys}
                st.session_state.mp_gen = st.session_state.get("mp_gen", 0) + 1
                st.session_state.mp_versions = picked
                log_activity(
                    user["name"],
                    f"generated multi-platform listing "
                    f"({', '.join(mp_keys)}): "
                    f"{mp_base['service']} in {mp_base['city']}")

        mpv = st.session_state.get("mp_versions") or {}
        if mpv:
            g = st.session_state.get("mp_gen", 0)
            mp_tabs = st.tabs([PLATFORMS[k] for k in mpv.keys()])
            for tab, (k, (t, d)) in zip(mp_tabs, mpv.items()):
                with tab:
                    st.text_input("Title (copy)", value=t,
                                  key=f"mp{g}_{k}_t")
                    st.text_area("Description (copy)", value=d, height=260,
                                 key=f"mp{g}_{k}_d")
                    # 🔍 Spam score per platform version.
                    show_spam_score(
                        st.session_state.get(f"mp{g}_{k}_t", t),
                        st.session_state.get(f"mp{g}_{k}_d", d),
                        f"mp{g}{k}")
                    st.caption(f"📌 Post manually on {PLATFORMS[k]} — "
                               f"never auto-post.")

        with st.expander("📏 Platform tips (limits & best practices)"):
            st.markdown(
                "- **📘 Facebook Marketplace** — keep titles under ~100 "
                "characters; put the price in the dedicated price field AND "
                "the title; emojis are fine; bright clear photos get more "
                "clicks; always post manually.\n"
                "- **📋 Locanto** — category: Home Services; images must be "
                "JPG/PNG (WebP is rejected); phone goes in the dedicated "
                "phone field (it gets masked); longer descriptions are OK.\n"
                "- **📌 Craigslist** — plain text only: no emojis, no ALL "
                "CAPS; one ad per category; never repost identical ads "
                "(they get flagged); keep the city in the title.\n"
                "- **⭐ Yelp** — this is a business listing, not a "
                "classified: professional tone, services list, no price in "
                "the title, no keyword stuffing.\n"
                "- **🏘️ Nextdoor** — real-name community: neighbor-friendly "
                "tone, local focus, no spammy commercial language or "
                "neighbors will report it."
            )

    # --- 🎬 Listing Video Clip: 4–5 sec FB-ready clips ---
    st.markdown("---")
    st.subheader("🎬 Listing Video Clip")
    st.caption("FB Marketplace listings allow video uploads. A short clip "
               "makes your listing look real — more views, more buyer trust, "
               "fewer reports.")
    with st.expander("💡 Why video helps (seedhi baat)"):
        st.markdown(
            "- 🎥 **Video wali listings ko zyada views milte hain** — buyers "
            "stop and watch.\n"
            "- ✅ **Real lagti hain** — buyer trust karta hai, report kam "
            "karta hai.\n"
            "- 📉 **Kam reports = kam ban risk** — legit look matters.\n"
            "- ⚠️ **Honest note:** video *helps* quality but is NOT a magic "
            "shield. Combine with VPN + unique variations + smart timing "
            "for real safety."
        )

    def _trim_clip(video_bytes: bytes, seconds: int = 5) -> bytes:
        """Trim to first N seconds, re-encode H.264+AAC faststart (FB-ready)."""
        import subprocess
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        tmpdir = tempfile.mkdtemp()
        vp = f"{tmpdir}/in.mp4"
        out = f"{tmpdir}/clip.mp4"
        with open(vp, "wb") as f:
            f.write(video_bytes)
        subprocess.run(
            [exe, "-y", "-v", "error", "-i", vp,
             "-t", str(seconds),
             "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-preset", "fast", "-c:a", "aac",
             "-movflags", "+faststart", out],
            check=True, timeout=180)
        with open(out, "rb") as f:
            return f.read()

    clip_presets = {
        "🚿 Drain Cleaning": "drain cleaning plumber",
        "🔧 Plumbing Repair": "plumber fixing sink",
        "🔨 Handyman": "handyman tools repair",
        "🚪 Garage Door": "garage door repair",
        "❄️ HVAC": "air conditioner technician",
        "⚡ Electrical": "electrician wiring",
        "🏠 Roofing": "roof repair worker",
        "🎨 Painting": "house painter painting wall",
    }
    cp_cols = st.columns(4)
    for i, (label, q) in enumerate(clip_presets.items()):
        if cp_cols[i % 4].button(label, use_container_width=True,
                                 key=f"clipp_{i}"):
            st.session_state["clip_query"] = q
    clip_query = st.text_input(
        "Service for the clip",
        value=st.session_state.get("clip_query", "plumber"),
        key="clip_search_box")
    if st.button("🔍 Find Clips", type="primary", key="clip_search_btn",
                 use_container_width=True) and clip_query:
        blocked = safety_check(clip_query)
        if blocked:
            log_activity(user["name"],
                         "blocked: misuse keywords in clip search")
            st.warning(blocked)
        elif not PIXABAY_API_KEY:
            st.error("No Pixabay key configured — ask the admin.")
        else:
            with st.spinner("Finding clips…"):
                try:
                    st.session_state["clip_results"] = _pixabay_search(
                        clip_query, PIXABAY_API_KEY, per_page=8)
                    log_activity(user["name"],
                                 f"searched listing clips: {clip_query}")
                except Exception as e:
                    st.error(f"Search failed: {e}")
    for r in st.session_state.get("clip_results", []):
        with st.container(border=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                if r["preview"]:
                    st.image(r["preview"], use_container_width=True)
            with c2:
                st.write(f"⏱️ {r['duration']}s • 📐 "
                         f"{r['width']}×{r['height']}")
                if st.button("✂️ Make 5-sec Clip", key=f"clipmk_{r['id']}"):
                    with st.spinner("Downloading & trimming to 5 sec…"):
                        try:
                            req = urllib.request.Request(
                                r["file"],
                                headers={"User-Agent": "Mozilla/5.0"})
                            with urllib.request.urlopen(req,
                                                         timeout=120) as resp:
                                data = resp.read()
                            clip = _trim_clip(data, 5)
                            st.session_state[f"clipvid_{r['id']}"] = clip
                            log_activity(
                                user["name"],
                                f"made 5-sec listing clip {r['id']} "
                                f"({len(clip)//1024} KB)")
                            st.success("✅ 5-second FB-ready clip done!")
                        except Exception as e:
                            st.error(f"Clip failed: {e}")
                cdata = st.session_state.get(f"clipvid_{r['id']}")
                if cdata:
                    st.video(cdata)
                    st.download_button(
                        "💾 Save Clip (FB-ready MP4)", cdata,
                        file_name=f"listing_clip_{r['id']}.mp4",
                        mime="video/mp4",
                        key=f"clipsv_{r['id']}")


# ----------------------------------------------------------------------------
# 💬 Reply Assistant
# ----------------------------------------------------------------------------
elif page == "💬 Reply Assistant":
    st.subheader("💬 Buyer Reply Assistant — Human Mode 🧑")
    st.caption("Paste a buyer's message → get 3 NATURAL replies that sound "
               "like a real person texting — not a robot. Copy the best one "
               "and send it yourself.")

    if not st.session_state.llm_key:
        st.warning("⚠️ The admin hasn't added the free AI key yet "
                   "(free signup, no payment). "
                   "Ask Mudasir to add it in Admin Panel → API Key.")
        st.stop()

    buyer_msg = st.text_area("Buyer's message", height=100,
                             placeholder="Paste what the buyer wrote…")
    c1, c2 = st.columns(2)
    with c1:
        tone = st.selectbox("Tone", ["Friendly 🙂", "Professional 💼",
                                     "Casual 😎"])
    with c2:
        svc_list = list(st.session_state.service_numbers.keys())
        svc = st.selectbox("Service", svc_list)
    phone = st.session_state.service_numbers.get(svc, DEFAULT_PHONE)

    if st.button("✨ Generate Human Replies", type="primary",
                 use_container_width=True):
        blocked = safety_check(buyer_msg)
        if not buyer_msg.strip():
            st.error("Paste the buyer's message first")
        elif blocked:
            # 🛡️ Misuse blocked — the LLM is never called.
            log_activity(user["name"], "blocked: misuse keywords in reply input")
            st.warning(blocked)
        else:
            log_activity(user["name"], "generated buyer replies (human mode)")
            with st.spinner("💬 Writing like a human…"):
                try:
                    tone_guide = {
                        "Friendly 🙂": ("warm, friendly and natural, like texting "
                                        "a friend"),
                        "Professional 💼": ("polite and confident, but still "
                                            "natural — never stiff"),
                        "Casual 😎": ("very casual and relaxed, like chatting "
                                      "on WhatsApp"),
                    }[tone]
                    system = (
                        "You are a real human customer-service person for "
                        "EasyFix (https://www.easytofix.homes), owned by "
                        "Muhammad Mudassir Yaseen. You text customers in "
                        "NATURAL Roman Urdu mixed with simple English — "
                        "exactly like a real Pakistani person texting. "
                        "Use contractions, short sentences, warm casual flow. "
                        "NEVER sound like an AI or a corporate robot. "
                        "No stiff formal language. "
                        f"Tone: {tone_guide}. "
                        f"Service: {svc}. Price: $110 flat (no hidden charges). "
                        f"Phone: {phone}. Website: https://www.easytofix.homes. "
                        "Weave the phone and website into replies naturally "
                        "(not in every single one). "
                        "Example style: 'Salam bhai! Ji haan, drain cleaning "
                        "ho jayegi. $110 flat hai, koi hidden charges nahi. "
                        "Kab ana hai?' "
                        "Generate exactly 3 different reply drafts, numbered "
                        "1-3, each 1-3 sentences."
                    )
                    out = llm_complete(
                        st.session_state.llm_key,
                        st.session_state.llm_provider,
                        st.session_state.llm_model,
                        [{"role": "system", "content": system},
                         {"role": "user",
                          "content": f"Buyer wrote: {buyer_msg.strip()}"}])
                    st.markdown("### 📋 Human-style reply drafts")
                    st.markdown(out)
                    st.caption("Copy the best draft and send it manually. "
                               "Phone + website are already inside the drafts.")
                except Exception as e:
                    st.error(f"❌ AI error: {e}. The free key may be invalid "
                             "or rate-limited.")


# ----------------------------------------------------------------------------
# 🔄 Smart Account Manager
# Rotation + safe scheduling. The agent NEVER logs in or posts —
# the human always uploads in their own browser.
# ----------------------------------------------------------------------------
elif page == "🔄 Smart Account Manager":
    st.subheader("🔄 Smart Account Manager")
    st.success("🛡️ **Smart scheduling keeps accounts safe.** This module only "
               "*suggests* which account to use next and tracks rest limits — "
               "it never logs in or uploads. **YOU upload in your browser.**")

    settings = st.session_state.acct_settings
    gap = float(settings.get("min_gap_hours", 2))
    limit = int(settings.get("daily_limit", 3))

    # --- 1. Which account should I use? ---
    st.markdown("### 🎯 Which account should I use?")
    rot_plat = st.selectbox(
        "Platform",
        ["YouTube", "Rumble", "Instagram", "Dailymotion", "Facebook"],
        key="rot_platform")
    member, idx, entry, note = _suggest_account(rot_plat)
    if entry is None:
        st.warning("⏸️ **Rest — no account available right now.**\n\n"
                   f"{note}\n\n"
                   "Try another platform, wait for the rest gap, or register "
                   "more accounts in 🔑 Account Vault.")
    else:
        with st.container(border=True):
            st.markdown(f"### ✅ Use: **{entry['platform']}** — "
                        f"{_mask_email(entry.get('email'))}")
            st.caption(f"👤 {member} • {note}")
            if st.button("✅ Mark as uploaded", type="primary",
                         key="rot_mark"):
                _mark_uploaded(member, entry, rot_plat, user["name"])
                st.success("✅ Logged! The next upload will rotate to "
                           "another account.")
                st.rerun()

    st.divider()

    # --- 2. Upload checklist ---
    st.markdown("### 📋 Upload Checklist")
    st.caption("Metadata is generated USA-targeted 🇺🇸 — copy it, upload in "
               "your browser, then mark it done so rotation stays accurate.")
    cc1, cc2 = st.columns(2)
    with cc1:
        chk_topic = st.text_input("Video topic", key="chk_topic",
                                  placeholder="e.g. Leaky Faucet Fix")
    with cc2:
        chk_city = st.selectbox("📍 Target city (USA)",
                                USA_CITIES_WITH_CUSTOM, key="chk_city")
        if chk_city == "✏️ Custom…":
            chk_city_val = st.text_input("Custom city", key="chk_city_custom",
                                         placeholder="e.g. Austin, TX")
        else:
            chk_city_val = chk_city
    if st.button("✨ Build checklist", key="chk_build"):
        if not chk_topic.strip():
            st.error("Enter the video topic")
        elif not chk_city_val.strip():
            st.error("Pick a target city")
        else:
            blocked = safety_check(chk_topic)
            if blocked:
                log_activity(user["name"],
                             "blocked: misuse keywords in upload checklist")
                st.warning(blocked)
            else:
                st.session_state.chk_meta = {
                    "title": f"{chk_topic} in {chk_city_val} — $110",
                    "desc": (
                        f"🔧 {chk_topic} in {chk_city_val}, USA! 🇺🇸\n\n"
                        f"Watch how our pros handle it — funny AND "
                        f"educational!\n\n"
                        f"💰 $110 flat — no hidden charges\n"
                        f"📞 Call/Text: {PHONE}\n"
                        f"🌐 {SITE_URL}\n\n"
                        f"👍 Like & follow USA Trade Confessions for daily "
                        f"home tips!"
                    ),
                    "tags": ("plumber, plumbing, hometips, USA, funny, "
                             "diy, home repair, shorts, "
                             f"{chk_city_val.replace(', ', ' ').replace(',', '')}, "
                             "usatradeconfessions"),
                    "city": chk_city_val,
                    "topic": chk_topic,
                    "platform": rot_plat,
                }
                log_activity(user["name"],
                             f"built upload checklist: {chk_topic} "
                             f"→ {chk_city_val}")
    meta = st.session_state.get("chk_meta")
    if meta:
        st.markdown("**☑ 1. Account:** "
                    f"{rot_plat} — see the suggestion above ☝️")
        st.text_input("☑ 2. Title (copy)", value=meta["title"],
                      key="chk_title")
        st.text_area("☑ 3. Description (copy)", value=meta["desc"],
                     height=180, key="chk_desc")
        st.text_input("☑ 4. Tags (copy)", value=meta["tags"],
                      key="chk_tags")
        st.info(f"☑ 5. **Best time to post:** 7–9am or 6–8pm US Eastern "
                f"gets the most views. Set video location to "
                f"**{meta['city']}, USA** during upload. 🇺🇸")

    with st.expander("⏰ Human-like timing tips"):
        st.markdown("""
        - 📅 **Space uploads out** — never post 2 videos within 30 minutes
          on the same account.
        - 🌙 **Let accounts rest** — the rotation above enforces a rest gap
          automatically.
        - 🎭 **Vary your content** — same title/description on every video
          looks like spam. Tweak the topic each time.
        - 👀 **Watch for warnings** — if a platform ever flags an account,
          set its status to **Flagged** in the health dashboard below and
          stop using it until the admin reviews it.
        - 🧍 **You are the human** — the agent prepares, you click. That's
          what keeps accounts alive.
        """)

    # --- 3. Admin: health dashboard + scheduling settings ---
    if is_admin:
        st.divider()
        st.markdown("### 🏥 Account Health Dashboard")
        rows = _all_accounts()
        if not rows:
            st.info("No accounts registered yet — team members add them in "
                    "🔑 Account Vault.")
        else:
            for m_name, a_idx, a in rows:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 2])
                    with c1:
                        st.markdown(f"**{a['platform']}** — "
                                    f"{_mask_email(a.get('email'))}")
                        st.caption(f"👤 {m_name}")
                    with c2:
                        st.caption(f"📤 {a.get('uploads_today', 0)}/{limit} today")
                        st.caption(f"🕒 last: {_rel_time(a.get('last_used'))}")
                    with c3:
                        new_status = st.selectbox(
                            "Status",
                            ["Active", "Resting", "Flagged"],
                            index=["Active", "Resting", "Flagged"].index(
                                a.get("status", "Active")),
                            key=f"acctstat_{m_name}_{a_idx}")
                        if new_status != a.get("status"):
                            a["status"] = new_status
                            log_activity("Admin",
                                         f"set {m_name}'s {a['platform']} "
                                         f"account to {new_status}")
                            st.rerun()

        st.divider()
        st.markdown("### ⚙️ Safe Scheduling Settings")
        st.caption("Applies to every account, every team member.")
        sc1, sc2 = st.columns(2)
        with sc1:
            new_gap = st.number_input(
                "⏳ Min hours between uploads (same account)",
                min_value=0.5, max_value=24.0, step=0.5,
                value=float(settings.get("min_gap_hours", 2)),
                key="acct_gap")
        with sc2:
            new_limit = st.number_input(
                "📊 Max uploads per account per day",
                min_value=1, max_value=10, step=1,
                value=int(settings.get("daily_limit", 3)),
                key="acct_limit")
        if st.button("💾 Save scheduling settings", type="primary",
                     key="acct_save"):
            st.session_state.acct_settings = {"min_gap_hours": float(new_gap),
                                              "daily_limit": int(new_limit)}
            log_activity("Admin",
                         f"updated scheduling: {new_gap}h gap, "
                         f"{new_limit}/day limit")
            st.success("✅ Saved — applies immediately.")
            st.rerun()


# ----------------------------------------------------------------------------
# 🔑 Account Vault
# ----------------------------------------------------------------------------
elif page == "🔑 Account Vault":
    st.subheader("🔑 Account Vault")
    st.warning("⚠️ **Agent drafts everything — YOU click send in your browser.**\n\n"
               "Auto-login or auto-posting gets accounts BANNED by Facebook/YouTube. "
               "Never type your password into this app.")
    st.info("🔒 Passwords are NEVER stored here. Only account emails are saved "
            "(masked), so the admin knows which accounts each member uses.")

    st.markdown("### Add your account")
    c1, c2 = st.columns(2)
    with c1:
        platform = st.selectbox("Platform", ["Facebook", "YouTube",
                                             "Instagram", "Dailymotion", "Rumble"],
                                key="vault_platform")
    with c2:
        email = st.text_input("Account email", key="vault_email",
                              placeholder="your@email.com")
    note = st.text_input("Note (optional)", key="vault_note",
                         placeholder="e.g. marketplace profile")
    if st.button("➕ Save account", type="primary"):
        if not email.strip() or "@" not in email:
            st.error("Enter a valid email")
        else:
            name = user["name"]
            st.session_state.account_vault.setdefault(name, []).append(
                {"platform": platform, "email": email.strip(),
                 "note": note.strip()})
            log_activity(name, f"registered {platform} account")
            st.success(f"✅ {platform} account saved (email masked)")
            st.rerun()

    st.divider()
    st.markdown("### Your accounts")
    mine = st.session_state.account_vault.get(user["name"], [])
    if not mine:
        st.info("No accounts registered yet.")
    for i, a in enumerate(mine):
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{a['platform']}** — {_mask_email(a['email'])}")
                if a.get("note"):
                    st.caption(a["note"])
            with c2:
                if st.button("🗑️", key=f"vaultdel_{i}"):
                    del st.session_state.account_vault[user["name"]][i]
                    log_activity(user["name"], f"removed {a['platform']} account")
                    st.rerun()


# ----------------------------------------------------------------------------
# 📋 Message Templates
# ----------------------------------------------------------------------------
elif page == "📋 Message Templates":
    st.subheader("📋 Message Templates")
    st.caption("Pick a template → fill the blanks → copy → send. "
               "Templates are managed by the admin.")

    if not st.session_state.msg_templates:
        st.info("No templates yet — ask the admin to add some.")
    else:
        tpl_name = st.selectbox("Template",
                                list(st.session_state.msg_templates.keys()))
        body = st.session_state.msg_templates[tpl_name]

        c1, c2 = st.columns(2)
        with c1:
            cust_name = st.text_input("Customer name", key="tpl_cust_name",
                                      placeholder="e.g. John")
        with c2:
            svc_list = list(st.session_state.service_numbers.keys())
            tpl_svc = st.selectbox("Service", svc_list, key="tpl_svc")
        phone = st.session_state.service_numbers.get(tpl_svc, DEFAULT_PHONE)

        filled = (body
                  .replace("{name}", cust_name.strip() or "[Name]")
                  .replace("{service}", tpl_svc)
                  .replace("{price}", "$110")
                  .replace("{phone}", phone)
                  .replace("{website}", SITE_URL))
        st.markdown("### 📝 Ready message")
        st.text_area("Copy this", value=filled, height=130, key="tpl_out")
        st.caption("Tap the text → copy → paste into Messenger/WhatsApp/FB.")


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
    7. **🛡️ No misuse, ever:** fraud, fake accounts/reviews, piracy, hacking,
       spam, impersonation, fake documents — **koi bhi ghalat kaam nahi.**
       The agent REFUSES such requests for everyone, including the admin.
       Sahi mashwara do, ghalat kaam kabhi mat karo.
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


elif page == "🛡️ Safety Toolkit":
    st.subheader("🛡️ Safety Toolkit")
    st.write("Keep your accounts safe — check your IP, manage Chrome profiles, "
             "and understand proxies honestly.")
    log_activity(user["name"], "opened Safety Toolkit")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🌐 IP Detector", "👤 Chrome Profiles", "🔌 Proxy Guide",
         "🔒 NordVPN Setup"])

    # ---------------- 1. IP Detector ----------------
    with tab1:
        st.markdown("### 🌐 IP Detector")
        st.caption("Check what country your internet connection appears from. "
                   "Free — no key needed (ipify + ip-api).")
        if st.button("🔍 Check My IP", type="primary"):
            with st.spinner("Checking..."):
                ip_data = _get_json("https://api.ipify.org?format=json")
                if ip_data and ip_data.get("ip"):
                    ip = ip_data["ip"]
                    info = _get_json(f"http://ip-api.com/json/{ip}"
                                     "?fields=status,country,countryCode,city,isp,query")
                    st.markdown(f"**Your IP:** `{ip}`")
                    if info and info.get("status") == "success":
                        country = info.get("country", "?")
                        cc = (info.get("countryCode") or "").upper()
                        city = info.get("city", "?")
                        isp = info.get("isp", "?")
                        st.markdown(f"**Country:** {country} ({cc})")
                        st.markdown(f"**City:** {city}")
                        st.markdown(f"**ISP:** {isp}")
                        if cc == "US":
                            st.success("🇺🇸 **USA IP detected** — good for "
                                       "USA-targeted accounts!")
                        else:
                            st.error(f"⚠️ **NOT USA** — your IP shows "
                                     f"{country}. USA accounts work best when "
                                     "the IP matches the account country.")
                    else:
                        st.warning("Could not get location details — "
                                   "showing IP only.")
                else:
                    st.error("Could not detect IP. Check your connection and "
                             "try again.")
        st.info("💡 **Tip:** FB accounts work best when your IP country matches "
                "the account's country. If you travel or use a VPN, check here "
                "first.")

    # ---------------- 2. Chrome Profile Manager ----------------
    with tab2:
        st.markdown("### 👤 Chrome Profile Manager")
        st.caption("One Chrome profile per FB account = accounts stay separate "
                   "and safer. No mixing cookies/sessions.")
        with st.expander("📖 How to create a Chrome profile (step by step)",
                         expanded=False):
            st.markdown(
                "1. Open Chrome → click your **profile icon** (top-right)\n"
                "2. Click **Add** / **Add another account**\n"
                "3. Click **Continue without an account**\n"
                "4. Name it clearly, e.g. `FB-Account-1`, pick a color\n"
                "5. Click **Done** — a new Chrome window opens for this profile\n"
                "6. **Log in to ONE FB account only** in this profile\n"
                "7. Repeat for each FB account — never mix accounts in one profile\n\n"
                "**Rules:**\n"
                "- 🔒 One profile = one FB account. Never log two accounts in "
                "the same profile.\n"
                "- 🚫 Don't switch accounts rapidly inside one profile.\n"
                "- 💤 Let new profiles 'warm up' — normal browsing a few days "
                "before heavy posting."
            )
        st.markdown("#### 📋 Profile ↔ Account Tracker")
        if "chrome_profiles" not in st.session_state:
            st.session_state.chrome_profiles = []
        with st.form("add_chrome_profile", clear_on_submit=True):
            c1, c2 = st.columns(2)
            member = c1.text_input("Team member name")
            profile = c2.text_input("Chrome profile name", placeholder="FB-Account-1")
            c3, c4 = st.columns(2)
            fb_acc = c3.text_input("FB account (email)", placeholder="masked in list")
            notes = c4.text_input("Notes (optional)")
            if st.form_submit_button("➕ Add mapping"):
                if member.strip() and profile.strip():
                    st.session_state.chrome_profiles.append({
                        "member": member.strip(),
                        "profile": profile.strip(),
                        "fb": _mask_email(fb_acc.strip()) if fb_acc.strip() else "—",
                        "notes": notes.strip(),
                    })
                    log_activity(user["name"],
                                 f"mapped Chrome profile '{profile.strip()}'")
                    st.success("Mapping added!")
                    st.rerun()
                else:
                    st.warning("Member name and profile name are required.")
        rows = st.session_state.chrome_profiles
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.caption("No mappings yet — add your first one above.")

    # ---------------- 3. Proxy Guide (honest) ----------------
    with tab3:
        st.markdown("### 🔌 Proxy Guide")
        st.warning("⚠️ **Honest truth:** No reliable FREE USA proxy exists. "
                   "Free proxies are slow, die within hours, are usually "
                   "already blocked by Facebook, and can steal your passwords "
                   "and data. Never enter real account passwords through a "
                   "free proxy you don't trust.")
        with st.expander("🔧 How to enter a proxy in Chrome (step by step)",
                         expanded=False):
            st.markdown(
                "1. Open the Chrome profile for that account\n"
                "2. Go to **Settings → System → Open your computer's proxy "
                "settings** (Windows) or **Network → Proxies** (Mac)\n"
                "3. Enable **Manual proxy setup**\n"
                "4. Enter the proxy **IP/hostname** and **port**\n"
                "5. If it needs a username/password, Chrome will ask on first "
                "use\n"
                "6. Re-check the **🌐 IP Detector** tab — it should show the "
                "proxy's country, not yours"
            )
        st.markdown("#### Proxy types — what to know")
        st.markdown(
            "- 🟢 **Residential (paid)** — real home IPs, best for accounts. "
            "Costs money ($5–15/GB typically). USA residential = what serious "
            "teams use.\n"
            "- 🟡 **Datacenter (cheap)** — server IPs. Cheap but Facebook "
            "spots them fast → higher ban risk.\n"
            "- 🔴 **Free lists** — slow, unreliable, often already blacklisted, "
            "and a real **security risk** (traffic can be spied on). "
            "**Not recommended for any account you care about.**"
        )
        st.info("💡 **Bottom line:** If you buy, buy **USA residential** "
                "proxies only, from a reputable provider. One proxy per "
                "account. There is no safe free option — anyone promising "
                "one is not telling the truth.")

    # ---------------- 4. NordVPN Setup ----------------
    with tab4:
        st.markdown("### 🔒 NordVPN Setup")
        st.success("✅ **Good news:** The owner has **NordVPN (paid)**. "
                   "Install it on **your own device** and every team member "
                   "gets a real **USA IP** — Facebook sees a USA location, "
                   "not the office WiFi.")
        st.markdown("#### Why this works")
        st.markdown(
            "NordVPN on **your laptop/phone** → your internet goes through a "
            "**USA server** → Facebook sees a **USA IP address**. "
            "30 members on 1 office WiFi = 1 IP = bans. "
            "30 members each on NordVPN USA = 30 different IPs = **safe**."
        )
        with st.expander("💻 Laptop setup (step by step)", expanded=True):
            st.markdown(
                "1. Download NordVPN from **nordvpn.com** and install it\\n"
                "2. **Log in** with the team NordVPN account (ask the admin)\\n"
                "3. In the server list, search **United States**\\n"
                "4. Pick a server in **Dallas** or **Chicago** (close = fast)\\n"
                "5. Click **Connect** — wait for the green \"Connected\" status\\n"
                "6. Open the **🌐 IP Detector** tab here and press "
                "**Check My IP** — it must show **🇺🇸 USA**\\n"
                "7. Only then open Facebook in your Chrome profile"
            )
        with st.expander("📱 Phone setup (step by step)", expanded=False):
            st.markdown(
                "1. Install **NordVPN** from the Play Store / App Store\\n"
                "2. **Log in** with the team NordVPN account\\n"
                "3. Connect to a **United States** server (Dallas/Chicago)\\n"
                "4. Open your phone browser and do Facebook work there\\n"
                "5. Keep the VPN connected the **whole time** you work"
            )
        st.markdown("#### 📏 Team rules — follow these every day")
        st.markdown(
            "- ✅ **VPN ON before opening Facebook** — always, no exceptions\\n"
            "- ✅ **Same USA city per account** — don't switch cities daily, "
            "it looks suspicious\\n"
            "- ✅ One NordVPN login works on **10 devices at the same time**\\n"
            "- ❌ **Never** do Facebook work with the VPN disconnected\\n"
            "- ❌ Don't share your Chrome profile with another member"
        )
        st.warning("⚠️ **Device limit math:** 30 members ÷ 10 devices per "
                   "NordVPN login = the team may need **3 NordVPN logins**. "
                   "Check the plan's device limit with the admin — if logins "
                   "run out, split members into groups of 10.")
        with st.expander("✅ VPN Check — do this BEFORE starting work",
                         expanded=False):
            st.markdown(
                "**Every member, every day, before touching Facebook:**\\n\\n"
                "1. ☐ NordVPN **connected** to a USA server?\\n"
                "2. ☐ **IP Detector** tab shows **🇺🇸 USA**?\\n"
                "3. ☐ Correct **Chrome profile** for your account?\\n\\n"
                "All three green → **start work**. Any red → **fix it first**."
            )

        # ---------------- NordVPN credential distribution ----------------
        st.markdown("---")
        if is_admin:
            st.markdown("### 🔑 NordVPN Logins Manager")
            st.caption("Your own paid NordVPN logins — given to team members "
                       "through the agent. Only you can see or change these.")
            st.warning("⚠️ **10 devices max per NordVPN login** — assign "
                       "wisely across the team. 🔒 **Never share these logins "
                       "outside the team.**")
            _nords = st.session_state.nord_logins
            if len(_nords) >= 4:
                st.info("Maximum 4 NordVPN logins stored — delete one to add "
                        "another.")
            else:
                with st.expander("➕ Add NordVPN login", expanded=False):
                    with st.form("nord_add", clear_on_submit=True):
                        _nl = st.text_input("Label", placeholder="e.g. Nord-1")
                        _nu = st.text_input("Username / email")
                        _np = st.text_input("Password", type="password")
                        _nc = st.text_input("Default USA server city",
                                            value="Dallas")
                        if st.form_submit_button("💾 Save login"):
                            if not _nl.strip() or not _nu.strip() or not _np:
                                st.error("Label, username and password are "
                                         "required")
                            elif any(l["label"].lower() == _nl.strip().lower()
                                     for l in _nords):
                                st.error("A login with this label already "
                                         "exists")
                            else:
                                _nords.append({
                                    "label": _nl.strip(),
                                    "username": _nu.strip(),
                                    "password": _np,
                                    "server_city": (_nc or "Dallas").strip()})
                                log_activity(
                                    "Admin",
                                    f"added NordVPN login {_nl.strip()}")
                                st.success(f"✅ **{_nl.strip()}** saved")
                                st.rerun()
            for _li, _nl in enumerate(list(_nords)):
                _label = _nl["label"]
                _users = [m["name"] for m in st.session_state.team.values()
                          if m.get("nord", {}).get("login") == _label]
                _n_used = len(_users)
                with st.container(border=True):
                    _h1, _h2 = st.columns([3, 1])
                    with _h1:
                        st.markdown(f"**{_label}** — `{_n_used}/10` devices "
                                    "used")
                        st.progress(min(1.0, _n_used / 10))
                        st.caption(f"Server: {_nl.get('server_city', 'Dallas')}, "
                                   "USA")
                    with _h2:
                        _show = st.checkbox("Show", key=f"nord_show_{_li}")
                    if _show:
                        st.markdown("**Username:**")
                        st.code(_nl["username"])
                        st.markdown("**Password:**")
                        st.code(_nl["password"])
                    else:
                        st.caption(f"👤 {_nl['username'][:3]}••• | 🔑 ••••••••")
                    if _users:
                        st.caption("👥 Assigned to: " + ", ".join(_users))
                    else:
                        st.caption("👥 Not assigned to anyone yet")
                    if st.button("🗑️ Delete login", key=f"nord_del_{_li}"):
                        for _m in st.session_state.team.values():
                            if _m.get("nord", {}).get("login") == _label:
                                _m.pop("nord", None)
                        _nords.pop(_li)
                        log_activity("Admin",
                                     f"deleted NordVPN login {_label}")
                        st.success(f"Deleted **{_label}**")
                        st.rerun()
        else:
            # ---- Team member view: their own VPN login card ----
            _mem = st.session_state.team.get(user.get("code", ""), {})
            _mn = _mem.get("nord")
            st.markdown("### 🔑 Your VPN Login")
            if not _mn:
                st.info("No NordVPN login assigned to you yet — ask the admin "
                        "(Mudasir) to assign one.")
            else:
                _login = next(
                    (l for l in st.session_state.nord_logins
                     if l["label"] == _mn["login"]), None)
                if not _login:
                    st.warning("Your assigned NordVPN login was removed — ask "
                               "the admin for a new one.")
                else:
                    _city = _mn.get("server_city",
                                    _login.get("server_city", "Dallas"))
                    with st.container(border=True):
                        st.markdown(f"### 🔒 {_login['label']}")
                        st.success(f"🌐 Connect to: **{_city}, USA** 🇺🇸")
                        st.markdown("**Username** (tap 📋 to copy):")
                        st.code(_login["username"])
                        st.markdown("**Password** (tap 📋 to copy):")
                        st.code(_login["password"])
                        st.caption(
                            "1. Open NordVPN on your device → log in with the "
                            f"above → connect to **{_city}, USA** → then open "
                            "the 🌐 IP Detector tab here and press "
                            "**Check My IP**.")
                        if st.button("✅ I connected — my IP is USA",
                                     type="primary"):
                            log_activity(
                                user["name"],
                                f"confirmed NordVPN connected ({_city}, USA)")
                            st.success("✅ Logged! Now verify in the "
                                       "🌐 IP Detector tab.")
        st.markdown("---")

        # ---------------- 5. VPN Setup Tracker ----------------
        st.markdown("---")
        st.markdown("### 📋 VPN Setup Tracker")
        st.caption("Admin tracks who has NordVPN installed. Members verify "
                   "their own IP here before work.")
        if "vpn_tracker" not in st.session_state:
            # [{name, device, installed, server_city, last_ip, last_country, last_check}]
            st.session_state.vpn_tracker = []
        if "vpn_team_target" not in st.session_state:
            st.session_state.vpn_team_target = 30

        _vrows = st.session_state.vpn_tracker
        _secured = sum(1 for _r in _vrows if _r.get("installed"))
        _target = max(1, int(st.session_state.vpn_team_target))
        st.markdown(f"#### 📊 VPN Coverage: **{_secured}/{_target}** "
                    "members secured")
        st.progress(min(1.0, _secured / _target))

        if is_admin:
            with st.expander("⚙️ Admin: team size target", expanded=False):
                _t = st.number_input("Team size target", min_value=1,
                                     max_value=200, value=_target,
                                     key="vpn_target_input")
                if int(_t) != _target:
                    st.session_state.vpn_team_target = int(_t)
                    st.rerun()
            with st.expander("➕ Add / update member", expanded=False):
                with st.form("vpn_add_member", clear_on_submit=True):
                    _c1, _c2 = st.columns(2)
                    _m_name = _c1.text_input("Member name")
                    _m_device = _c2.selectbox(
                        "Device", ["Laptop", "Phone", "Laptop + Phone"])
                    _m_city = _c1.text_input("USA server city", value="Dallas")
                    _m_inst = _c2.checkbox("VPN installed ✅", value=False)
                    if st.form_submit_button("💾 Save"):
                        if not _m_name.strip():
                            st.error("Enter a name")
                        else:
                            _ex = next(
                                (_r for _r in _vrows
                                 if _r["name"].lower() == _m_name.strip().lower()),
                                None)
                            if _ex:
                                _ex.update({"device": _m_device,
                                            "installed": bool(_m_inst),
                                            "server_city": _m_city.strip() or "Dallas"})
                                log_activity("Admin",
                                             f"updated VPN tracker for {_m_name}")
                                st.success(f"Updated **{_m_name}**")
                            else:
                                _vrows.append({
                                    "name": _m_name.strip(), "device": _m_device,
                                    "installed": bool(_m_inst),
                                    "server_city": _m_city.strip() or "Dallas",
                                    "last_ip": "-", "last_country": "-",
                                    "last_check": "-"})
                                log_activity("Admin",
                                             f"added {_m_name} to VPN tracker")
                                st.success(f"Added **{_m_name}** to tracker")
                            st.rerun()

        st.markdown("#### 👥 Tracker")
        if not _vrows:
            st.info("No members in the tracker yet — admin adds them above.")
        else:
            for _i, _r in enumerate(_vrows):
                if _r.get("installed") and _r.get("last_country") == "US":
                    _st = "✅ Secured"
                elif _r.get("installed"):
                    _st = "🟡 Installed — not verified"
                else:
                    _st = "❌ Not installed"
                with st.container(border=True):
                    _cc1, _cc2, _cc3 = st.columns([4, 3, 1])
                    with _cc1:
                        st.markdown(f"**{_r['name']}** · {_r['device']} · "
                                    f"{_r['server_city']}")
                        st.caption(f"Last check: {_r['last_ip']} · "
                                   f"{_r['last_country']} · {_r['last_check']}")
                    with _cc2:
                        st.markdown(_st)
                    with _cc3:
                        if is_admin:
                            if st.button("🔄", key=f"vpn_toggle_{_i}",
                                         help="Toggle installed on/off"):
                                _r["installed"] = not _r["installed"]
                                log_activity(
                                    "Admin",
                                    f"toggled VPN for {_r['name']} -> "
                                    f"{_r['installed']}")
                                st.rerun()

        st.markdown("#### 🔍 Verify My IP")
        st.caption("One click — checks your current IP and country.")
        if st.button("🔍 Verify My IP", type="primary", key="vpn_verify_ip"):
            with st.spinner("Checking..."):
                _ip_data = _get_json("https://api.ipify.org?format=json")
                _ip = _ip_data.get("ip") if _ip_data else None
                if not _ip:
                    st.error("Could not detect IP. Check your connection "
                             "and try again.")
                else:
                    _info = _get_json(
                        f"http://ip-api.com/json/{_ip}"
                        "?fields=status,country,countryCode")
                    _cc = ((_info.get("countryCode") or "").upper()
                           if _info and _info.get("status") == "success"
                           else "")
                    _country = (_info.get("country", "?")
                                if _info else "?")
                    st.markdown(f"**Your IP:** `{_ip}` · **Country:** "
                                f"{_country} ({_cc or '?'})")
                    if _cc == "US":
                        st.success("✅ **Secure — kaam shuru karo!** "
                                   "Your IP is in the USA.")
                    else:
                        st.error("⚠️ **VPN on karo phir check karo!** "
                                 "Your IP is NOT in the USA.")
                    _me = next(
                        (_r for _r in _vrows
                         if _r["name"].lower() == user["name"].lower()),
                        None)
                    if _me:
                        _me.update({
                            "last_ip": _ip,
                            "last_country": _cc or _country,
                            "last_check": time.strftime("%Y-%m-%d %H:%M")})
                        log_activity(user["name"],
                                     f"verified IP {_ip} ({_country})")


# ----------------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------------
st.markdown(
    '<p class="footer">🔧 <b>EasyFix Agent</b> — built for '
    '<b>Muhammad Mudassir Yaseen</b> · 💯 <b>100% FREE</b> — no paid credits, ever<br>'
    '🌐 <a href="https://www.easytofix.homes" style="color:#a78bfa;">'
    'easytofix.homes</a> · 📞 +18312931196</p>',
    unsafe_allow_html=True,
)
