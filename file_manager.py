import os
import json
import random
from config import Config

class FileManager:
    def __init__(self):
        self.memes_dir = Config.MEMES_DIR
        self.situations_file = Config.SITUATIONS_FILE
        self.used_memes_file = Config.USED_MEMES_FILE
        self._ensure_directories()

    def _ensure_directories(self):
        os.makedirs(self.memes_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.used_memes_file), exist_ok=True)

        if not os.path.exists(self.used_memes_file):
            with open(self.used_memes_file, 'w') as f:
                json.dump({"used_memes": []}, f)

    def get_all_memes(self):
        memes = []
        if not os.path.exists(self.memes_dir):
            return memes

        for file in os.listdir(self.memes_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov')):
                memes.append({
                    'filename': file,
                    'path': os.path.join(self.memes_dir, file)
                })
        return memes

    def get_random_memes(self, count=6):
        all_memes = self.get_all_memes()
        if not all_memes:
            return []

        used_memes = self._load_used_memes()
        available_memes = [m for m in all_memes if m['filename'] not in used_memes]

        if len(available_memes) < count:
            used_memes = []
            available_memes = all_memes

        selected_memes = random.sample(available_memes, min(count, len(available_memes)))
        self._mark_memes_as_used([m['filename'] for m in selected_memes])

        return selected_memes

    def get_all_situations(self):
        if not os.path.exists(self.situations_file):

            os.makedirs(os.path.dirname(self.situations_file), exist_ok=True)
            with open(self.situations_file, 'w', encoding='utf-8') as f:
                f.write("")
            return []

        with open(self.situations_file, 'r', encoding='utf-8') as f:
            situations = [line.strip() for line in f if line.strip()]
        return situations

    def get_random_situations(self, count=10):
        situations = self.get_all_situations()
        if not situations:
            return []
        return random.sample(situations, min(count, len(situations)))

    def _load_used_memes(self):
        try:
            with open(self.used_memes_file, 'r') as f:
                data = json.load(f)
                return data.get('used_memes', [])
            except:
                return []

        def _mark_memes_as_used(self, memes):
            used_memes = self._load_used_memes()
            used_memes.extend(memes)
            used_memes = list(set(used_memes))

            with open(self.used_memes_file, 'w') as f:
                json.dump({"used_memes": used_memes}, f)

        def reset_used_memes(self):
            with open(self.used_memes_file, 'w') as f:
                json.dump({"used_memes": []}, f)