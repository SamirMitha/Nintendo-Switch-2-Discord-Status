import xml.etree.ElementTree as ET
import json
import os

INPUT_FILE = 'switchtdb.xml'
OUTPUT_FILE = 'games.json'

def parse_xml():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Parsing {INPUT_FILE}...")
    
    games = []
    
    try:
        # Use iterparse for memory efficiency if the file is huge, 
        # but 20MB is fine for standard parse.
        tree = ET.parse(INPUT_FILE)
        root = tree.getroot()
        
        for game in root.findall('game'):
            game_id = game.find('id').text
            
            # Find English title
            title = None
            
            # Look for locale lang="EN"
            for locale in game.findall('locale'):
                if locale.get('lang') == 'EN':
                    title_elem = locale.find('title')
                    if title_elem is not None:
                        title = title_elem.text
                    break
            
            # Fallback to name attribute if no EN title found
            if not title:
                title = game.get('name')
                
            if game_id and title:
                games.append({'id': game_id, 'title': title})
                
        print(f"Parsed {len(games)} games.")
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(games, f, indent=4)
        print(f"Saved to {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"Error parsing XML: {e}")

if __name__ == "__main__":
    parse_xml()
