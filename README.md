# Nintendo Switch 2 Discord Status

A Python-based Discord Rich Presence (RPC) manager that allows you to display Nintendo Switch games as your Discord status.

> [!IMPORTANT]
> **This application does NOT connect to your Nintendo Switch console.**
> It runs entirely on your PC and only displays the status you manually select within this application. It does not read any data from your actual Switch.

## How It Works

This application connects to your local Discord client using RPC (Rich Presence). It allows you to:
1.  **Search** for Nintendo Switch games using a local database or online via GameTDB.
2.  **Display** the game's box art and title on your Discord profile by querying GameTDB.
3.  **Customize** your status details (e.g., "Playing", "Online").
4.  **Manually Update** your status. You must open the app and click "Set Presence" to change what Discord shows.

It relies on a database file (`games.json`) derived from GameTDB's `switchtdb.xml` to quickly find game IDs and titles.

## Prerequisites & Setup (Important!)

Due to file size and licensing, the game database is **not included** by default. You must download it manually for the "Search" and "Autocomplete" features to work correctly.

1.  Download the **switchtdb.xml** file from GameTDB:
    [https://www.gametdb.com/Switch/Downloads](https://www.gametdb.com/Switch/Downloads)
2.  Place the `switchtdb.xml` file in the same folder as the application (`.exe` or `main.py`).

## How to Run (using .exe)

Download the exe from here: [https://github.com/SamirMitha/Nintendo-Switch-2-Discord-Status/releases](https://github.com/SamirMitha/Nintendo-Switch-2-Discord-Status/releases)

1.  Ensure you have placed `switchtdb.xml` next to the `Nintendo Switch 2 Discord Status.exe`.
2.  Double-click `Nintendo Switch 2 Discord Status.exe` to launch the application.
3.  **First Time Setup**:
    *   Click the **"Populate Database (XML)"** button.
    *   Wait for the status to say "DB Updated". This converts the XML into a faster `games.json` file.
4.  **Usage**:
    *   Type a game name in the search box (e.g., "Metroid Dread").
    *   Select the game from the dropdown and click **"Search GameTDB"**.
    *   Once the game details appear, click **"Set Presence"** to update your Discord status.
    *   This will update your Discord status to show the game's box art and title.
