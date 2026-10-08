import os
import shutil
import sys

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

design_data_dir = './StarRail_Data/StreamingAssets/DesignData/Windows/'

# All official 2-character text languages supported by Honkai: Star Rail
TEXT_LANGUAGES = {
    "1": ("en", "English"),
    "2": ("th", "Thai (ภาษาไทย)"),
    "3": ("ja", "Japanese (日本語)"),
    "4": ("ko", "Korean (한국어)"),
    "5": ("cn", "Simplified Chinese (简体中文)"),
    "6": ("es", "Spanish (Español)"),
    "7": ("id", "Indonesian (Bahasa Indonesia)"),
    "8": ("vi", "Vietnamese (Tiếng Việt)"),
    "9": ("fr", "French (Français)"),
    "10": ("de", "German (Deutsch)"),
    "11": ("ru", "Russian (Русский)"),
    "12": ("pt", "Portuguese (Português)")
}

# Voice languages with existing in-game audio packs
VOICE_LANGUAGES = {
    "1": ("en", "English"),
    "2": ("ja", "Japanese"),
    "3": ("ko", "Korean"),
    "4": ("cn", "Chinese")
}

def replace_bytes(content, idx, choice, param):
    for _ in range(param):
        content[idx:idx + 2] = choice.encode('utf-8')
        idx += 3
    return idx

def prompt_choice(title, options):
    print(f"\n=== {title} ===")
    for key, (code, name) in options.items():
        print(f" [{key}] {name} ({code})")
    
    valid_codes = {code: code for code, _ in options.values()}
    # Allow common aliases
    if "ja" in valid_codes:
        valid_codes["jp"] = "ja"
    if "ko" in valid_codes:
        valid_codes["kr"] = "ko"

    while True:
        sel = input("Please select number or code: ").strip().lower()
        if sel in options:
            return options[sel][0]
        if sel in valid_codes:
            return valid_codes[sel]
        print("Invalid choice, please try again.")

def main():
    if not os.path.exists(design_data_dir):
        print(f"[!] Target directory not found: {design_data_dir}")
        print("Make sure this file is placed in the same folder where StarRail.exe is located.")
        input("Press Enter to exit...")
        return

    text_lang = prompt_choice("Select Text Language", TEXT_LANGUAGES)
    voice_lang = prompt_choice("Select Voice Language", VOICE_LANGUAGES)

    # Convert to internal 2-letter codes used in DesignData (ja -> jp, ko -> kr)
    text_code = "jp" if text_lang == "ja" else ("kr" if text_lang == "ko" else text_lang)
    voice_code = "jp" if voice_lang == "ja" else ("kr" if voice_lang == "ko" else voice_lang)

    found = False
    for filename in os.listdir(design_data_dir):
        filepath = os.path.join(design_data_dir, filename)
        if not os.path.isfile(filepath) or filename.endswith('.bak'):
            continue

        with open(filepath, 'rb') as f:
            content = bytearray(f.read())

        pattern_to_find = 'SpriteOutput/UI/Fonts/RPG_CN.ttf'.encode('utf-8')
        if pattern_to_find not in content:
            continue

        try:
            idx = content.index('Korean'.encode('utf-8'))
        except ValueError:
            continue

        found = True
        print(f"\n[+] Found target language configuration file: {filename}")

        bak_path = filepath + '.bak'
        if not os.path.exists(bak_path):
            shutil.copy2(filepath, bak_path)
            print(f"[+] Backup created: {filename}.bak")

        print(f"[*] Patching language -> Text: [{text_code}] | Voice: [{voice_code}]...")

        # Move to os text language
        idx += 10 + 4
        idx = replace_bytes(content, idx, text_code, 4)

        # Move to cn voice language
        idx += 1 + 5
        idx = replace_bytes(content, idx, voice_code, 2)

        # Move to os voice language
        idx += 1 + 5
        idx = replace_bytes(content, idx, voice_code, 5)

        # Move to cn text language
        idx += 1 + 4
        idx = replace_bytes(content, idx, text_code, 2)

        with open(filepath, 'wb') as w:
            w.write(content)

        print("[✓] Language patched successfully!")
        break

    if not found:
        print("[!] Could not find the file to patch in DesignData.")

    input("\nPress Enter to exit...")

if __name__ == '__main__':
    main()