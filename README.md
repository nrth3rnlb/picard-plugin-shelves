# Shelves Plugin for MusicBrainz Picard

## Description

The **Shelves** plugin adds virtual shelf management to MusicBrainz Picard, allowing you to organise your music files by top-level folders (shelves) in your music library.

Think of your music library as a physical library with different shelves — one for your standard collection, one for incoming/unprocessed music, one for Christmas music, etc.

## Features

- ✅ **Automatic shelf detection** from file paths during scanning
- ✅ **Smart detection** prevents artist/album names from being mistaken as shelves
- ✅ **Manual shelf assignment** via context menu
- ✅ **Shelf management** in plugin settings (add, remove, scan directory)
- ✅ **Workflow automation** automatically moves files between shelves (e.g. "Incoming" > "Standard")
- ✅ **Script function `$shelf()`** for file naming integration
- ✅ **Visual script preview** in settings shows your file naming snippet

## Installation

1. Copy the `shelves` folder to your Picard plugins directory:
   - **System Package**: `~/.config/MusicBrainz/Picard/plugins/`
   - **Flatpak**: `~/.var/app/org.musicbrainz.Picard/config/MusicBrainz/Picard/plugins`

2. Restart Picard

3. Enable the plugin in: **Options → Plugins → Shelves**

## Usage

### Directory Structure

The plugin expects your music library to be organised like this:

```
~/Music/
├── Standard/
│   ├── Artist Name/
│   │   └── Album Name/
│   │       └── track.mp3
├── Incoming/
├── Christmas/
├── Soundtrack/
│   ├── Album Name/
│   │   └── track.mp3
└── ...
```

It is important to remember that each top-level folder in your music directory is considered a “shelf”.


### Automatic Detection

When you scan files in Picard, the plugin automatically:
1. Detects the shelf name from the file path
2. Sets the `shelf` tag in the file metadata
3. Adds the shelf to the list of known shelves

### Smart Shelf Detection

The plugin has semi-intelligent recognition to avoid confusion:

- **Default and known shelves** are always recognised correctly
- **Suspicious folder names** are automatically identified and treated as misplaced files:
  - Names containing "-" (typical for "Artist - Album" format)
  - Very long names (> 30 characters)
  - Names with many words (> three words)
  - Names containing album indicators (Vol., Disc, CD, Part)

**Example:**
- If you accidentally place files in `~/Music/Wardruna - Runaljod - Yggdrasil/`, the plugin recognises this as an artist/album name (not a shelf)
- The shelf tag is automatically set to "Standard" instead
- Files will be organised properly when saved: `~/Music/Standard/Wardruna/Runaljod - Yggdrasil/`

**Note:** If you *really* want to use such a name as a shelf, add it manually in the plugin settings. Once added, it will be recognised as a valid shelf.

### Manual Assignment

**Right-click** on albums or tracks in Picard and select **"Set shelf name..."** to assign or change the shelf.

### Plugin Settings

Open **Options → Plugins → Shelves** to:

#### Shelf Management
- View all known shelves
- **Add Shelf** — Manually add a new shelf
- **Remove Shelf** — Remove a shelf from the list
- **Scan Music Directory** — Automatically detect all shelves from your music folder

#### Workflow Configuration
Enable automatic shelf transitions when saving files:

- **Enable Workflow** — Turn workflow automation on/off
- **Stage 1** — Source shelf (e.g. "Incoming")
- **Stage 2** — Destination shelf (e.g. "Standard")

When enabled, files from Stage 1 are automatically moved to Stage 2 when you save them.

#### Script Preview
The settings show a ready-to-use file naming script that you can copy to **Options → File Naming**.

## File Naming Script

The plugin provides the `$shelf()` script function. Use this in **Options → File Naming**:

```
$set(_shelffolder,$shelf())
$set(_shelffolder,$if($not($eq(%_shelffolder%,)),%_shelffolder%/))

%_shelffolder%
$if2(%albumartist%,%artist%)/%album%/%title%
```

The `$shelf()` function:
- Returns the shelf name from the file's metadata
- Automatically applies workflow transitions if enabled (e.g. "Incoming" → "Standard")
- Returns an empty string if no shelf is set

**Tip:** Copy the script snippet directly from the plugin settings — it's shown in the "Script Preview" section!

## Workflow Examples

### Example 1: Incoming → Standard Workflow

Configure in plugin settings:
- ✅ Enable Workflow
- Stage 1: "Incoming"
- Stage 2: "Standard"

Then:
1. **Scan** music files from `~/Music/Incoming/Artist/Album/`
2. Plugin sets `shelf` tag to "Incoming"
3. Do your tagging/editing in Picard
4. **Save** the files
5. Files are automatically moved to `~/Music/Standard/Artist/Album/` (because workflow transforms "Incoming" → "Standard")

### Example 2: Manual Shelf Assignment

If you want to keep files in a specific shelf (e.g. "Christmas"):

1. **Scan** files from any location
2. **Right-click** the album → **"Set shelf name..."** → Select "Christmas"
3. **Save** the files
4. Files are moved to `~/Music/Christmas/Artist/Album/`

### Example 3: Moving Between Shelves Outside Picard

If you manually move files outside Picard:

1. Move `~/Music/Standard/Artist/Album/` to `~/Music/Soundtrack/Artist/Album/` (outside Picard)
2. **Scan** the files in Picard
3. Plugin automatically detects shelf as "Soundtrack"
4. When you **Save**, files remain in `~/Music/Soundtrack/Artist/Album/`

### Example 4: Accidentally Misplaced Files

If you accidentally place files directly under Music:

1. Files are in: `~/Music/Artist - Album/tracks/`
2. **Scan** in Picard
3. Plugin detects suspicious name, sets shelf to "Standard" (with warning in the log)
4. **Save** moves files to: `~/Music/Standard/Artist/Album/`

## Tag Information

- **Tag name:** `shelf`
- **Default shelves:** Standard, Incoming

## Troubleshooting

### My folder name is detected as "Standard" instead of the actual folder name

This is intentional! The plugin detected that your folder name looks like an artist/album name rather than a shelf name. Check the log for details about why it was considered suspicious.

**Solutions:**
1. **Recommended:** Let the plugin move your files to the correct location (`Standard/Artist/Album/`)
2. **Alternative:** If this folder name really should be a shelf, add it manually in the plugin settings

### How can I see which shelf was detected?

1. Select a file/album in Picard
2. Look at the metadata panel on the right
3. Find the `shelf` tag

You can also check Picard's log (Help → View Error/Debug Log) for detailed information about shelf detection.

### The workflow isn't working

Make sure:
- ✅ Workflow is **enabled** in plugin settings
- ✅ Your file naming script uses `$shelf()` (not `%shelf%` directly)
- ✅ Stage 1 and Stage 2 are set to different shelves

## Development

The plugin has a modular structure:

```
shelves/
├── __init__.py           # Plugin registration and setup
├── constants.py          # Constants and defaults
├── validators.py         # Shelf name validation
├── manager.py            # ShelfManager class
├── utils.py              # Utility functions
├── processors.py         # File and metadata processors
├── actions.py            # Context menu actions
├── options.py            # Options page
├── script_functions.py   # $shelf() function
└── ui_shelves_config.py  # Generated UI file
```

## Requirements

- MusicBrainz Picard 2.0 or higher 
- PyQt5
- `discid/discid.h` for the installation of the development environment using `pip install -e '.[dev]`
  - Search for a package with a name like `libdiscid-dev`, `libdiscid-devel` or similar, depending on your Linux distribution.

## License

GPL-2.0

## Author

nrth3rnlb

## Version

1.0.0
