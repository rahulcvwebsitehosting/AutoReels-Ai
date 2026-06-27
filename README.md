# AutoReels Ai

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/FFmpeg-Required-red?style=for-the-badge&logo=ffmpeg" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
  <img src="https://komarev.com/ghpvc/?username=AutoReels-Ai&style=for-the-badge&color=blue" />
  <img src="https://img.shields.io/badge/LLM-7_Providers-orange?style=for-the-badge" />
</p>

<p align="center">
  <b>Open-source terminal app that generates a fully-edited YouTube Short from a topic —<br>scriptwriting, voiceover, stock footage, captions, transitions, all automated.</b>
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

## What It Does

You type a topic (or paste a script). AutoReels Ai handles the rest:

1. **Writes or refines a script** using one of 7 LLM providers
2. **Generates voiceover** with Microsoft Edge TTS
3. **Downloads stock footage** from Pexels matching each scene
4. **Injects an avatar** (optional, your own video) in middle scenes
5. **Burns captions** into every scene automatically
6. **Stitches** everything with crossfade transitions
7. **Outputs** a finished `final_short.mp4`

---

## Quick Start

### Prerequisites

| Tool | Check |
|------|-------|
| Python 3.10+ | `python --version` |
| FFmpeg | `ffmpeg -version` |

**FFmpeg install:**
- **Windows:** `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

### 1. Clone

```bash
git clone https://github.com/rahulcvwebsitehosting/AutoReels-Ai.git
cd AutoReels-Ai
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env`. At minimum you need:

```ini
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
PEXELS_API_KEY=your_pexels_api_key
```

### 4. (Optional) Add Avatar Video

Place one or more `.mp4` files in `assets/avatar/`. The program will list them at startup for you to pick (or skip). Real human footage works best.

### 5. Run

```bash
python main.py
```

The terminal will guide you through each choice interactively.

---

## Interactive Startup Walkthrough

When you run `python main.py`, you see this flow:

### Provider Selection

If you have API keys for multiple providers configured in `.env`, you pick one:

```
[PROVIDER] Multiple providers have API keys configured. Pick one:
  1. gemini (gemini-2.0-flash)
  2. ollama (minimax-m3)
Enter choice [1-2]:
```

If only one provider has a valid key, it is auto-selected. If none are set, you get an interactive menu of all 7.

### Topic

```
[TOPIC] What should the reel be about?
  (Press Enter to let AI auto-pick a trending topic)
Topic: _
```

Type your topic, or press Enter to let the AI choose one.

### Script Mode

```
[SCRIPT] Script mode:
  1. AI auto-write the script
  2. I'll write the script myself
Enter choice [1-2] (default 1):
```

**Option 1** — AI generates an 8-scene script from your topic.

**Option 2** — You provide content:
- Paste plain text directly in the terminal (no JSON needed)
- Or load from a `.txt` file on your computer
- Then choose: **Refine** (AI keeps your story, fixes grammar and visuals) or **Expand** (AI uses your ideas as inspiration for a new script)

If your script is long, the AI condenses it to fit ~60 seconds. You confirm before proceeding.

### Avatar Selection

```
[AVATAR] Choose an avatar for the video:
  1. presenter_interview.mp4
  2. reaction_clip.mp4
  3. No avatar (skip)
