import requests
from bs4 import BeautifulSoup
from pypresence import Presence
import re
import json
import sys
import os

# Discord Client ID for Nintendo Switch 2
CLIENT_ID = '1456107266766798971'

class SwitchRPCBackend:
    def __init__(self):
        self.rpc = None
        self.connected = False
        self.game_db = []
        self._load_game_db()
        try:
            self.rpc = Presence(CLIENT_ID)
            self.rpc.connect()
            self.connected = True
            print("Connected to Discord RPC")
        except Exception as e:
            print(f"Failed to connect to Discord RPC: {e}")

    def reload_db(self):
        self._load_game_db()
        return self.game_db

    def _load_game_db(self):
        # Determine path safely for EXE
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.abspath(".")
        
        json_path = os.path.join(base_path, 'games.json')

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.game_db = json.load(f)
            print(f"Loaded {len(self.game_db)} games from local DB.")
        except Exception as e:
            print(f"Could not load games.json: {e}")

    def get_game_db(self):
        """Returns the full game database list."""
        return self.game_db

    def update_presence(self, state, details, large_image, large_text, small_image, small_text):
        if not self.connected or not self.rpc:
            try:
                self.rpc = Presence(CLIENT_ID)
                self.rpc.connect()
                self.connected = True
            except Exception as e:
                print(f"Reconnection failed: {e}")
                return

        try:
            # pypresence handling of image URLs depends on Discord's allow-list, 
            # but usually it requires an asset key. 
            # If the large_image is a URL, we might need to rely on Discord's 
            # auto-detection or fallback to a generic image if it fails.
            # For now, we pass it as is.
            self.rpc.update(
                state=state,
                details=details,
                large_image=large_image,
                large_text=large_text,
                small_image=small_image,
                small_text=small_text
            )
            print(f"Updated presence: {details} - {state}")
        except Exception as e:
            print(f"Failed to update presence: {e}")

    def search_gametdb(self, query):
        """
        Searches GameTDB.
        Strategy 1: Search by name (note: often protected/difficult)
        Strategy 2: Check if query looks like an ID (e.g. AAACA) and fetch directly.
        """
        
        # Helper headers to mimic browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Strategy 1: Local DB Lookup (Name -> ID)
        found_id_by_name = None
        if self.game_db:
             query_upper = query.upper()
             # If exact ID match in DB (unlikely if user typed name, but possible)
             for game in self.game_db:
                 if game['id'].upper() == query_upper:
                     found_id_by_name = game['id']
                     print(f"Direct ID match in DB: {found_id_by_name}")
                     break
             
             if not found_id_by_name:
                 # Check names
                 query_lower = query.lower()
                 for game in self.game_db:
                     if game['title'].lower() == query_lower:
                         found_id_by_name = game['id']
                         print(f"Exact Name match in DB: {found_id_by_name}")
                         break
        
        if found_id_by_name:
            query = found_id_by_name # Promote to ID for Strategy 2

        # Strategy 2: Check ID first if it looks like one (5 uppercase chars usually)
        if re.match(r'^[A-Z0-9]{5}$', query.upper()):
            game_id = query.upper()
            url = f"https://www.gametdb.com/Switch/{game_id}"
            print(f"Attempting valid ID fetch: {url}")
            try:
                res = requests.get(url, headers=headers)
                if res.status_code == 200:
                    return self._parse_game_page(res.text, game_id)
            except Exception as e:
                print(f"Error fetching ID {game_id}: {e}")

        # Strategy 1: Search query
        search_url = "https://www.gametdb.com/Switch/Search"
        params = {'q': query}
        print(f"Attempting search: {params}")
        
        try:
            res = requests.get(search_url, params=params, headers=headers)
            if res.status_code == 200:
                # If we got a direct list or no results, parsing is needed.
                # However, for now, let's assume the user might want a specific ID if general search fails.
                # We can implement a more complex search parser here later if needed.
                return None
        except Exception as e:
            print(f"Search failed: {e}")
            
        return None

    def _parse_game_page(self, html, game_id):
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract Title
        # Title is often in h1, format "ID - Title"
        title_tag = soup.find('h1', class_='notranslate')
        title = "Unknown Game"
        if title_tag:
            full_title = title_tag.text.strip()
            # Remove ID prefix if present (e.g. "AAACA - Super Mario Odyssey")
            if full_title.startswith(f"{game_id} - "):
                title = full_title[len(f"{game_id} - "):]
            else:
                title = full_title
        
        # Extract Box Art
        # Look for img with specific source pattern
        box_art = "switch" # Default asset key
        
        # GameTDB structure for covers:
        # <a href="..." class="highslide" ...><img src="https://art.gametdb.com/switch/cover/US/AAACA.jpg?..." ...></a>
        # We want the 'cover' or 'coverHQ' URL.
        
        # Try finding the 'coverHQ' image first (High Quality) containing the ID
        img_tags = soup.find_all('img')
        found_hq = False
        
        # First pass: Look for coverHQ with Game ID
        for img in img_tags:
            src = img.get('src', '')
            if 'art.gametdb.com/switch/coverHQ/' in src and game_id in src:
                box_art = src
                found_hq = True
                break
        
        # Second pass: Fallback to standard cover with Game ID
        if not found_hq:
            for img in img_tags:
                src = img.get('src', '')
                if 'art.gametdb.com/switch/cover/' in src and game_id in src:
                    box_art = src
                    break
        
        return {
            'name': title,
            'image_url': box_art,
            'page_url': f"https://www.gametdb.com/Switch/{game_id}"
        }

if __name__ == "__main__":
    # Simple test
    backend = SwitchRPCBackend()
    result = backend.search_gametdb("AAACA")
    print(result)
