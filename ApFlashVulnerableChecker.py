# ==========================================================
# Author: Prashanth Baragur Hanuman
# File  : ApFlashVulnerableChecker.py
# ==========================================================

import os
import re
import string
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def _read_lines(path: str):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()


def ap_hostname_from_run_header(path: str) -> Optional[str]:
    for line in _read_lines(path):
        if line.startswith("<run ") and "hostname=" in line:
            m = re.search(r"hostname='([^']+)'", line)
            if m:
                return m.group(1)
    return None


def ap_model_from_log(path: str) -> Tuple[Optional[str], Optional[bool]]:
    for line in _read_lines(path):
        if "Cisco AP Software" not in line:
            continue
        parts = line.split(",")
        if len(parts) < 2:
            return None, None
        ap_model = parts[1].strip()
        FLASH_ALLOWED_MODELS = {"(ap1g6)", "(ap1g6a)", "(ap1g6b)"}
        return ap_model, ap_model in FLASH_ALLOWED_MODELS
    return None, None


def primary_version_check(path: str) -> Tuple[Optional[str], Optional[bool]]:
    primary_image = None
    for line in _read_lines(path):
        if "AP Running Image     :" in line:
            primary_image = line.split(":", 1)[1].strip()
            break
    if not primary_image:
        return None, None
    try:
        parts = primary_image.split(".")
        if len(parts) < 4:
            return primary_image, None

        a, b, c, d = parts[:4]
        c_i = int(c); d_i = int(d)
        buggy = True
        if a == "17" and b == "12" and c_i <= 3:
            buggy = False
        elif a == "17" and b == "12" and c == "4" and d_i >= 213:
            buggy = False
        elif a == "17" and b == "12" and c == "5" and d_i >= 209:
            buggy = False
        elif a == "17" and b == "12" and c == "6" and d_i >= 201:
            buggy = False
        elif a == "17" and b == "15" and c == "3" and d_i >= 212:
            buggy = False
        elif a == "17" and b == "15" and c == "4" and d_i >= 206:
            buggy = False
        elif a == "17" and b == "15" and c == "5":
            buggy = False
        elif a == "17" and b == "18" and c == "1" and d_i >= 203:
            buggy = False
        elif a == "17" and b == "18" and c == "2" and d_i >= 201:
            buggy = False
        elif a == "17" and int(b) <= 9:
            buggy = False
        return primary_image, buggy
    except Exception:
        return primary_image, None


def backup_version_check(path: str) -> Tuple[Optional[str], Optional[bool]]:
    backup_image = None
    for line in _read_lines(path):
        if "Backup Boot Image    :" in line:
            backup_image = line.split(":", 1)[1].strip()
            break
    if not backup_image:
        return None, None
    try:
        parts = backup_image.split(".")
        if len(parts) < 4:
            return backup_image, None

        a, b, c, d = parts[:4]
        c_i = int(c); d_i = int(d)
        buggy = True
        if a == "17" and b == "12" and c_i <= 3:
            buggy = False
        elif a == "17" and b == "12" and c == "4" and d_i >= 213:
            buggy = False
        elif a == "17" and b == "12" and c == "5" and d_i >= 209:
            buggy = False
        elif a == "17" and b == "12" and c == "6" and d_i >= 201:
            buggy = False
        elif a == "17" and b == "15" and c == "3" and d_i >= 212:
            buggy = False
        elif a == "17" and b == "15" and c == "4" and d_i >= 206:
            buggy = False
        elif a == "17" and b == "15" and c == "5":
            buggy = False
        elif a == "17" and b == "18" and c == "1" and d_i >= 203:
            buggy = False
        elif a == "17" and b == "18" and c == "2" and d_i >= 201:
            buggy = False
        elif a == "17" and b == "9" and c == "7":
            buggy = False
        return backup_image, buggy
    except Exception:
        return backup_image, None


def cnssdaemon_log_present(path: str) -> bool:
    for line in _read_lines(path):
        if "cnssdaemon.log" in line and "root" in line:
            return True
    return False


def current_boot_partition(path: str) -> Tuple[Optional[str], Optional[bool]]:
    for line in _read_lines(path):
        if "BOOT path-list:" in line:
            part = line.split(":", 1)[1].strip()
            return part, (part == "part1")
    return None, None