Enter choice [1-3] (default random):
```

Press Enter for a random pick, or choose "No avatar" for stock footage only.

### Output

The final video is saved to `assets/final/final_short.mp4`.

---

## Features

| Feature | Detail |
|---------|--------|
| **7 LLM providers** | Gemini, OpenAI, OpenRouter, Groq, Anthropic, Ollama (cloud + local), OpenCode Zen |
| **Interactive startup** | Provider, topic, script mode all chosen via terminal prompts |
| **Custom script input** | Paste text or load `.txt` file — no JSON knowledge needed |
| **Script refinement** | AI reads your script, fixes grammar, restructures, generates sourced claims |
| **Source-backed narration** | AI includes source attribution in script text (e.g. "Amnesty International reported...") |
| **Smart condensing** | Long documents are summarized to fit ~60-second Short format |
| **Dual-visual A/B split** | Two different stock videos per scene, switched mid-sentence for retention |
| **Multi-avatar support** | Drop multiple `.mp4` files in `assets/avatar/`, pick one at startup or skip |
| **Auto-captions** | Every scene gets burned-in SRT subtitles with semi-transparent background |
| **Crossfade transitions** | Random xfade effects between scenes |
| **Windows compatible** | `yuv420p` + `faststart` flags prevent green/black frames |
| **Auto topic selection** | Press Enter at topic prompt to let AI pick a trending topic |

---

## LLM Provider Configuration

| `LLM_PROVIDER=` | API Key Env Var | Model Env Var | Default Model |
|---|---|---|---|
| `gemini` | `GEMINI_API_KEY` | `GEMINI_MODEL` | `gemini-2.0-flash` |
| `openai` | `OPENAI_API_KEY` | `OPENAI_MODEL` | `gpt-4o-mini` |
| `openrouter` | `OPENROUTER_API_KEY` | `OPENROUTER_MODEL` | `openrouter/auto` |
| `groq` | `GROQ_API_KEY` | `GROQ_MODEL` | `llama-3.3-70b-versatile` |
| `anthropic` | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` | `claude-3-5-sonnet-latest` |
| `ollama` | `OLLAMA_API_KEY` | `OLLAMA_MODEL` | `llama3.1` |
| `opencode-zen` | `OPENCODE_ZEN_API_KEY` | `OPENCODE_ZEN_MODEL` | `openrouter/auto` |

### Ollama Cloud Example

```ini
LLM_PROVIDER=ollama
OLLAMA_API_KEY=sk-...
OLLAMA_MODEL=minimax-m3
OLLAMA_BASE_URL=https://ollama.com/v1
```

### Local Ollama Example

```ini
LLM_PROVIDER=ollama
OLLAMA_API_KEY=anything
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
```

---

## Project Structure

```
AutoReels-Ai/
├── main.py                        # Entry point — interactive startup + pipeline orchestration
├── requirements.txt               # Python dependencies
├── .env.example                   # API key template
│
├── modules/
│   ├── llm.py                     # 7 LLM providers behind a unified interface
│   ├── brain.py                   # Script generation, refinement, expansion
│   ├── audio.py                   # edge-tts voiceover per scene
│   ├── asset_manager.py           # Pexels stock footage search + download
│   └── composer.py                # FFmpeg scene editing, captions, transitions
│
└── assets/
    ├── audio_clips/               # Generated TTS audio
    ├── video_clips/               # Downloaded stock footage
    ├── temp/                      # Intermediate processing files
    ├── final/                     # Final rendered final_short.mp4
    └── avatar/                    # Drop your avatar .mp4 files here
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| API key error | Copy `.env.example` to `.env` and fill keys |
| `ffmpeg not found` | Install FFmpeg, verify with `ffmpeg -version` |
| Green/black video on Windows | Open with VLC — `yuv420p` is forced for compatibility |
| Avatar not appearing | Place `.mp4` files in `assets/avatar/` |
| Audio silent | Check internet connection, `edge-tts` requires network |

---

## Pipeline Architecture

```
INPUT: topic string
       |
       v
  +----------+    +--------------+    +---------+    +-------------+    +-----------+
  | 1. Topic  |--->| 2. Script    |--->| 3. Audio |--->| 4. Stock    |--->| 5. Compose|
  | Selection |    | Generation   |    | TTS      |    | Footage     |    | + Captions|
  +----------+    +--------------+    +---------+    +-------------+    +-----+-----+
                                                                              |
                                                                              v
                                                                      +---------------+
                                                                      | final_short    |
                                                                      | .mp4           |
                                                                      +---------------+
```

---

## License

MIT License. See [LICENSE](LICENSE).

<p align="center">
  Made with ❤️ by
  <a href="https://www.linkedin.com/in/rahulshyamcivil/">Rahul Shyam Civil</a>
  ·
  <a href="https://x.com/RahulShyamCv">X</a>
  ·
  <a href="https://threads.com/@RahulCvJPS">Threads</a>
  <br>
  Open-source and free. If this helps you, a star or share means everything.
</p>
