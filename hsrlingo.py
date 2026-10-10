import hashlib
import json
import os
import re
import shutil
import struct
import sys
import urllib.request
import winreg

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

# All official text languages supported by Honkai: Star Rail
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

# Languages natively bundled in the base/beta client (no external download needed)
BUNDLED_LANGUAGES = {"en", "cn", "ja", "ko", "jp", "kr"}

# Permanent 8-byte Container IDs used by Honkai: Star Rail DesignData
CONTAINER_IDS = {
    "en": "f90c090cbf12fd1f",
    "cn": "6d8877f08e2ebf38",
    "ja": "58421c81a556484d",
    "jp": "58421c81a556484d",
    "ko": "c6e9d754f933488c",
    "kr": "c6e9d754f933488c",
    "th": "1573487e8c3d61ca",
    "ru": "3e9816b2db9acd5f",
    "vi": "861c6edb381fbc90",
    "id": "636296c3f4aed4b2",
    "es": "11a91d3c9157673a",
    "pt": "b01537acbc54d57d",
    "de": "3992433e80b825e5",
    "fr": "c50e0a4eb272f963"
}

def exit_program(code=0):
    print("\nกด Enter หรือปุ่มใดก็ได้เพื่อปิดโปรแกรม (Press any key to exit)...")
    try:
        if sys.platform == "win32" and sys.stdin.isatty():
            import msvcrt
            msvcrt.getch()
        else:
            input()
    except Exception:
        pass
    sys.exit(code)

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

def sync_registry(text_code, voice_code):
    """Sets PlayerPrefs in Windows Registry so the game boots directly in the chosen language."""
    reg_paths = [
        r"Software\Cognosphere\Star Rail",
        r"Software\miHoYo\崩坏：星穹铁道"
    ]
    for r_path in reg_paths:
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r_path) as key:
                # String language keys
                winreg.SetValueEx(key, "Language_h2876912797", 0, winreg.REG_SZ, text_code)
                winreg.SetValueEx(key, "MIHOYOSDK_CURRENT_LANGUAGE_h255914971", 0, winreg.REG_SZ, text_code)
                # Binary language keys (with null terminator)
                bin_val = text_code.encode("utf-8") + b"\x00"
                winreg.SetValueEx(key, "MIHOYOSDK_CURRENT_LANGUAGE_h2559149783", 0, winreg.REG_BINARY, bin_val)
                # Audio language key
                audio_bin = voice_code.encode("utf-8") + b"\x00"
                winreg.SetValueEx(key, "LanguageSettings_LocalAudioLanguage_h882585060", 0, winreg.REG_BINARY, audio_bin)
            print(f"[+] ซิงค์การตั้งค่าลง Windows Registry เรียบร้อย: {r_path}")
        except Exception as e:
            print(f"[!] คำเตือน: ไม่สามารถบันทึกลง Registry ({r_path}): {e}")

def replace_bytes(content, idx, choice, param):
    for _ in range(param):
        content[idx:idx + 2] = choice.encode('utf-8')
        idx += 3
    return idx

def patch_font_file(text_code, voice_code):
    """Patches AllowedLanguage table in font configuration file."""
    for filename in os.listdir(design_data_dir):
        filepath = os.path.join(design_data_dir, filename)
        if not os.path.isfile(filepath) or filename.endswith('.bak') or filename.endswith('.tmp'):
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

        bak_path = filepath + '.bak'
        if not os.path.exists(bak_path):
            try:
                shutil.copy2(filepath, bak_path)
                print(f"[+] สำรองไฟล์ Font/UI config ไว้ที่: {filename}.bak")
            except Exception:
                pass

        print(f"[*] กำลัง Patch ไฟล์ Font/UI config ({filename})...")
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

        tmp_path = filepath + '.tmp'
        with open(tmp_path, 'wb') as w:
            w.write(content)
        os.replace(tmp_path, filepath)
        print("[✓] Patch ไฟล์ Font/UI config สำเร็จเรียบร้อย!")
        return True
    return False