def image_integrity_failed(path: str) -> Optional[bool]:
    try:
        lines = _read_lines(path)

        idx = None
        for i, line in enumerate(lines):
            if "show image integrity" in line:
                idx = i
                break

        if idx is None:
            return None

        next_50 = [l.strip() for l in lines[idx:idx+50] if l.strip()]

        integrity_statuses = []

        for line in next_50:
            if (
                "part.bin" in line or
                "ramfs_data_cisco" in line or
                "iox.tar.gz" in line
            ):
                try:
                    status = line.split(":")[1].strip().split()[0]
                    integrity_statuses.append(status)
                except Exception:
                    pass

        if len(integrity_statuses) < 6:
            return None

        ok = all(x == "Good" for x in integrity_statuses[:6])

        return not ok

    except Exception:
        return None


def part2_mem_available_mb(path: str) -> Tuple[Optional[float], Optional[bool]]:
    target = "/dev/ubivol/part2"

    for line in _read_lines(path):
        if target not in line:
            continue

        parts = line.split()
        if len(parts) < 4:
            return None, None

        mem_str = parts[3].strip().lower()

        m = re.match(r"([0-9.]+)\s*([gmk]?)", mem_str)
        if not m:
            return None, None

        value = float(m.group(1))
        suffix = m.group(2)

        if suffix == "g":
            mb = value * 1024
        elif suffix == "k":
            mb = value / 1024
        elif suffix == "m":
            mb = value
        else:
            mb = value

        return mb, mb < 80.0

    return None, None

def part1_mem_available_mb(path: str) -> Tuple[Optional[float], Optional[bool]]:
    target = "/dev/ubivol/part1"

    for line in _read_lines(path):
        if target not in line:
            continue

        parts = line.split()
        if len(parts) < 4:
            return None, None

        mem_str = parts[3].strip().lower()

        m = re.match(r"([0-9.]+)\s*([gmk]?)", mem_str)
        if not m:
            return None, None

        value = float(m.group(1))
        suffix = m.group(2)

        if suffix == "g":
            mb = value * 1024
        elif suffix == "k":
            mb = value / 1024
        elif suffix == "m":
            mb = value
        else:
            mb = value

        return mb, mb < 80.0

    return None, None
