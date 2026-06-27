import asyncio
from modules.brain import ContentBrain
from modules.asset_manager import AssetManager
from modules.audio import AudioEngine
from modules.composer import Composer
from modules.llm import get_configured_providers, PROVIDERS
import os
import shutil


def clean_cache():
    folders_to_clean = [
        os.path.join(os.getcwd(), "assets", "audio_clips"),
        os.path.join(os.getcwd(), "assets", "video_clips"),
        os.path.join(os.getcwd(), "assets", "temp"),
    ]
    for folder in folders_to_clean:
        if not os.path.exists(folder):
            continue
        if "assets" not in folder:
            continue
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"   [ERROR] Failed to delete {file_path}. Reason: {e}")
    print("[CLEAN] Workspace clean!")


def pick_provider():
    configured = get_configured_providers()

    if len(configured) == 1:
        pid = configured[0]
        print(f"[PROVIDER] Using {pid} (only configured provider)")
        return pid

    if len(configured) > 1:
        print()
        print("[PROVIDER] Multiple providers have API keys configured. Pick one:")
        for i, pid in enumerate(configured, start=1):
            cfg = PROVIDERS[pid]
            model = os.getenv(cfg["model_env"], cfg["default"])
            print(f"  {i}. {pid} ({model})")
        while True:
            choice = input(f"Enter choice [1-{len(configured)}]: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(configured):
                return configured[int(choice) - 1]
            print("   Invalid choice, try again.")

    return None


def get_topic():
    print()
    print("[TOPIC] What should the reel be about?")
    print("  (Press Enter to let AI auto-pick a trending topic)")
    topic = input("Topic: ").strip()
    return topic if topic else None


def get_script_mode():
    print()
    print("[SCRIPT] Script mode:")
    print("  1. AI auto-write the script")
    print("  2. I'll write the script myself")
    while True:
        choice = input("Enter choice [1-2] (default 1): ").strip()
        if not choice or choice == "1":
            return "auto"
        if choice == "2":
            return "manual"
        print("   Invalid choice, try again.")


def get_custom_script_input():
    print()
    print("[SCRIPT] How would you like to provide your script?")
    print("  1. Type or paste the script directly")
    print("  2. Load from a .txt file on your computer")
    while True:
        choice = input("Enter choice [1-2] (default 1): ").strip()
        if not choice or choice == "1":
            print()
            print("[SCRIPT] Paste your script below (plain text, no JSON needed).")
            print("  Type '---' on a new line when done:")
            print()
            lines = []
            while True:
                line = input()
                if line.strip() == "---":
                    break
                lines.append(line)
            return "\n".join(lines)
        if choice == "2":
            print()
            path = input("Enter full path to your .txt file: ").strip()
            if not os.path.exists(path):
                print(f"[ERROR] File not found: {path}")
                return None
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        print("   Invalid choice, try again.")


async def main():
    print("AutoReels Ai")
    print("-" * 40)

    provider_id = pick_provider()
    brain = ContentBrain(provider_id)

    topic = get_topic()
    if topic is None:
        topic = brain.get_trending_topic()

    mode = get_script_mode()

    if mode == "manual":
        raw = get_custom_script_input()
        if raw is None:
            return
        if not raw.strip():
            print("[ERROR] No script content provided. Aborting.")
            return
        print()
        print("[SCRIPT] How should AI handle your script?")
        print("  1. AI refines it — keeps your story, fixes grammar/format/visuals")
        print("  2. AI expands it — uses your ideas as inspiration for a new script")
        while True:
            choice = input("Enter choice [1-2] (default 1): ").strip()
            if not choice or choice == "1":
                script = brain.refine_script(raw, topic)
                if script is None:
                    print("[ERROR] Script refinement failed. Aborting.")
                    return
                break
            if choice == "2":
                script = brain.expand_script(raw, topic)
                if script is None:
                    print("[ERROR] Script expansion failed. Aborting.")
                    return
                break
            print("   Invalid choice, try again.")
    else:
        try:
            script = brain.generate_script(topic)
        except Exception as e:
            print(f"[ERROR] Brain Error: {e}")
            return

    if not script:
        print("[ERROR] Script generation failed.")
        return

    audio_engine = AudioEngine()
    try:
        script = await audio_engine.process_script(script)
    except Exception as e:
        print(f"[ERROR] Audio Error: {e}")
        return

    asset_manager = AssetManager()
    assets_map = asset_manager.get_videos(script)

    composer = Composer()
    final_scene_paths = composer.render_all_scenes(script, assets_map)

    if final_scene_paths:
        composer.concatenate_with_transitions(final_scene_paths)
        clean_cache()
    else:
        print("[ERROR] Failed to generate any scenes.")


if __name__ == "__main__":
    asyncio.run(main())