def download_stream(url, target_path, expected_size=None):
    """Downloads a file with clean progress reporting."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    print(f"[*] กำลังดาวน์โหลด: {os.path.basename(target_path)}...")
    tmp_path = target_path + ".download"
    try:
        with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_path, "wb") as out_file:
            total_size = int(resp.headers.get("Content-Length", expected_size or 0))
            downloaded = 0
            chunk_size = 65536
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100
                    sys.stdout.write(f"\r    -> ความคืบหน้า: {pct:.1f}% ({downloaded}/{total_size} bytes)")
                    sys.stdout.flush()
        print()
        if os.path.exists(target_path):
            os.remove(target_path)
        os.replace(tmp_path, target_path)
        print(f"[✓] ดาวน์โหลดเสร็จสิ้น: {os.path.basename(target_path)}")
        return True
    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        print(f"\n[!] ดาวน์โหลดล้มเหลว: {e}")
        return False

def detect_language_markers(data):
    """Detects which language a DesignData bytes chunk belongs to."""
    if b"BK_All_In_One" in data[:1000]:
        return "audio"
    if b"ActionGroup_SelectMenu" in data[:1000]:
        return "ui"

    # Inspect body text (after language names header, e.g. bytes 600..3000)
    body = data[600:3000].decode("utf-8", errors="ignore")

    # Non-Latin script counts
    if len(re.findall(r"[\u0e00-\u0e7f]", body)) >= 10:
        return "th"
    if len(re.findall(r"[\u0400-\u04ff]", body)) >= 15:
        return "ru"
    if len(re.findall(r"[\uac00-\ud7af]", body)) >= 15:
        return "ko"
    if len(re.findall(r"[\u3040-\u30ff]", body)) >= 15:
        return "ja"

    lower = body.lower()
    if len(re.findall(r"[\u1ea0-\u1ef9]", body)) >= 3 or "tiếng việt" in lower or "âm thanh" in lower:
        return "vi"
    if "tekan" in lower or "pengumuman" in lower or "masuk" in lower:
        return "id"
    if "toca" in lower or "presiona" in lower or "idioma" in lower or "iniciar sesi" in lower:
        return "es"
    if "selecione" in lower or "servidor" in lower or "carregando" in lower:
        return "pt"
    if "veuillez" in lower or "retour" in lower or "chargement" in lower:
        return "fr"
    if "bitte" in lower or "server" in lower or "wähle" in lower or "anmelden" in lower:
        return "de"
    if "verification" in lower or "failed to obtain" in lower or "retry" in lower or "click to restart" in lower:
        return "en"

    if len(re.findall(r"[\u4e00-\u9fff]", body)) >= 15:
        if "繁體" in body or "華語" in body or "點擊" in body:
            return "zh-tw"
        return "cn"
    return "unknown"

def resolve_and_download_language(target_lang):
    """Dynamically resolves and downloads the target language package from the official Global CDN."""
    print(f"\n[*] กำลังเชื่อมต่อ Official HoYoverse CDN เพื่อค้นหาแพ็กเกจภาษา [{target_lang}]...")
    
    # 1. Query Global Launcher API to obtain the dynamic CDN resource URL
    hyp_api = "https://sg-hyp-api.hoyoverse.com/hyp/hyp-connect/api/getGamePackages?game_ids[]=4ziysqXOQ8&launcher_id=VYTpXlbWo8"
    try:
        req = urllib.request.Request(hyp_api, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        res_list_url = data["data"]["game_packages"][0]["main"]["major"]["res_list_url"].rstrip("/")
    except Exception as e:
        print(f"[!] ไม่สามารถเชื่อมต่อ Launcher API ได้: {e}")
        return None

    # 2. Fetch pkg_version manifest
    pkg_v_url = f"{res_list_url}/pkg_version"
    try:
        req = urllib.request.Request(pkg_v_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            manifest_lines = resp.read().decode("utf-8").splitlines()
    except Exception as e:
        print(f"[!] ไม่สามารถดาวน์โหลด manifest จาก CDN ได้: {e}")
        return None

    # 3. Locate DesignV on CDN and parse all language entries
    cdn_design_v_item = None
    candidate_items = []
    for line in manifest_lines:
        if "DesignData/Windows/" not in line:
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        rname = item.get("remoteName", "")
        if "DesignV_" in rname:
            cdn_design_v_item = item
        elif not any(k in rname for k in ["ArchiveV", "NativeDataV"]):
            candidate_items.append(item)

    if not cdn_design_v_item:
        print("[!] ไม่พบ DesignV ใน manifest ของ CDN")
        return None

    # Download CDN DesignV to extract precise subitem boundaries and container metadata
    cdn_dv_url = f"{res_list_url}/{cdn_design_v_item['remoteName']}"
    try:
        with urllib.request.urlopen(urllib.request.Request(cdn_dv_url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15) as resp:
            cdn_dv_data = resp.read()
    except Exception as e:
        print(f"[!] ไม่สามารถดาวน์โหลด CDN DesignV: {e}")
        return None

    # Parse entries in CDN DesignV
    cdn_entries = {}
    for item in candidate_items:
        h = item["md5"]
        h_bytes = bytes.fromhex(h)
        idx = cdn_dv_data.find(h_bytes)
        if idx == -1:
            continue
        off, flen, sub_count = struct.unpack(">III", cdn_dv_data[idx + 16:idx + 28])
        subs = []
        p = idx + 28
        for _ in range(sub_count):
            sid, ssz, sof = struct.unpack(">III", cdn_dv_data[p:p + 12])
            subs.append((sid, ssz, sof))
            p += 12
        cid_bytes = cdn_dv_data[idx - 4:idx]
        cdn_entries[h] = {
            "remoteName": item["remoteName"],
            "fileSize": flen,
            "md5": h,
            "cid_bytes": cid_bytes,
            "sub_items": subs
        }

    # 4. Search candidate files to match the requested language
    matched_entry = None
    print(f"[*] กำลังตรวจสอบหาไฟล์ภาษา [{target_lang}] จาก CDN ({len(candidate_items)} ไฟล์)...")

    for item in candidate_items:
        h = item["md5"]
        local_path = os.path.join(design_data_dir, f"{h}.bytes")
        file_bytes = None

        if os.path.exists(local_path):
            with open(local_path, "rb") as lf:
                file_bytes = lf.read(3000)
        else:
            # Fetch the first 3000 bytes via HTTP Range request to detect language without downloading the whole file
            f_url = f"{res_list_url}/{item['remoteName']}"
            try:
                r_range = urllib.request.Request(f_url, headers={"Range": "bytes=0-2999", "User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(r_range, timeout=10) as fl:
                    file_bytes = fl.read()
            except Exception:
                continue

        if not file_bytes:
            continue

        detected = detect_language_markers(file_bytes)
        if detected == target_lang:
            matched_entry = cdn_entries.get(h)
            print(f"[+] พบไฟล์ภาษา [{target_lang}] -> Hash: {h} (ขนาด {item['fileSize']} bytes)")
            break

    if not matched_entry:
        print(f"[!] ไม่พบแพ็กเกจภาษา [{target_lang}] บน CDN")
        return None

    # 5. Ensure full file is downloaded locally
    target_file_path = os.path.join(design_data_dir, f"{matched_entry['md5']}.bytes")
    if not os.path.exists(target_file_path) or os.path.getsize(target_file_path) != matched_entry["fileSize"]:
        dl_url = f"{res_list_url}/{matched_entry['remoteName']}"
        success = download_stream(dl_url, target_file_path, matched_entry["fileSize"])
        if not success:
            return None
    else:
        print(f"[✓] ไฟล์ภาษา [{target_lang}] มีอยู่แล้วในเครื่อง: {matched_entry['md5']}.bytes")

    return matched_entry

def patch_design_v_container(target_lang, lang_meta):
    """Dynamically injects the language container into the client's DesignV manifest."""
    archive_path = os.path.join(design_data_dir, "M_Design_ArchiveV.bytes")
    m_design_path = os.path.join(design_data_dir, "M_DesignV.bytes")

    if not os.path.exists(archive_path) or not os.path.exists(m_design_path):
        print("[!] ไม่พบ M_Design_ArchiveV.bytes หรือ M_DesignV.bytes")
        return False

    # Back up metadata files if not already backed up
    if not os.path.exists(archive_path + ".bak"):
        shutil.copy2(archive_path, archive_path + ".bak")
    if not os.path.exists(m_design_path + ".bak"):
        shutil.copy2(m_design_path, m_design_path + ".bak")

    # Read active DesignV hash from archive
    with open(archive_path, "r", encoding="utf-8") as f:
        archive_lines = [l.strip() for l in f if l.strip()]

    active_hash = None
    for l in archive_lines:
        try:
            obj = json.loads(l)
            if obj.get("FileName") == "M_DesignV":
                active_hash = obj.get("ContentHash")
                break
        except Exception:
            pass

    if not active_hash:
        print("[!] ไม่สามารถระบุ active DesignV hash ได้")
        return False

    # Prefer reading from original .bak to always build from clean manifest
    base_dv_candidates = [
        os.path.join(design_data_dir, f"DesignV_{active_hash}.bytes.bak"),
        os.path.join(design_data_dir, f"DesignV_{active_hash}.bytes")
    ]
    dv_path = None
    for cand in base_dv_candidates:
        if os.path.exists(cand):
            dv_path = cand
            break

    if not dv_path:
        print(f"[!] ไม่พบไฟล์ DesignV_{active_hash}.bytes")
        return False

    # Backup original DesignV if needed
    orig_dv_path = os.path.join(design_data_dir, f"DesignV_{active_hash}.bytes")
    if not os.path.exists(orig_dv_path + ".bak") and os.path.exists(orig_dv_path):
        shutil.copy2(orig_dv_path, orig_dv_path + ".bak")

    with open(dv_path, "rb") as f:
        dv_content = bytearray(f.read())

    # If the target language is a bundled language, restore clean DesignV
    if target_lang in BUNDLED_LANGUAGES:
        print(f"[*] ภาษา [{target_lang}] เป็นภาษาในตัวเกม (Bundled) -> คืนค่า DesignV กลับสู่สภาพเดิม...")
        if os.path.exists(orig_dv_path + ".bak"):
            shutil.copy2(orig_dv_path + ".bak", orig_dv_path)
        if os.path.exists(archive_path + ".bak"):
            shutil.copy2(archive_path + ".bak", archive_path)
        if os.path.exists(m_design_path + ".bak"):
            shutil.copy2(m_design_path + ".bak", m_design_path)
        return True

    # For non-bundled languages, construct the replacement container entry
    target_cid_hex = CONTAINER_IDS.get(target_lang, "1573487e8c3d61ca")
    target_cid = bytes.fromhex(target_cid_hex)
    target_fhash = bytes.fromhex(lang_meta["md5"])
    flen = lang_meta["fileSize"]

    # Extract subitem sizes
    sub_items = lang_meta.get("sub_items", [])
    if len(sub_items) >= 2:
        s0_sz = sub_items[0][1]
        s1_id = sub_items[1][0]
        s1_sz = sub_items[1][1]
    else:
        # Fallback split approximation if subitems are missing
        s0_sz = int(flen * 0.87)
        s1_sz = flen - s0_sz
        s1_id = 0x331a87c0

    s1_id_bytes = struct.pack(">I", s1_id) + b"\x00\x00\x00\x00"

    # Construct clean 71-byte DesignV container entry
    new_entry = bytearray()
    new_entry += target_cid
    new_entry += target_fhash
    new_entry += struct.pack(">III", 0, flen, 2)
    new_entry += target_cid + struct.pack(">II", s0_sz, 0)
    new_entry += s1_id_bytes + struct.pack(">II", s1_sz, s0_sz)
    new_entry += b"\x00\x00\x80"

    if len(new_entry) != 71:
        print(f"[!] ข้อผิดพลาด: ขนาด Entry ไม่ถูกต้อง ({len(new_entry)} != 71)")
        return False

    # Replace Entry 5 (EN container slot: offset 643..714)
    print(f"[*] กำลัง Inject Container สำหรับ [{target_lang}] (CID: {target_cid_hex}) ลงใน DesignV...")
    dv_content[643:714] = new_entry

    new_dv_md5 = hashlib.md5(dv_content).hexdigest()
    new_dv_path = os.path.join(design_data_dir, f"DesignV_{new_dv_md5}.bytes")
    with open(new_dv_path, "wb") as f:
        f.write(dv_content)
    print(f"[+] สร้าง DesignV ใหม่: DesignV_{new_dv_md5}.bytes")

    # Update M_DesignV.bytes
    with open(m_design_path, "rb") as f:
        m_bytes = bytearray(f.read())
    parts = [int(new_dv_md5[i:i+8], 16) for i in range(0, 32, 8)]
    m_bytes[28:44] = struct.pack("<IIII", *parts)
    m_bytes[44:48] = struct.pack("<I", len(dv_content))
    with open(m_design_path, "wb") as f:
        f.write(m_bytes)
    print(f"[+] อัปเดต M_DesignV.bytes -> Checksum: {new_dv_md5}")

    # Update M_Design_ArchiveV.bytes
    updated_archive = []
    for l in archive_lines:
        obj = json.loads(l)
        if obj.get("FileName") == "M_DesignV":
            obj["ContentHash"] = new_dv_md5
            obj["FileSize"] = len(dv_content)
        updated_archive.append(json.dumps(obj, separators=(",", ":")))
    with open(archive_path, "wb") as f:
        f.write(("\r\n".join(updated_archive) + "\r\n").encode("utf-8"))
    print(f"[+] อัปเดต M_Design_ArchiveV.bytes เรียบร้อย!")

    return True

