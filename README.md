# HSRLingo

A language patcher for **Honkai: Star Rail**. 

Now supports **all official text languages** (en, th, ja, ko, cn, es, id, vi, fr, de, ru, pt) and in-game voice languages (en, ja, ko, cn).

## Supported Languages

### Text Languages:
- **English** (`en`)
- **Thai** (`th`)
- **Japanese** (`ja` / `jp`)
- **Korean** (`ko` / `kr`)
- **Simplified Chinese** (`cn`)
- **Spanish** (`es`)
- **Indonesian** (`id`)
- **Vietnamese** (`vi`)
- **French** (`fr`)
- **German** (`de`)
- **Russian** (`ru`)
- **Portuguese** (`pt`)

### Voice Languages:
- **English** (`en`)
- **Japanese** (`ja` / `jp`)
- **Korean** (`ko` / `kr`)
- **Chinese** (`cn`)

## Target

This patcher works for both **OS (Global)** and **CN** clients.

## How to Use?

1. Place `hsrlingo.py` in the same game folder where `StarRail.exe` is located (next to `StarRail_Data`).
2. Run the script:
   ```bash
   python hsrlingo.py
   ```
3. Choose your desired text language and voice language from the menu.
4. The patcher will automatically locate the configuration file, create a `.bak` backup, and apply the language patch.

## Notes

- An automatic `.bak` backup file is created before patching.
- For voice languages, ensure your client has the corresponding audio files installed (can be copied from official live client).
- For text languages in Beta/CN clients, ensure the respective TextData / font assets exist or allow the client to download them.