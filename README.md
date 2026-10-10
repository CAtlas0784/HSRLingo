# HSRLingo

A universal, dynamic language switcher and asset patcher for **Honkai: Star Rail**.

Supports **all 12 official text languages** (English, Thai, Japanese, Korean, Chinese, Spanish, Indonesian, Vietnamese, French, German, Russian, Portuguese) and in-game voice languages.

For Beta/CBT/CN clients that only bundle 4 default languages (`en`, `cn`, `ja`, `ko`), HSRLingo automatically and dynamically connects to the official HoYoverse Global CDN to resolve and download the requested language packages and properly registers their containers in `DesignV`—without hardcoding file hashes or local PC paths, preventing black-screen errors.

---

## Features

- **Universal Language Support**: Switch to any of the 12 official text languages and 4 audio languages.
- **Dynamic CDN Auto-Downloader**: Automatically resolves and downloads official language assets directly from HoYoverse CDN if missing.
- **Zero Hardcoded Hashes**: Dynamically parses client and CDN `DesignV` manifests across game versions.
- **Non-Destructive & Safe**: Creates `.bak` backups before modifying any files, with a one-click restore option.
- **Windows Registry (`PlayerPrefs`) Sync**: Automatically updates the registry so the game boots directly into the chosen language.
- **Portable**: Pure Python standard library—no `pip install` required.

---

## Supported Languages

### Text Languages:
- **English** (`en`)
- **Thai (ภาษาไทย)** (`th`)
- **Japanese (日本語)** (`ja` / `jp`)
- **Korean (한국어)** (`ko` / `kr`)
- **Simplified Chinese (简体中文)** (`cn`)
- **Spanish (Español)** (`es`)
- **Indonesian (Bahasa Indonesia)** (`id`)
- **Vietnamese (Tiếng Việt)** (`vi`)
- **French (Français)** (`fr`)
- **German (Deutsch)** (`de`)
- **Russian (Русский)** (`ru`)
- **Portuguese (Português)** (`pt`)

### Voice Languages:
- **English** (`en`)
- **Japanese** (`ja` / `jp`)
- **Korean** (`ko` / `kr`)
- **Chinese** (`cn`)

---

## How to Use?

1. Place `hsrlingo.py` in the **Game Root folder** (the same folder where `StarRail.exe` is located).
2. Run the script:
   ```bash
   python hsrlingo.py
   ```
3. Select option `[1]` to choose your desired text language and voice language.
4. The tool will:
   - Check if the language is bundled or already cached.
   - If missing, download it from the official CDN and inject its container into `DesignV`.
   - Patch the font fallback and allowed language tables.
   - Sync Windows Registry.
5. Launch `StarRail.exe` and enjoy!

To revert any changes back to the original client files, simply select option `[2]` (Restore Original Backups).

---

## License

MIT License.