def safe_copy_file(src, dst):
    """Safely copies a file using an atomic replace to bypass permission and attribute lock errors."""
    tmp = dst + ".tmp"
    try:
        shutil.copyfile(src, tmp)
        os.replace(tmp, dst)
        return True
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False

def restore_backups():
    """Restores all original .bak files."""
    print("\n[*] กำลังคืนค่าไฟล์ต้นฉบับทั้งหมดจาก .bak...")
    restored = 0
    for root, _, files in os.walk(design_data_dir):
        for f in files:
            if f.endswith(".bak"):
                orig = os.path.join(root, f[:-4])
                bak = os.path.join(root, f)
                if safe_copy_file(bak, orig):
                    restored += 1
                    print(f"  [✓] คืนค่า: {f[:-4]}")
                else:
                    print(f"  [!] ไม่สามารถคืนค่า: {f[:-4]}")
    if restored > 0:
        sync_registry("en", "en")
        print(f"\n[✓] คืนค่าไฟล์ทั้งหมด {restored} ไฟล์เรียบร้อยแล้ว!")
    else:
        print("\n[!] ไม่พบไฟล์สำรอง (.bak) ในโฟลเดอร์")

def main():
    try:
        print("==================================================")
        print("   HSRLingo - Universal Language Switcher / Downloader")
        print("   Support All Official Languages (No Hardcoded Hashes)")
        print("==================================================")

        if not os.path.exists(design_data_dir):
            print(f"[!] ไม่พบโฟลเดอร์: {design_data_dir}")
            print("กรุณานำไฟล์ hsrlingo.py ไปวางไว้ในโฟลเดอร์ Root ของเกม (โฟลเดอร์เดียวกับที่มี StarRail.exe)")
            exit_program(1)
            return

        print("\nเมนูหลัก (Main Menu):")
        print(" [1] เลือกเปลี่ยนภาษา (Switch/Download Language)")
        print(" [2] คืนค่าไฟล์ต้นฉบับ (Restore Original Backups)")
        print(" [0] ออกจากโปรแกรม (Exit)")
        choice = input("\nกรุณาเลือกตัวเลือก: ").strip()

        if choice == "0":
            sys.exit(0)
        elif choice == "2":
            restore_backups()
            exit_program(0)
            return
        elif choice != "1":
            print("[!] ตัวเลือกไม่ถูกต้อง")
            exit_program(1)
            return

        text_lang = prompt_choice("เลือกภาษาข้อความ (Text Language)", TEXT_LANGUAGES)
        voice_lang = prompt_choice("เลือกภาษาเสียงพากย์ (Voice Language)", VOICE_LANGUAGES)

        text_code = "jp" if text_lang == "ja" else ("kr" if text_lang == "ko" else text_lang)
        voice_code = "jp" if voice_lang == "ja" else ("kr" if voice_lang == "ko" else voice_lang)

        # For non-bundled languages, download from CDN if missing
        if text_lang not in BUNDLED_LANGUAGES:
            lang_meta = resolve_and_download_language(text_lang)
            if not lang_meta:
                print(f"[!] ไม่สามารถติดตั้งภาษา [{text_lang}] ได้เนื่องจากไม่พบไฟล์ภาษาบน CDN")
                exit_program(1)
                return
            success = patch_design_v_container(text_lang, lang_meta)
            if not success:
                print("[!] ไม่สามารถ Patch DesignV container ได้")
                exit_program(1)
                return
        else:
            # Bundled language
            patch_design_v_container(text_lang, None)

        # Patch Font/UI config (AllowedLanguage table)
        patch_font_file(text_code, voice_code)

        # Sync Registry PlayerPrefs
        sync_registry(text_code, voice_code)

        print("\n==================================================")
        print(f"[✓] ติดตั้งและตั้งค่าภาษาสำเร็จเรียบร้อย!")
        print(f"    ข้อความ (Text):  [{text_lang.upper()}]")
        print(f"    เสียงพากย์ (Voice): [{voice_lang.upper()}]")
        print("    คุณสามารถเปิดเกม Star Rail เข้าเล่นได้ทันที!")
        print("==================================================")
        exit_program(0)

    except KeyboardInterrupt:
        print("\n\n[!] ยกเลิกการทำงาน")
        sys.exit(0)

if __name__ == '__main__':
    main()