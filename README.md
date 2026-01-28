# Shelves Plugin for MusicBrainz Picard

The **Shelves** plugin adds virtual shelf management to [MusicBrainz Picard](https://picard.musicbrainz.org/), allowing
you to organize your music files by top-level folders (shelves) in your music library.

## Features

- **Script function `$shelf()`** for file naming integration
- **Automatic shelf detection** from file paths during scanning
- **Manual shelf assignment** via the context menu
- **Manually locking and unlocking** the shelf via the context menu
- **Workflow automation** automatically moves files between shelves (e.g. "Incoming" or "Stash" or … -> "Standard")
- **Configuration** in plugin settings

---

## Installation

1. Copy the `shelves` folder to your Picard plugins directory:
    - **System Package**: `~/.config/MusicBrainz/Picard/plugins/`
    - **Flatpak**: `~/.var/app/org.musicbrainz.Picard/config/MusicBrainz/Picard/plugins`
2. Restart Picard
3. Enable the plugin in: **Options → Plugins → Shelves**

## Usage

### Directory Structure

The plugin expects your music library to be organized like this:

```
~/Picard_FileNaming_DestinationDirectory/
├── Standard/
│   └── …
├── Incoming/
│   └── …
├── Stash/
│   └── …
├── Soundtracks/
│   └── …
└── …
```

It is important to remember that each top-level folder in your music directory is considered a “shelf.”

### Automatic Detection

When you scan files in Picard, the plugin automatically:

1. Detects the shelf name from the file path
2. Sets the `shelf` tag in the file metadata
3. Adds the shelf to the list of known shelves

### Smart Shelf Detection

The plugin has semi-intelligent recognition to avoid confusion:

- **Default and known shelves** are always recognized correctly
- **Suspicious folder names** are automatically identified and treated as misplaced files:
    - Names containing "-" (typical for "Artist - Album" format)
    - Very long names (> 30 characters)
    - Names with many words (> three words)
    - Names containing album indicators (Vol., Disc, CD, Part)

**Example:**

- If you accidentally place files in `~/Music/Wardruna - Runaljod - Yggdrasil/`, the plugin recognizes this as an
  artist/album name (not a shelf)
- The shelf tag is automatically set to "Standard" instead
- Files will be organized properly when saved: `~/Music/Standard/Wardruna/Runaljod - Yggdrasil/`

**Note:** If you *really* want to use such a name as a shelf, add it manually in the plugin settings. Once added, it
will be recognized as a valid shelf.

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

- Scan for potential shelf names from your music directory.
- Activate and configure the workflow

Then:

1. **Scan** music files from `~/Music/Incoming/Artist/Album/`
2. Plugin sets `shelf` tag to "Incoming"
3. Do your tagging/editing in Picard
4. **Save** the files
5. Files are automatically moved to `~/Music/Standard/Artist/Album/` (because workflow transforms "Incoming" → "
   Standard")

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
3. Plugin detects suspicious name, sets shelf to "Standard"
4. **Save** moves files to: `~/Music/Standard/Artist/Album/`

## Troubleshooting

### My folder name is detected as "Standard" instead of the actual folder name

This is intentional! The plugin detected that your folder name looks like an artist/album name rather than a shelf name.
Check the log for details about why it was considered suspicious.

**Solutions:**

1. **Recommended:** Let the plugin move your files to the correct location (`Standard/Artist/Album/`)
2. **Alternative:** If this folder name really should be a shelf, add it manually in the plugin settings

### How can I see which shelf was detected?

1. Select a file/album in Picard
2. Look at the metadata panel on the right
3. Find the `shelf` tag

It is also possible to view the examples under Options -> File Naming.

### The workflow isn't working

Make sure:

- Workflow is **enabled** in plugin settings
- Your file naming script uses `$shelf()` (not `%shelf%` directly)
- Stage 1 and Stage 2 are set to different shelves

## Architektur

Module in `shelves/`:

- `__init__.py`: Plugin registration
- `constants.py`: Constants and defaults
- `exceptions.py`: Custom exceptions
- `typings.py`: Types and guards
- `utils.py`: Utility functions (validation, path handling)
- `manager.py`: Central shelf management (registry, votes, lock status, validation)
- `processors.py`: Processing of paths and metadata, voting, priorities, workflow integration
- `workflow.py`: Engine for two-stage transitions and target path calculation
- `actions.py`: Context menu actions (set/reset/determine shelf name)
- `options.py`: Options page including validations and script example with the `$shelf()` function
- `dialogs.py`: UI dialogs for selecting/entering shelves
- `widgets.py`: UI widgets
- `script_functions.py`: Implementation of `$shelf()`

## License

GPL-2.0-or-later
