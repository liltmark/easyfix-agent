# 🔧 EasyFix Agent

**Built for Muhammad Mudassir Yaseen** — the team AI command center.

## 💯 100% FREE — no paid credits, ever

This is non-negotiable. Every feature uses only free resources:

| Feature | Free source | Signup needed? |
|---|---|---|
| 💬 Reply Assistant (AI chat) | Groq free tier / Gemini free tier | ✅ Free signup only — no payment, no credit card |
| 🎙️ Voiceover | edge-tts | ❌ No key needed at all |
| 🎬 AI video generation | Public Hugging Face Spaces (auto-fallback) | ❌ No key needed |
| 🎞️ Stock video search | Pixabay API (your free key, unlimited) | ✅ Free signup only |
| 📝 Listing generator | Built-in templates | ❌ Nothing needed |

**Rule:** if any feature would need paid credits, it is either replaced with a
free alternative or clearly labeled "needs free signup, no payment".

## What it does

| Module | Who | Description |
|---|---|---|
| 🎬 Video Studio | videos | Free AI text-to-video & image-to-video + voiceover |
| 🎙️ Voiceover Studio | videos | Free AI voices (US/UK/Urdu) → MP3 |
| 📝 Listing Generator | listings | FB Marketplace title + description generator ($110 flat, +18312931196, easytofix.homes) |
| 💬 Reply Assistant | replies | Paste buyer message → 3 professional reply drafts (free Groq/Gemini key) |
| 🧠 Knowledge Base | all | Searchable business knowledge: services, characters, video rules, ideas |
| 🔗 Tools Hub | all | **Free Video Sources Hub** (Pixabay direct search + honest quota cards) + general tools |
| 📋 Surveys | all | Earning surveys |
| 👑 Admin Panel | admin | Create/remove team members, access codes, role assignment, activity log |

## Team system

- **Admin** (Mudasir): password `easyfix123` (change it in Admin Panel → Settings)
- **Team members**: admin creates them → each gets a unique 6-letter access code + only their assigned modules
- Team works UNDER the admin — no full access, activity is logged

## Deploy (Streamlit Cloud — free)

1. Push this folder to a GitHub repo (public)
2. Go to share.streamlit.io → New app → select repo → main file `app.py` → Deploy
3. **Pixabay search**: add your free key at App settings → Secrets as `PIXABAY_API_KEY` (get one free at pixabay.com/api/docs). Without it, the Pixabay search box shows a warning but everything else works.
4. **Reply Assistant**: admin adds a free Groq key (console.groq.com) or Gemini key (aistudio.google.com) in Admin Panel → API Key. The team never sees the key.

## Monetization

- Ad gate on entry (10 sec, Adsterra units)
- Ad before every video download
- Survey unlock every 3rd video
- Edit `AD_HTML` / `SURVEY_LINKS` at the top of `app.py` to change networks

## Chrome extension

See `extension/` — a launcher that opens EasyFix Agent + quick links.
Install: `chrome://extensions` → Developer mode ON → Load unpacked → select `extension/`.
Note: it is a launcher/shortcut panel, not full browser automation.

## Free-only

No paid APIs. Video engines are public Hugging Face Spaces with auto-fallback.
Quotas are shown honestly in the Tools Hub.
