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

# Force working directory to the directory where this script is located (Game Root)
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
design_data_dir = os.path.join(script_dir, 'StarRail_Data', 'StreamingAssets', 'DesignData', 'Windows')

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

def exit_program(code=0):
    print("\nกด Enter หรือปุ่มใดก็ได้เพื่อปิดโปรแกรม (Press any key to exit)...")
    if sys.platform == "win32":
        try:
            import msvcrt
            msvcrt.getch()
        except Exception:
            try:
                input()
            except Exception:
                pass
    else:
        try:
            input()
        except Exception:
            pass
    sys.exit(code)

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
    if "ja" in valid_codes:
        valid_codes["jp"] = "ja"
    if "ko" in valid_codes:
        valid_codes["kr"] = "ko"

    while True:
        sel = input("กรุณาเลือกหมายเลขหรือพิมพ์รหัส (Select number or code): ").strip().lower()
        if sel in options:
            return options[sel][0]
        if sel in valid_codes:
            return valid_codes[sel]
        print("ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง (Invalid choice, please try again).")

def main():
    try:
        if not os.path.exists(design_data_dir):
            print(f"[!] ไม่พบโฟลเดอร์: {design_data_dir}")
            print("กรุณานำไฟล์ hsrlingo.py ไปวางไว้ในโฟลเดอร์ Root ของเกม (โฟลเดอร์เดียวกับที่มี StarRail.exe)")
            exit_program(1)
            return

        text_lang = prompt_choice("เลือกภาษาข้อความ (Text Language)", TEXT_LANGUAGES)
        voice_lang = prompt_choice("เลือกภาษาเสียงพากย์ (Voice Language)", VOICE_LANGUAGES)

        # Convert to internal 2-letter codes used in DesignData (ja -> jp, ko -> kr)
        text_code = "jp" if text_lang == "ja" else ("kr" if text_lang == "ko" else text_lang)
        voice_code = "jp" if voice_lang == "ja" else ("kr" if voice_lang == "ko" else voice_lang)

        found = False
        for filename in os.listdir(design_data_dir):
            filepath = os.path.join(design_data_dir, filename)
            if not os.path.isfile(filepath) or filename.endswith('.bak'):
                continue

            try:
                with open(filepath, 'rb') as f:
                    content = bytearray(f.read())
            except Exception:
                continue

            pattern_to_find = 'SpriteOutput/UI/Fonts/RPG_CN.ttf'.encode('utf-8')
            if pattern_to_find not in content:
                continue

            try:
                idx = content.index('Korean'.encode('utf-8'))
            except ValueError:
                continue

            found = True
            print(f"\n[+] ตรวจพบไฟล์ตั้งค่าภาษา: {filename}")

            bak_path = filepath + '.bak'
            if not os.path.exists(bak_path):
                shutil.copy2(filepath, bak_path)
                print(f"[+] สร้างไฟล์สำรองไว้ที่: {filename}.bak")

            print(f"[*] กำลัง Patch ภาษา -> ข้อความ: [{text_code}] | เสียงพากย์: [{voice_code}]...")

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

            print("[✓] แก้ไขภาษาสำเร็จเรียบร้อยแล้ว (Language patched successfully)!")
            break

        if not found:
            print("[!] ไม่พบไฟล์ภาษาที่ต้องการแก้ไขใน DesignData")

        exit_program(0)

    except KeyboardInterrupt:
        print("\n\n[!] ยกเลิกการทำงาน")
        sys.exit(0)

if __name__ == '__main__':
    main()