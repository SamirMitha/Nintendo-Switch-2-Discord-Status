import customtkinter as ctk
import threading
import requests
from PIL import Image
from io import BytesIO
from backend import SwitchRPCBackend
from parse_xml import parse_xml
import os

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

import sys

# Function to handle paths in both dev and OneFile mode
def resource_path(relative_path):
    # In OneFile mode, PyInstaller unpacks to sys._MEIPASS for bundled files
    # But usually we want files next to the EXE for things like games.json/switchtdb.xml
    # if we didn't bundle them.
    # However, to be safe for local files adjacent to exe:
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Class to redirect stdout/stderr to a text widget
class PrintLogger:
    def __init__(self, textbox):
        self.textbox = textbox
        self.terminal = sys.stdout

    def write(self, message):
        if self.terminal:
            self.terminal.write(message)
        # Safely update GUI on main thread
        try:
            # We use a trick if not on main thread:
            # But standard Tkinter methods *might* be risky from threads.
            # However, inserting into a widget from threads often causes issues.
            # We'll assume simple usage for now, or wrap if needed.
            self.textbox.configure(state="normal")
            self.textbox.insert("end", message)
            self.textbox.see("end")
            self.textbox.configure(state="disabled")
        except:
             pass

    def flush(self):
        if self.terminal:
            self.terminal.flush()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Nintendo Switch 2 Discord Status")
        self.geometry("800x500")

        # Layout Configuration

        # Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Frame: Controls
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.label_title = ctk.CTkLabel(self.left_frame, text="Nintendo Switch 2 Discord Status", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_title.pack(pady=20)

        # Search Mode
        self.option_mode = ctk.CTkOptionMenu(self.left_frame, values=["Name", "ID"], command=self.change_search_mode)
        self.option_mode.pack(pady=5, padx=20, fill="x")

        # Game Input (Autocomplete)
        self.entry_game = ctk.CTkComboBox(self.left_frame, values=[], command=self.on_game_select)
        self.entry_game.set("")
        self.entry_game.pack(pady=5, padx=20, fill="x")
        
        # Bind key release for autocomplete
        self.entry_game._entry.bind("<KeyRelease>", self.check_autocomplete)

        # Description Input
        self.entry_desc = ctk.CTkEntry(self.left_frame, placeholder_text="Description (e.g. Playing Online)")
        self.entry_desc.pack(pady=10, padx=20, fill="x")
        self.entry_desc.insert(0, "Playing")

        # Buttons
        self.btn_search = ctk.CTkButton(self.left_frame, text="Search GameTDB", command=self.search_gametdb)
        self.btn_search.pack(pady=10, padx=20, fill="x")
        
        self.btn_update = ctk.CTkButton(self.left_frame, text="Set Presence", fg_color="green", hover_color="darkgreen", command=self.update_presence)
        self.btn_update.pack(pady=10, padx=20, fill="x")

        self.btn_populate = ctk.CTkButton(self.left_frame, text="Populate Database (XML)", fg_color="gray", hover_color="darkgray", command=self.populate_db)
        self.btn_populate.pack(pady=10, padx=20, fill="x")


        # Status Label
        self.status_label = ctk.CTkLabel(self.left_frame, text="Status: Ready", text_color="gray")
        self.status_label.pack(pady=20)

        # Right Frame: Info / Logs
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.label_info = ctk.CTkLabel(self.right_frame, text="Game Details", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_info.pack(pady=20)

        self.image_label = ctk.CTkLabel(self.right_frame, text="")
        self.image_label.pack(pady=10)

        self.info_box = ctk.CTkTextbox(self.right_frame, width=300, height=100)
        self.info_box.pack(pady=10, padx=20, fill="both")
        self.info_box.insert("0.0", "Search for a game to see details here.\n\nTip: Use a 5-character ID (like AAACA for Mario Odyssey) for best results.")
        self.info_box.configure(state="disabled")
        
        # Log Viewer
        self.label_logs = ctk.CTkLabel(self.right_frame, text="Terminal Logs", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_logs.pack(pady=5)
        
        self.log_box = ctk.CTkTextbox(self.right_frame, width=300, height=150, font=("Consolas", 10))
        self.log_box.pack(pady=5, padx=20, expand=True, fill="both")
        self.log_box.configure(state="disabled")
        
        # Redirect Output
        sys.stdout = PrintLogger(self.log_box)
        sys.stderr = PrintLogger(self.log_box)

        # Initialize Backend (Moved here so logs are captured)
        self.backend = SwitchRPCBackend()

        # State variables
        self.current_image_url = "switch" # Default asset
        self.game_db = self.backend.get_game_db() # List of dicts
        self.all_titles = [g['title'] for g in self.game_db] if self.game_db else []
        self.cached_id_map = {g['title']: g['id'] for g in self.game_db} if self.game_db else {}

    def change_search_mode(self, choice):
        if choice == "ID":
            self.entry_game.set("")
            self.entry_game.configure(values=[])
        else:
            self.entry_game.set("")

    def check_autocomplete(self, event):
        if self.option_mode.get() == "ID":
            return
            
        current_text = self.entry_game.get()
        if not current_text or len(current_text) < 2:
            return

        # Simple filter: case-insensitive containment
        # Limit to top 20 for performance
        query = current_text.lower()
        matches = []
        count = 0
        for title in self.all_titles:
            if query in title.lower():
                matches.append(title)
                count += 1
                if count >= 20:
                    break
        
        self.entry_game.configure(values=matches)
        
    def on_game_select(self, choice):
        # When user selects a game from dropdown, we automatically have the correct name.
        # We can optionally trigger search immediately or just let them click Search.
        pass


    def search_gametdb(self):
        query = self.entry_game.get()
        if not query:
            self.status_label.configure(text="Status: Please enter a game name or ID", text_color="red")
            return

        self.status_label.configure(text="Status: Searching...", text_color="yellow")
        
        # Run in thread to avoid freezing GUI
        threading.Thread(target=self._run_search, args=(query,), daemon=True).start()

    def _run_search(self, query):
        result = self.backend.search_gametdb(query)
        self.after(0, self._handle_search_result, result)

    def _handle_search_result(self, result):
        if result:
            self.status_label.configure(text="Status: Found!", text_color="green")
            
            # Update inputs
            self.entry_game.set(result['name'])
            
            self.current_image_url = result['image_url']
            
            # Display Image
            try:
                response = requests.get(result['image_url'])
                img_data = Image.open(BytesIO(response.content))
                # Resize for display (keep aspect ratio roughly)
                ctk_image = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(160, 260))
                self.image_label.configure(image=ctk_image, text="")
            except Exception as e:
                print(f"Failed to load image: {e}")
                self.image_label.configure(image=None, text="[Image Load Failed]")

            # Update info box
            self.info_box.configure(state="normal")
            self.info_box.delete("0.0", "end")
            self.info_box.insert("0.0", f"Found: {result['name']}\n\nGame Page:\n{result['page_url']}")
            self.info_box.configure(state="disabled")
        else:
            self.status_label.configure(text="Status: Not Found", text_color="red")
            self.image_label.configure(image=None, text="")
            self.info_box.configure(state="normal")
            self.info_box.delete("0.0", "end")
            self.info_box.insert("0.0", "No results found on GameTDB.\nTry using the Game ID directly (e.g. AAACA).")
            self.info_box.configure(state="disabled")

    def update_presence(self):
        game = self.entry_game.get()
        desc = self.entry_desc.get()
        
        if not game:
            self.status_label.configure(text="Status: Game name required", text_color="red")
            return

        if not desc or len(desc) < 2:
            desc = "Playing"
            
        self.backend.update_presence(
            state=desc,
            details=game,
            large_image=self.current_image_url,
            large_text=game,
            small_image="online", # Default status icon
            small_text="Online"
        )
        self.status_label.configure(text=f"Status: Presence Set '{game}'", text_color="cyan")

    def populate_db(self):
        xml_path = resource_path('switchtdb.xml')
        if not os.path.exists(xml_path):
             self.status_label.configure(text=f"Status: switchtdb.xml not found at {xml_path}!", text_color="red")
             return
             
        self.status_label.configure(text="Status: Parsing XML...", text_color="yellow")
        self.btn_populate.configure(state="disabled")
        threading.Thread(target=self._run_populate, daemon=True).start()

    def _run_populate(self):
        try:
            parse_xml()
            # Reload DB
            self.game_db = self.backend.reload_db()
            self.all_titles = [g['title'] for g in self.game_db] if self.game_db else []
            self.after(0, lambda: self.status_label.configure(text=f"Status: DB Updated ({len(self.game_db)} games)", text_color="green"))
        except Exception as e:
            print(e)
            self.after(0, lambda: self.status_label.configure(text="Status: XML Parse Failed", text_color="red"))
        finally:
             self.after(0, lambda: self.btn_populate.configure(state="normal"))

if __name__ == "__main__":
    app = App()
    app.mainloop()