def analyze_logs(log_dir: str):

    recovery_option_image_partition_swap = []
    recovery_option_devshell = []
    recovery_option_simple_archive_download = []
    recovery_option_image_integrity_check_failed = []
    recovery_option_partition_safe_but_clean_up_reccomended = []
    # NEW: per-AP partition info, keyed by "ap_name|ap_ip", so we can attach
    # Active Boot Part + free-space-on-both-partitions data to each row later
    # without touching the many existing recovery_option_*.append(...) tuples.
    ap_partition_info: Dict[str, Dict[str, object]] = {}

    status_rows: List[Dict[str, str]] = []
    print("\n" + "=" * 80)
    print("FLASH CHECKER DEBUG START")
    print("=" * 80)
    print("DEBUG: analyze_logs running on:", os.path.abspath(log_dir))
    print("DEBUG: Directory exists:", os.path.exists(log_dir))
    # REPLACE WITH:
    print("DEBUG: Files in directory (recursive):")
    file_list = []
    for dirpath, dirnames, filenames in os.walk(log_dir):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            file_list.append((fn, fp))
            print(f"FOUND FILE: {fp}")

    for fn, fp in file_list:
        if fn.startswith("Status_check_results_"):
            continue
        if not fn.lower().endswith(".log"):
            continue
        print(f"\n[PARSER] PROCESSING: {fp}")
        ap_name = ap_hostname_from_run_header(fp) or fn
        ap_model_sig, ap_model_check = ap_model_from_log(fp)
        ap_ip = ap_ip_from_run_header(fp)
        print(f"[PARSER] AP Name      : {ap_name}")
        print(f"[PARSER] AP Model     : {ap_model_sig}")
        print(f"[PARSER] AP IP        : {ap_ip}")
        print(f"[PARSER] Model Allowed: {ap_model_check}")
        if ap_model_sig is None:
            ap_model_sig = "UNKNOWN"

        cnss = cnssdaemon_log_present(fp)
        primary_image, prim_buggy = primary_version_check(fp)
        backup_image, back_buggy = backup_version_check(fp)
        part, part1 = current_boot_partition(fp)
        integ_fail = image_integrity_failed(fp)
        mem_mb, mem_low = part2_mem_available_mb(fp)
        part1_mem_mb, part1_mem_low = part1_mem_available_mb(fp)   # NEW

        # NEW: figure out which partition a new image install would actually
        # land on (the partition the AP is NOT currently booted from), and
        # use THAT partition's free space for the "low memory" decisions
        # below instead of always assuming part2.
        if part == "part1":
            target_part_name = "part2"
            target_mem_mb, target_mem_low = mem_mb, mem_low
        elif part == "part2":
            target_part_name = "part1"
            target_mem_mb, target_mem_low = part1_mem_mb, part1_mem_low
        else:
            # Couldn't detect active partition — fall back to old behavior
            target_part_name = "part2"
            target_mem_mb, target_mem_low = mem_mb, mem_low
        # NEW: special case — booting from part2, part1 has enough room,
        # only part2 is low. Not a devshell scenario, just informational.
        part1_ok_part2_low = (
            part == "part2"
            and part1_mem_mb is not None and part1_mem_mb >= 80.0
            and mem_mb is not None and mem_mb < 80.0
        )
        special_note = None
        if part1_ok_part2_low:
            special_note = (
                f"AP is booting from part2. Part1 has sufficient free space "
                f"({part1_mem_mb:.1f} MB) for image installation. "
                f"Low free space detected only in part2."
            )
        # NEW: stash raw partition facts for this AP so they can be attached
        # to the final vulnerable_rows entry later (see add_rows below).
        ap_partition_info[f"{ap_name}|{ap_ip}"] = {
            "active_boot_part": part or "unknown",
            "part1_free_mb": part1_mem_mb,
            "part2_free_mb": mem_mb,
            "special_note": special_note,
        }

        print(f"[PARSER] cnssdaemon present : {cnss}")
        print(f"[PARSER] Primary Image     : {primary_image}")
        print(f"[PARSER] Primary Buggy     : {prim_buggy}")
        print(f"[PARSER] Backup Image      : {backup_image}")
        print(f"[PARSER] Backup Buggy      : {back_buggy}")
        print(f"[PARSER] Boot Partition    : {part}")
        print(f"[PARSER] Is Part1          : {part1}")
        print(f"[PARSER] Integrity Failed  : {integ_fail}")
        print(f"[PARSER] Free MB Part2     : {mem_mb}")
        print(f"[PARSER] Low Memory Flag   : {mem_low}")

        # ------------------------------
        # Build Status Table Row
        # ------------------------------
        status_rows.append({
            "AP Name": ap_name,
            "Model": ap_model_sig or "",
            "Primary Image": primary_image or "",
            "Primary Buggy": str(prim_buggy),
            "Backup Image": backup_image or "",
            "Backup Buggy": str(back_buggy),
            "Boot Partition": part or "",
            "Image Integrity Failed": str(integ_fail),
            "Part1 Free MB": f"{part1_mem_mb:.2f}" if part1_mem_mb is not None else "",
            "Part2 Free MB": f"{mem_mb:.2f}" if mem_mb is not None else "",
            "Low Memory": str(mem_low)
        })

        # ------------------------------
        # Recovery Logic (UNCHANGED)
        # ------------------------------

        ap_failures = []  # ✅ NEW per-AP failure collector

        if integ_fail is True:
            ap_failures.append(("IMAGE_INTEGRITY", "Image integrity failed"))

        if target_mem_mb is not None and target_mem_mb < 20.0:
            ap_failures.append(("LOW_MEMORY_CRITICAL", f"Very low memory in part2 [{mem_mb:.1f} MB]"))

        elif target_mem_low:
            ap_failures.append(("LOW_MEMORY_80", f"Low memory in part2 [{mem_mb:.1f} MB]"))

        elif part1_ok_part2_low:
            ap_failures.append(("PART1_OK_PART2_LOW", special_note))
        if ap_model_check:
            if cnss:
                if prim_buggy:
                    if part1:
                        if target_mem_low:
                            ap_failures.append(("PARTITION_SWAP", "Partition swap required"))
                    else:
                        if target_mem_low and target_mem_mb is not None and target_mem_mb < 20.0:
                            ap_failures.append(("LOW_FLASH", "Low flash cleanup needed"))
                        else:
                            if back_buggy:
                                if target_mem_low:
                                    ap_failures.append(("BUGGY_BACKUP_LOW_MEM", "Backup buggy + low flash"))
                                else:
                                    ap_failures.append(("BUGGY_BACKUP", "Backup image is buggy"))
                else:
                        if back_buggy:
                                if target_mem_low:
                                    ap_failures.append(("BUGGY_BACKUP_LOW_MEM", "Backup buggy + low flash"))
                                else:
                                    ap_failures.append(("BUGGY_BACKUP", "Backup image is buggy"))
        print("[PARSER] Failure List:")
        for code, desc in ap_failures:
            print(f"    {code} -> {desc}")

        if not ap_failures:
            print("[PARSER] RESULT: AP NOT MARKED VULNERABLE")
        else:
            print("[PARSER] RESULT: AP MARKED VULNERABLE")
        if ap_failures:
            if len(ap_failures) == 1:
                # ✅ KEEP EXISTING BEHAVIOR (NO CHANGE)
                code, _ = ap_failures[0]

                if code == "IMAGE_INTEGRITY":
                    recovery_option_image_integrity_check_failed.append((ap_name, ap_model_sig, ap_ip))

                elif code == "LOW_MEMORY_CRITICAL":
                    recovery_option_devshell.append((ap_name, ap_model_sig, ap_ip))

                elif code == "PARTITION_SWAP":
                    recovery_option_image_partition_swap.append((ap_name, ap_model_sig, ap_ip))


                elif code == "BUGGY_BACKUP":

                    recovery_option_simple_archive_download.append((ap_name, ap_model_sig, ap_ip))


                elif code == "BUGGY_BACKUP_LOW_MEM":

                    recovery_option_partition_safe_but_clean_up_reccomended.append((ap_name, ap_model_sig, ap_ip))

                elif code == "LOW_FLASH":
                    recovery_option_partition_safe_but_clean_up_reccomended.append((ap_name, ap_model_sig, ap_ip))
                elif code == "LOW_MEMORY_80":
                    recovery_option_partition_safe_but_clean_up_reccomended.append((ap_name, ap_model_sig, ap_ip))
                elif code == "PART1_OK_PART2_LOW":
                    recovery_option_partition_safe_but_clean_up_reccomended.append((ap_name, ap_model_sig, ap_ip))

            else:
                # ✅ MULTIPLE FAILURES → COMBINED ENTRY
                failure_desc = ", ".join([desc for _, desc in ap_failures])

                recovery_option_devshell.append(
                    (ap_name, f"{ap_model_sig} [MULTI: {failure_desc}]", ap_ip)
                )
    # ---------------------------------------------------
    # Write Status Check Summary File
    # ---------------------------------------------------
    # ---------------------------------------------------
    # Write Status Check Summary File (FULL TABLE + RECOVERY)
    # ---------------------------------------------------
    has_vulnerable_aps = any([
        recovery_option_image_partition_swap,
        recovery_option_devshell,
        recovery_option_simple_archive_download,
        recovery_option_image_integrity_check_failed,
        recovery_option_partition_safe_but_clean_up_reccomended
    ])

    output_file = ""
    if status_rows:

        folder_name = os.path.basename(log_dir)
        output_file = os.path.join(
            log_dir,
            f"Status_check_results_{folder_name}.log"
        )

        with open(output_file, "a", encoding="utf-8") as f:

            f.write("\n============================================================\n")
            f.write(f"Flash Checker Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("============================================================\n\n")

            f.write("=========== AP FLASH CHECK STATUS SUMMARY ===========\n\n")

            # Define headers in correct order
            headers = [
                "AP Name",
                "Model",
                "Primary Image",
                "Primary Buggy",
                "Backup Image",
                "Backup Buggy",
                "Boot Partition",
                "Image Integrity Failed",
                "Part1 Free MB",
                "Part2 Free MB",
                "Low Memory"
            ]

            # Column width (increase for cleaner spacing)
            col_width = 22

            # Print header row
            for h in headers:
                f.write(h.ljust(col_width))
            f.write("\n")

            # Print separator line
            f.write("-" * (col_width * len(headers)))
            f.write("\n")

            # Print each AP row
            for row in status_rows:
                for h in headers:
                    value = str(row.get(h, ""))
                    f.write(value.ljust(col_width))
                f.write("\n")
            if not has_vulnerable_aps:
                f.write("\nNo AP flash issues detected.\n")
            # Add Recovery Section
            f.write("\n\n=========== RECOVERY SUMMARY ===========\n\n")

            def write_recovery(title, items):
                if items:
                    f.write(title + "\n")
                    for name, model, ip in items:
                        f.write(f"  - {name} ({model}) [{ip}]\n")
                    f.write("\n")

            write_recovery("Recover with image partition swap", recovery_option_image_partition_swap)
            write_recovery("Recover with devshell", recovery_option_devshell)
            write_recovery("Safe state but buggy backup image", recovery_option_simple_archive_download)
            write_recovery("Image integrity failed", recovery_option_image_integrity_check_failed)
            write_recovery("Partition safe but low flash", recovery_option_partition_safe_but_clean_up_reccomended)

            if not has_vulnerable_aps:
                f.write("No recovery actions required.\n")

    # ---------------------------------------------------
    # Build GUI Vulnerable Table (unchanged)
    # ---------------------------------------------------

    vulnerable_rows: List[Dict[str, str]] = []

    def add_rows(items, recovery):
        for name, model, ip in items:
            info = ap_partition_info.get(f"{name}|{ip}", {})
            active_part = info.get("active_boot_part", "unknown")
            p1 = info.get("part1_free_mb")
            p2 = info.get("part2_free_mb")

            def _fmt(v):
                return f"{v:.1f} MB" if v is not None else "N/A"

            # Human-readable note so TAC/customers can see both partitions'
            # free space at a glance, e.g.:
            # "Active: part2 | part1 free: 177.8 MB | part2 free: 73.6 MB"
            partition_note = info.get("special_note") or (
                f"Active: {active_part} | part1 free: {_fmt(p1)} | part2 free: {_fmt(p2)}"
            )

            vulnerable_rows.append({
                "ap_name": name,
                "ap_model": model or "",
                "ap_ip": ip or "",
                "recovery": recovery,
                "active_boot_part": active_part,
                "partition_note": partition_note
            })

    add_rows(recovery_option_image_partition_swap, "Recover with image partition swap")
    add_rows(recovery_option_devshell, "Recover with devshell")
    add_rows(recovery_option_simple_archive_download, "Safe state but AP has buggy image in the backup partition")
    add_rows(recovery_option_image_integrity_check_failed, "Image integrity check has failed for these APs")
    add_rows(recovery_option_partition_safe_but_clean_up_reccomended, "Partition is safe but the flash storage is low")
    
    print("DEBUG: analyze_logs running on:", log_dir)

    # ---------------- BUILD SUMMARY TEXT ----------------

    summary_lines = []


    if not has_vulnerable_aps:
        summary_lines.append("No recovery actions required.")
    for ap_name, ap_model,ap_ip in recovery_option_image_partition_swap:
        summary_lines.append(f"{ap_name} ({ap_model}) [{ap_ip}]-> IMAGE PARTITION SWAP")

    for ap_name, ap_model, ap_ip in recovery_option_devshell:
        summary_lines.append(f"{ap_name} ({ap_model}) [{ap_ip}] -> DEV SHELL RECOVERY")

    for ap_name, ap_model, ap_ip in recovery_option_simple_archive_download:
        summary_lines.append(f"{ap_name} ({ap_model}) [{ap_ip}] -> SIMPLE ARCHIVE DOWNLOAD")
    for ap_name, ap_model, ap_ip in recovery_option_image_integrity_check_failed:
        summary_lines.append(
            f"{ap_name} ({ap_model}) [{ap_ip}] -> IMAGE INTEGRITY FAILED"
        )
    for ap_name, ap_model, ap_ip in recovery_option_partition_safe_but_clean_up_reccomended:
        note = ap_partition_info.get(f"{ap_name}|{ap_ip}", {}).get("special_note")
        if note:
            summary_lines.append(f"{ap_name} ({ap_model}) [{ap_ip}] -> {note}")
        else:
            summary_lines.append(
                f"{ap_name} ({ap_model}) [{ap_ip}] -> PARTITION SAFE BUT LOW FLASH"
            )

    summary_text = "\n".join(summary_lines)
    if not output_file:
        return [], ""
    summary_filename = output_file




    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



    with open(summary_filename, "a", encoding="utf-8") as f:
        vuln_count = len(vulnerable_rows)

        f.write("\n=========== SUSCEPTIBILITY SUMMARY ===========\n\n")
        f.write(f"Total Susceptible APs: {vuln_count}\n")
        f.write("\n\n=========== QUICK RECOVERY SUMMARY ===========\n\n")
        f.write(summary_text)
    print("DEBUG summary_filename:", summary_filename)

    return vulnerable_rows, summary_filename
def ap_ip_from_run_header(fp: str) -> str:
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # First try header style
        m = re.search(r"[Ii]p='([^']+)'", content)
        if m:
            return m.group(1)

        # Then try GOT IP[10.x.x.x] format
        m = re.search(r"GOT IP\[(.*?)\]", content)
        if m:
            return m.group(1)

        return ""
    except Exception:
        return ""



