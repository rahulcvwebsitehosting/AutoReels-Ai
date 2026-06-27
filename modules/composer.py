import os
import random
import subprocess
import ffmpeg


class Composer:
    def __init__(self):
        self.temp_dir = os.path.join(os.getcwd(), "assets", "temp")
        self.final_dir = os.path.join(os.getcwd(), "assets", "final")
        self.avatar_dir = os.path.join(os.getcwd(), "assets", "avatar")
        
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)
        self.transitions = ['fade', 'diagbr', 'diagtl']

    @staticmethod
    def list_avatars():
        """Scan avatar directory and return list of video file paths."""
        avatar_dir = os.path.join(os.getcwd(), "assets", "avatar")
        if not os.path.isdir(avatar_dir):
            return []
        valid_exts = (".mp4", ".mov", ".avi", ".mkv", ".webm")
        files = []
        for f in os.listdir(avatar_dir):
            if f.lower().endswith(valid_exts):
                files.append(os.path.join(avatar_dir, f))
        return sorted(files)

    @staticmethod
    def pick_avatar(choice=None):
        """Return an avatar path. If choice is None, pick random. If 'none', return None."""
        avatars = Composer.list_avatars()
        if not avatars:
            return None
        if choice is None:
            return random.choice(avatars)
        if 0 <= choice < len(avatars):
            return avatars[choice]
        return None

    def get_duration(self, filepath):
        try:
            probe = ffmpeg.probe(filepath)
            return float(probe['format']['duration'])
        except:
            return 0.0

    @staticmethod
    def _write_srt(scene_text, duration, output_path):
        words = scene_text.split()
        if not words:
            return
        chunk_size = 5
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i+chunk_size]))
        n = len(chunks)
        per = duration / max(n, 1)
        with open(output_path, "w", encoding="utf-8") as f:
            for idx, chunk in enumerate(chunks):
                start = idx * per
                end = min((idx + 1) * per, duration)
                if end - start < 0.3:
                    end = start + 0.3
                hs, ms, ss, mms = int(start//3600), int((start%3600)//60), int(start%60), int((start-int(start))*1000)
                he, me, se, mme = int(end//3600), int((end%3600)//60), int(end%60), int((end-int(end))*1000)
                f.write(f"{idx+1}\n{hs:02d}:{ms:02d}:{ss:02d},{mms:03d} --> {he:02d}:{me:02d}:{se:02d},{mme:03d}\n{chunk}\n\n")

    def process_scene(self, scene, video_pair, is_avatar=False):
        scene_id = scene['id']
        audio_path = scene['audio_path']
        total_duration = scene['duration']
        scene_text = scene['text']
        output_path = os.path.join(self.temp_dir, f"scene_{scene_id}.mp4")
        srt_path = os.path.join(self.temp_dir, f"scene_{scene_id}.srt")
        subtitled_path = os.path.join(self.temp_dir, f"scene_{scene_id}_subs.mp4")

        self._write_srt(scene_text, total_duration, srt_path)

        try:
            input_audio = ffmpeg.input(audio_path)

            if is_avatar:
                print(f"   [SCENE {scene_id}] Avatar mode")
                video_stream = (
                    ffmpeg.input(video_pair[0], stream_loop=-1)
                    .trim(duration=total_duration + 0.5)
                    .setpts('PTS-STARTPTS')
                    .filter('crop', 'iw', 'ih-150', 0, 0)
                    .filter('scale', 1080, 1920, force_original_aspect_ratio='increase')
                    .filter('crop', 1080, 1920)
                    .filter('fps', fps=30, round='up')
                )
            else:
                print(f"   [SCENE {scene_id}] A/B split mode")
                path_a, path_b = video_pair
                duration_a = total_duration / 2
                duration_b = (total_duration / 2) + 0.5

                stream_a = (
                    ffmpeg.input(path_a, stream_loop=-1)
                    .trim(duration=duration_a)
                    .setpts('PTS-STARTPTS')
                    .filter('scale', 1080, 1920).filter('crop', 1080, 1920)
                    .filter('fps', fps=30, round='up')
                )
                stream_b = (
                    ffmpeg.input(path_b, stream_loop=-1)
                    .trim(duration=duration_b)
                    .setpts('PTS-STARTPTS')
                    .filter('scale', 1080, 1920).filter('crop', 1080, 1920)
                    .filter('fps', fps=30, round='up')
                )
                video_stream = ffmpeg.concat(stream_a, stream_b, v=1, a=0)

            # Render base scene
            base_path = os.path.join(self.temp_dir, f"scene_{scene_id}_base.mp4")
            (
                ffmpeg.output(video_stream, input_audio, base_path,
                              vcodec='libx264', acodec='aac',
                              pix_fmt='yuv420p', shortest=None)
                .run(overwrite_output=True, quiet=True)
            )

            # Overlay subtitles (use just the filename + cwd to avoid Windows path colon issue)
            srt_filename = f"scene_{scene_id}.srt"
            style = 'Alignment=2,FontSize=24,FontName=Arial,PrimaryColour=&HFFFFFF,BackColour=&H80000000,Outline=1,Shadow=0'
            vf = f'subtitles={srt_filename}:force_style={style}'.replace(',', '\\,')
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', base_path,
                '-vf', vf,
                '-c:v', 'libx264', '-c:a', 'copy', '-pix_fmt', 'yuv420p',
                subtitled_path
            ], capture_output=True, text=True, cwd=self.temp_dir)
            if result.returncode != 0:
                raise RuntimeError(result.stderr[:500])

            return subtitled_path

        except ffmpeg.Error as e:
            error_log = e.stderr.decode('utf8') if e.stderr else str(e)
            print(f"[ERROR] Render fail scene {scene_id}: {error_log[:500]}")
            return None
        except Exception as e:
            print(f"[ERROR] Render fail scene {scene_id}: {e}")
            return None

    def render_all_scenes(self, script_data, video_pairs, avatar_path=None):
        rendered_paths = []
        avatar_indices = []

        if avatar_path and len(script_data) >= 4:
            valid_range = list(range(1, len(script_data) - 1))
            count_to_pick = 2 if len(valid_range) >= 2 else 1
            avatar_indices = random.sample(valid_range, count_to_pick)
            avatar_indices.sort()
            print(f"[AVATAR] Injecting at scenes: {[i+1 for i in avatar_indices]}")

        for i, scene in enumerate(script_data):
            current_pair = video_pairs[i]
            is_avatar = False

            if i in avatar_indices and avatar_path:
                current_pair = (avatar_path, None)
                is_avatar = True
            elif current_pair is None:
                continue

            output_path = self.process_scene(scene, current_pair, is_avatar)
            if output_path:
                rendered_paths.append(output_path)

        return rendered_paths

    def concatenate_with_transitions(self, video_paths, output_filename="final_short.mp4"):
        """
        Stitches rendered scenes together.
        INCLUDES FIXES FOR: Windows 0x80004005 Error & Playback Issues.
        """
        print("🎬 Stitching final video...")
        output_path = os.path.join(self.final_dir, output_filename)
        
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                print("⚠️ Warning: Could not delete old file. It might be open in a player.")

        if not video_paths:
            return None

        input1 = ffmpeg.input(video_paths[0])
        v_stream = input1.video
        a_stream = input1.audio
        
        current_dur = self.get_duration(video_paths[0])

        for i in range(1, len(video_paths)):
            next_clip = ffmpeg.input(video_paths[i])
            next_dur = self.get_duration(video_paths[i])
            
            trans_dur = 0.5
            offset = current_dur - trans_dur
            
            effect = random.choice(self.transitions)
            print(f"   ✨ Transition {i}: '{effect}' at {offset:.2f}s")

            v_stream = ffmpeg.filter(
                [v_stream, next_clip.video], 
                'xfade', 
                transition=effect, 
                duration=trans_dur, 
                offset=offset
            )
            
            a_stream = ffmpeg.filter(
                [a_stream, next_clip.audio], 
                'acrossfade', 
                d=trans_dur
            )
            
            current_dur = (current_dur + next_dur) - trans_dur

        try:
            runner = ffmpeg.output(
                v_stream, 
                a_stream, 
                output_path, 
                vcodec='libx264',   # Standard H.264 video
                acodec='aac',       # Standard AAC audio
                pix_fmt='yuv420p',  # 🔥 FIX 1: Windows compatibility
                movflags='faststart', # 🔥 FIX 2: Corruption fix
                preset='medium' 
            )
            
            runner.run(overwrite_output=True, quiet=False)
            
            print(f"✅ FINAL VIDEO SAVED: {output_path}")
            return output_path

        except ffmpeg.Error as e:
            error_log = e.stderr.decode('utf8') if e.stderr else str(e)
            print(f"❌ Stitching Error: {error_log}")
            return None