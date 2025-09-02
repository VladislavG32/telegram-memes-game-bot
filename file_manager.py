import os
import json
import random
from config import Config

class FileManager:
    def __init__(self):
        print("=== FileManager инициализация ===")
        self.memes_dir = Config.MEMES_DIR
        self.situations_file = Config.SITUATIONS_FILE
        self.used_memes_file = Config.USED_MEMES_FILE
        
        print(f"MEMES_DIR: {self.memes_dir}")
        print(f"SITUATIONS_FILE: {self.situations_file}")
        print(f"USED_MEMES_FILE: {self.used_memes_file}")
        
        self._ensure_directories()
        print("=== FileManager инициализирован успешно ===")
    
    def _ensure_directories(self):
        os.makedirs(self.memes_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.used_memes_file), exist_ok=True)
        
        if not os.path.exists(self.used_memes_file):
            with open(self.used_memes_file, 'w', encoding='utf-8') as f:
                json.dump({"used_memes": []}, f, ensure_ascii=False)
    
    def get_all_memes(self):
        memes = []
        if not os.path.exists(self.memes_dir):
            return memes
            
        for file in os.listdir(self.memes_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov', '.avi')):
                memes.append({
                    'filename': file,
                    'path': os.path.join(self.memes_dir, file)
                })
        return memes
    
    def get_random_memes(self, count=6):
        all_memes = self.get_all_memes()
        if not all_memes:
            # Создаем заглушки если нет мемов
            stub_memes = []
            for i in range(count):
                stub_memes.append({
                    'filename': f'stub_{i}.jpg', 
                    'path': os.path.join(os.path.dirname(__file__), 'assets', f'stub_{i}.jpg')
                })
            return stub_memes
            
        used_memes = self._load_used_memes()
        available_memes = [m for m in all_memes if m['filename'] not in used_memes]
        
        # Если доступных мемов меньше нужного количества, сбрасываем использованные
        if len(available_memes) < count:
            print("⚠️ Доступные мемы закончились, сбрасываем список использованных")
            self.reset_used_memes()
            available_memes = all_memes
        
        # Если все равно недостаточно мемов, используем повторно
        if len(available_memes) < count:
            needed = count - len(available_memes)
            additional_memes = random.sample(all_memes, min(needed, len(all_memes)))
            available_memes.extend(additional_memes)
        
        selected_memes = random.sample(available_memes, min(count, len(available_memes)))
        self._mark_memes_as_used([m['filename'] for m in selected_memes])
        
        return selected_memes
    
    def get_all_situations(self):
        if not os.path.exists(self.situations_file):
            os.makedirs(os.path.dirname(self.situations_file), exist_ok=True)
            with open(self.situations_file, 'w', encoding='utf-8') as f:
                f.write("Когда ты опоздал на работу, но начальник тоже\n")
                f.write("Когда пытаешься объяснить IT-специалисту, что 'у меня ничего не работает'\n")
            return [
                "Когда ты опоздал на работу, но начальник тоже",
                "Когда пытаешься объяснить IT-специалисту, что 'у меня ничего не работает'"
            ]
        
        with open(self.situations_file, 'r', encoding='utf-8') as f:
            situations = [line.strip() for line in f if line.strip()]
        return situations
    
    def get_random_situations(self, count=10):
        situations = self.get_all_situations()
        if not situations:
            return ["Пример ситуации: Когда кофе закончился"]
        return random.sample(situations, min(count, len(situations)))
    
    def _load_used_memes(self):
        try:
            with open(self.used_memes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('used_memes', [])
        except Exception as e:
            print(f"❌ Ошибка загрузки used_memes: {e}")
            return []
    
    def _mark_memes_as_used(self, memes):
        try:
            used_memes = self._load_used_memes()
            used_memes.extend(memes)
            used_memes = list(set(used_memes))
            
            with open(self.used_memes_file, 'w', encoding='utf-8') as f:
                json.dump({"used_memes": used_memes}, f, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Ошибка сохранения used_memes: {e}")
    
    def reset_used_memes(self):
        try:
            with open(self.used_memes_file, 'w', encoding='utf-8') as f:
                json.dump({"used_memes": []}, f, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Ошибка сброса used_memes: {e}")
    
    def add_situation(self, situation):
        """Добавить новую ситуацию в файл"""
        try:
            with open(self.situations_file, 'a', encoding='utf-8') as f:
                f.write(situation + '\n')
            return True
        except Exception as e:
            print(f"❌ Ошибка добавления ситуации: {e}")
            return False
