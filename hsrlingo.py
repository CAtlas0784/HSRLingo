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

def wait_exit(msg="กดปุ่มใดก็ได้เพื่อปิดโปรแกรม (Press any key to exit)...", code=0):
    print(f"\n{msg}")
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
        sel = input("กรุณาเลือกหมายเลขหรือรหัสภาษา (Select number or code): ").strip().lower()
        if sel in options:
            return options[sel][0]
        if sel in valid_codes:
            return valid_codes[sel]
        print("ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง (Invalid choice, please try again).")

def resolve_design_data_dir():
    """Smart auto-detection of StarRail_Data directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.getcwd(), 'StarRail_Data', 'StreamingAssets', 'DesignData', 'Windows'),
        os.path.join(script_dir, 'StarRail_Data', 'StreamingAssets', 'DesignData', 'Windows'),
    ]

    for p in candidates:
        if os.path.exists(p):
            return p

    # Auto-detect from Desktop and common drives
    search_roots = [
        os.path.expanduser('~/Desktop'),
        os.path.expanduser('~/Downloads'),
        r"C:\HoYoPlay\games\Star Rail Games",
        r"D:\HoYoPlay\games\Star Rail Games",
        r"C:\Program Files\Star Rail\Games",
        r"D:\Program Files\Star Rail\Games"
    ]

    detected = []
    for root in search_roots:
        if not os.path.exists(root):
            continue
        # Direct check
        dd = os.path.join(root, 'StarRail_Data', 'StreamingAssets', 'DesignData', 'Windows')
        if os.path.exists(dd) and dd not in detected:
            detected.append(dd)
        # Check subdirectories (e.g. StarRail_4.6.51_OS)
        try:
            for item in os.listdir(root):
                sub = os.path.join(root, item)
                if os.path.isdir(sub):
                    dd_sub = os.path.join(sub, 'StarRail_Data', 'StreamingAssets', 'DesignData', 'Windows')
                    if os.path.exists(dd_sub) and dd_sub not in detected:
                        detected.append(dd_sub)
        except Exception:
            pass

    if detected:
        print("\n[+] ตรวจพบโฟลเดอร์เกมอัตโนมัติ (Auto-detected game folders):")
        for i, path in enumerate(detected, 1):
            print(f" [{i}] {path}")
        sel = input("เลือกหมายเลขโฟลเดอร์ หรือกด Enter เพื่อใช้ตัวเลือกแรก [1]: ").strip()
        idx = 0
        if sel.isdigit() and 1 <= int(sel) <= len(detected):
            idx = int(sel) - 1
        return detected[idx]

    # If still not found, allow user to drag & drop or paste game path
    print("\n[!] ไม่พบโฟลเดอร์ StarRail_Data อัตโนมัติ")
    user_input = input("กรุณาลากโฟลเดอร์เกม / StarRail_Data มาวางที่นี่ (หรือกด Enter เพื่อออก):\n> ").strip(' "\'')
    if not user_input:
        return None

    # Handle if user dragged StarRail.exe or root directory
    if os.path.isfile(user_input):
        user_input = os.path.dirname(user_input)
    if os.path.basename(user_input).lower() == "starrail_data":
        dd = os.path.join(user_input, 'StreamingAssets', 'DesignData', 'Windows')
    else:
        dd = os.path.join(user_input, 'StarRail_Data', 'StreamingAssets', 'DesignData', 'Windows')

    if os.path.exists(dd):
        return dd

    return None

def main():
    try:
        design_data_dir = resolve_design_data_dir()
        if not design_data_dir:
            print("[!] ไม่พบโฟลเดอร์ DesignData ของเกม Star Rail")
            wait_exit()
            return

        print(f"\n[+] กำลังทำงานกับโฟลเดอร์: {design_data_dir}")

        text_lang = prompt_choice("เลือกภาษาข้อความ (Select Text Language)", TEXT_LANGUAGES)
        voice_lang = prompt_choice("เลือกภาษาเสียงพากย์ (Select Voice Language)", VOICE_LANGUAGES)

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

        wait_exit()

    except KeyboardInterrupt:
        print("\n\n[!] ยกเลิกการทำงาน (Operation canceled)")
        sys.exit(0)

if __name__ == '__main__':
    main()