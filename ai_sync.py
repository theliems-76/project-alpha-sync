import os
import json
import time
import hashlib
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv

load_dotenv()

class GeminiKeyManager:
    def __init__(self):
        api_keys_env = os.getenv("API_KEY") or os.getenv("GEMINI_API_KEYS")
        if not api_keys_env:
            raise ValueError("API_KEY or GEMINI_API_KEYS environment variable is not set.")
        
        self.keys = [k.strip().strip('"').strip("'") for k in api_keys_env.split(",") if k.strip()]
        self.current_index = 0
            
        self._configure_current_key()

    def _configure_current_key(self):
        genai.configure(api_key=self.keys[self.current_index])
        
    def rotate_key(self):
        self.current_index = (self.current_index + 1) % len(self.keys)
        self._configure_current_key()

class AISyncManager:
    def __init__(self, state_file="sync_state.json"):
        self.state_file = state_file
        self.key_manager = GeminiKeyManager()
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_state(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=4)

    def _get_file_hash(self, file_path):
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def upload_with_retry(self, file_path, retries=10):
        for attempt in range(retries):
            try:
                return genai.upload_file(path=file_path, display_name=os.path.basename(file_path), mime_type="text/markdown")
            except ResourceExhausted:
                if attempt < retries - 1:
                    self.key_manager.rotate_key()
                    time.sleep(2)
                else:
                    raise
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(5)
                else:
                    raise e

    def delete_remote_file(self, file_id, retries=5):
        for attempt in range(retries):
            try:
                genai.delete_file(file_id)
                return
            except ResourceExhausted:
                if attempt < retries - 1:
                    self.key_manager.rotate_key()
                    time.sleep(2)
                else:
                    raise
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(3)
                else:
                    pass

    def sync_directory(self, docs_dir="docs"):
        added = 0
        updated = 0
        skipped = 0

        for filename in os.listdir(docs_dir):
            if not filename.endswith(".md"):
                continue
                
            file_path = os.path.join(docs_dir, filename)
            file_hash = self._get_file_hash(file_path)
            
            if filename in self.state:
                if self.state[filename]["hash"] == file_hash:
                    skipped += 1
                    continue
                
                old_file_id = self.state[filename].get("cloud_id")
                if old_file_id:
                    self.delete_remote_file(old_file_id)
                
                uploaded = self.upload_with_retry(file_path)
                self.state[filename] = {"hash": file_hash, "cloud_id": uploaded.name}
                updated += 1
            else:
                uploaded = self.upload_with_retry(file_path)
                self.state[filename] = {"hash": file_hash, "cloud_id": uploaded.name}
                added += 1

            self._save_state()

        return added, updated, skipped

if __name__ == "__main__":
    sync_manager = AISyncManager()
    a, u, s = sync_manager.sync_directory()
    print(f"Sync complete. Added: {a}, Updated: {u}, Skipped: {s}")
