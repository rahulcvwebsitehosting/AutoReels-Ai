# AutoReels Ai — Automated Faceless YouTube Shorts Generator

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/FFmpeg-Required-red?style=for-the-badge&logo=ffmpeg" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
  <img src="https://komarev.com/ghpvc/?username=AutoReels-Ai&style=for-the-badge&color=blue" />
</p>

<p align="center">
  <b>Open‑source pipeline that converts a topic into a fully‑edited, faceless YouTube Short —<br>scriptwriting, voiceover, stock footage, transitions, all automated.</b>
</p>

<p align="center">
  Built with ❤️ by
  <a href="https://www.linkedin.com/in/rahulshyamcivil/">Rahul Shyam Civil</a>
  ·
  <a href="https://x.com/RahulShyamCv">X / Twitter</a>
  ·
  <a href="https://threads.com/@RahulCvJPS">Threads</a>
</p>

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Pipeline Walkthrough (Step by Step)](#pipeline-walkthrough-step-by-step)
- [Quick Start](#quick-start)
- [LLM Provider Configuration](#llm-provider-configuration)
- [Project Structure](#project-structure)
- [Module Reference](#module-reference)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Why This Exists

I built AutoReels Ai because creating consistent, high‑quality faceless shorts by hand is time‑consuming and repetitive. This tool automates the entire production chain — from ideation to rendered MP4 — so you can focus on content strategy, not manual editing.

**It is 100 % open‑source, free to use, modify, and deploy.** If you find value in it, a star on GitHub or a shoutout on socials means the world.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        main.py  (Orchestrator)                              │
│    Calls each module in sequence, passes data via Python objects             │
└───────┬───────────────────────────┬───────────────────────────┬─────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌─────────────────┐        ┌──────────────────┐
│   ContentBrain │          │   AudioEngine    │        │   AssetManager   │
│  (modules/    │          │  (modules/      │        │  (modules/       │
│   brain.py)   │          │   audio.py)      │        │   asset_         │
│               │          │                  │        │   manager.py)    │
│ 1. Picks topic│          │ 1. Splits script │        │                  │
│ 2. Calls LLM  │          │    into scenes   │        │ 1. Searches      │
│    → JSON     │          │ 2. edge-tts TTS  │        │    Pexels API    │
│    script     │          │    → per-scene   │        │    per keyword   │
│               │          │    audio files   │        │ 2. Downloads     │
│               │          │ 3. Mutagen reads │        │    portrait      │
│               │          │    durations     │        │    (9:16) videos │
└───────┬───────┘          └────────┬────────┘        └────────┬─────────┘
        │                          │                          │
        │    ┌─────────────────────┼──────────────────────────┘
        │    │                     │
        ▼    ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Composer (modules/composer.py)                     │
│                                                                             │
│   For each scene:                                                           │
│     ✂  Trim video_A to first half of audio duration                        │
│     ✂  Trim video_B to second half of audio duration                       │
│     🎭  (Optional) inject avatar into a random middle scene                  │
│     🔀  Concatenate A + B into a single scene clip                         │
│                                                                             │
│   After all scenes:                                                         │
│     🎬  Stitch scenes with xfade transitions (fade, slide, wipe)           │
│     🎞  Render final MP4 (H.264, yuv420p, faststart)                       │
│                                                                             │
└───────────────────────────┬─────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  assets/final/           │
              │  final_short.mp4         │
              │  🏆  YOU'RE DONE         │
              └─────────────────────────┘
```

---

## Tech Stack

| Component              | Technology                                        |
|------------------------|---------------------------------------------------|
| Language               | Python 3.10+                                      |
| LLM Interface          | 7 providers via unified `LLMClient` abstraction   |
| Text‑to‑Speech         | `edge-tts` (Microsoft Edge TTS engine)            |
| Stock Footage API      | Pexels API (free tier, portrait 9:16 videos)      |
| Audio Analysis         | `mutagen` (read MP3 durations)                    |
| Video Processing       | FFmpeg + `ffmpeg-python` wrapper                  |
| Config / Secrets       | `python-dotenv` + `.env` file                     |
| Packaging              | `requirements.txt`                                |

### Supported LLM Providers

| Provider       | SDK/Protocol               | Default Model             |
|----------------|----------------------------|---------------------------|
| Gemini         | `google-genai` (native)    | `gemini-2.0-flash`        |
| OpenAI         | `openai` (Chat Completions)| `gpt-4o-mini`             |
| OpenRouter     | `openai` (Chat Completions)| `openrouter/auto`         |
| Groq           | `openai` (Chat Completions)| `llama-3.3-70b-versatile` |
| Anthropic      | `anthropic` (native)       | `claude-3-5-sonnet-latest`|
| Ollama         | `openai` (Chat Completions)| `llama3.1`                |
| OpenCode Zen   | `openai` (Chat Completions)| `openrouter/auto`         |

---

## Pipeline Walkthrough (Step by Step)

### Step 1 — Topic Selection
`ContentBrain.get_trending_topic()` asks the active LLM for one viral, engaging short‑documentary topic. The response is a plain‑text topic string.

### Step 2 — Script Generation
`ContentBrain.generate_script(topic)` sends a structured prompt to the LLM requesting an 8–9 scene JSON array. Every scene contains:
- `text` — the voiceover line
- `visual_1` / `visual_2` — two distinct Pexels‑optimised search terms (creates the A/B split visual effect)
- `mood` — tone hint for editing (e.g. `"intriguing"`, `"educational"`)

The LLM response is parsed from JSON (markdown fences are stripped automatically).

### Step 3 — Voiceover Generation
`AudioEngine.process_script()` iterates over every scene, calls `edge-tts` to generate a `.mp3` file per scene, and measures its exact duration with `mutagen`. Durations are stored back onto each scene object so the composer can sync video length to audio length.

### Step 4 — Stock Footage Download
`AssetManager.get_videos()` loops over each scene's two keywords (`visual_1`, `visual_2`) and queries the Pexels API for portrait (9:16, `orientation=portrait`) videos. Files are downloaded to `assets/video_clips/`. If a query returns no results, the complementary video is used as fallback.

### Step 5 — Composing
`Composer.render_all_scenes()` processes every scene:

1. **Trim video_A** to `audio_duration / 2` seconds.
2. **Trim video_B** to `audio_duration / 2` seconds.
3. **Avatar injection** — with a configurable probability, one non‑hook/non‑outro scene has its visuals replaced by the avatar loop.
4. **Concatenate** A‑half + B‑half into a single scene MP4.

### Step 6 — Final Assembly
`Composer.concatenate_with_transitions()` merges all scene MP4s with randomly selected `xfade` transitions (fade, slide left/right, fadeblack, etc.). The final output is written to `assets/final/final_short.mp4` with H.264 encoding, `yuv420p` pixel format, and `faststart` flag for maximum compatibility (no green/ black frames on Windows).

```
INPUT: topic string
       │
       ▼
  ┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌─────────────┐    ┌───────────┐
  │ 1. Topic  │───→│ 2. Script    │───→│ 3. Audio  │───→│ 4. Stock    │───→│ 5. Compose│
  │ Selection │    │ Generation   │    │  TTS      │    │ Footage     │    │ + Trans.  │
  └──────────┘    └──────────────┘    └──────────┘    └─────────────┘    └─────┬─────┘
                                                                               │
                                                                               ▼
                                                                       ┌──────────────┐
                                                                       │ final_short   │
                                                                       │ .mp4          │
                                                                       └──────────────┘
```

---

## Quick Start

### Prerequisites

| Requirement  | Verification                      |
|-------------  |-----------------------------------|
| Python 3.10+  | `python --version`                |
| FFmpeg        | `ffmpeg -version`                 |
| Git           | `git --version`                   |

**Installing FFmpeg:**
- **Windows:** `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg` (Debian/Ubuntu)

### 1. Clone

```bash
git clone https://github.com/rahulcvwebsitehosting/AutoReels-Ai.git
cd AutoReels-Ai
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example file:

```bash
cp .env.example .env
```

Edit `.env` with your API keys. At minimum you need:

```ini
# Pick one LLM provider
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Pexels API key (required for stock footage)
PEXELS_API_KEY=your_pexels_api_key_here
```

### 4. Set Up Avatar (Optional)

If you want an avatar/mascot to appear in a random scene:

```
assets/avatar/avatars.mp4
```

### 5. Run

```bash
python main.py
```

The pipeline will:
1. Select a trending topic from the LLM
2. Generate a structured JSON script
3. Produce per‑scene voiceover files
4. Download matching stock footage from Pexels
5. Render and stitch everything into `assets/final/final_short.mp4`

---

## LLM Provider Configuration

Set `LLM_PROVIDER` in `.env` to one of the following values. Each provider has its own `*_API_KEY` and optional `*_MODEL` override.

| `LLM_PROVIDER=` | API Key Env Var       | Model Env Var         | Default Model              |
|-----------------|-----------------------|-----------------------|----------------------------|
| `gemini`        | `GEMINI_API_KEY`      | `GEMINI_MODEL`        | `gemini-2.0-flash`         |
| `openai`        | `OPENAI_API_KEY`      | `OPENAI_MODEL`        | `gpt-4o-mini`              |
| `openrouter`    | `OPENROUTER_API_KEY`  | `OPENROUTER_MODEL`    | `openrouter/auto`          |
| `groq`          | `GROQ_API_KEY`        | `GROQ_MODEL`          | `llama-3.3-70b-versatile`  |
| `anthropic`     | `ANTHROPIC_API_KEY`   | `ANTHROPIC_MODEL`     | `claude-3-5-sonnet-latest` |
| `ollama`        | `OLLAMA_API_KEY`      | `OLLAMA_MODEL`        | `llama3.1`                 |
| `opencode-zen`  | `OPENCODE_ZEN_API_KEY`| `OPENCODE_ZEN_MODEL`  | `openrouter/auto`          |

**Example — OpenRouter:**

```ini
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

**Local Ollama:**

```ini
LLM_PROVIDER=ollama
OLLAMA_API_KEY=anything   # not checked when using local
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
```

If `LLM_PROVIDER` is not set (or empty), the program displays an interactive numbered menu at startup so you can pick a provider per run.

---

## Project Structure

```
AutoReels-Ai/
│
├── main.py                        # Entry point — runs the full pipeline
├── requirements.txt               # Python package dependencies
├── .env.example                   # Template for environment variables
│
├── modules/
│   ├── llm.py                     # LLM provider abstraction layer (7 providers)
│   ├── brain.py                   # Topic selection + script generation
│   ├── audio.py                   # edge-tts voiceover per scene
│   ├── asset_manager.py           # Pexels stock footage search & download
│   └── composer.py                # FFmpeg scene assembly + transitions
│
└── assets/
    ├── audio_clips/               # Generated TTS audio files
    ├── video_clips/               # Downloaded stock footage
    ├── temp/                      # Intermediate processing clips
    ├── final/                     # Final rendered output
    └── avatar/
        └── avatars.mp4            # (Optional) avatar video
```

---

## Module Reference

### `modules/llm.py` — Provider Abstraction Layer

Defines a uniform `LLMClient` interface with one method: `generate(prompt, max_tokens) -> str`. The factory `get_llm_client()` selects the active provider from the `LLM_PROVIDER` env var (or interactive menu) and returns the correct client:
- **Gemini** → `GeminiClient` (native `google-genai` SDK)
- **Anthropic** → `AnthropicClient` (native `anthropic` SDK)
- **OpenAI, OpenRouter, Groq, Ollama, OpenCode Zen** → `OpenAICompatibleClient` (shared `/chat/completions` code path, differing only in `base_url`, `api_key`, and `model`)

### `modules/brain.py` — Scriptwriter

- `get_trending_topic()` → LLM prompt returning a single topic string.
- `generate_script(topic)` → LLM prompt returning a JSON array of scenes with `text`, `visual_1`, `visual_2`, and `mood`. Response is cleaned of markdown fences and parsed with `json.loads`.

### `modules/audio.py` — Voiceover Engine

- Reads the script's scene list, calls `edge-tts` per scene, saves `.mp3` files to `assets/audio_clips/`.
- Uses `mutagen` to read each file's duration and attaches it to the scene dict for video timing.

### `modules/asset_manager.py` — Stock Footage Sourcing

- Takes `visual_1` and `visual_2` per scene, queries Pexels for portrait videos.
- Downloads to `assets/video_clips/<scene_id>_a.mp4` and `_b.mp4`.
- Falls back to the other video if one query returns nothing.

### `modules/composer.py` — Video Editor

- **Per scene:** trims each video half to `audio_duration / 2`, optionally injects avatar, concatenates A+B.
- **Post processing:** merges all scenes with `xfade` transitions, writes final MP4 with H.264 `yuv420p` `faststart`.

---

## Troubleshooting

| Symptom                          | Likely Cause                        | Fix                                              |
|----------------------------------|--------------------------------------|--------------------------------------------------|
| `ModuleNotFoundError`            | Missing dependency                   | `pip install -r requirements.txt`                |
| `KeyError: GEMINI_API_KEY`       | `.env` missing or incomplete         | Copy `.env.example → .env`, fill keys           |
| `FFmpeg ... not found`           | FFmpeg not in PATH                   | Install FFmpeg, verify with `ffmpeg -version`   |
| Green / black video on Windows   | Wrong pixel format                   | Composer forces `yuv420p` — open with VLC       |
| `0x80004005` playback error      | Windows Media Player codec issue     | Use VLC, MPC‑HC, or your browser                |
| Avatar not appearing             | Missing avatar file                  | Place video at `assets/avatar/avatars.mp4`      |
| Audio silent or no speech        | `edge-tts` network / install issue   | Check internet, reinstall `edge-tts`            |

---

## License

Released under the MIT License. See [LICENSE](LICENSE).

<p align="center">
  Made with ❤️ by
  <a href="https://www.linkedin.com/in/rahulshyamcivil/">Rahul Shyam Civil</a>
  ·
  <a href="https://x.com/RahulShyamCv">X</a>
  ·
  <a href="https://threads.com/@RahulCvJPS">Threads</a>
  <br>
  If this project helps you, a star or a share means everything. ❤️
</p>
