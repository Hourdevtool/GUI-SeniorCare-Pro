
import os

source_file = r"d:\test\GUI-SeniorCare-Pro\views\schedule_setup_view.py"
# Mapping of target files to list of line ranges (start, end) inclusive 0-indexed logic (start_line-1 : end_line-1)
# Note: Python slice [start:end] excludes end. So we use (start_line-1, end_line)

# Line numbers from findstr are 1-based.
# Frame2: 2794
# Frame3: 2996
# HealthNumpad: 3145
# Frame4: 3250
# add_Frame: 3411
# AIgen: 3663
# TimeNumpad: 3774
# MedicationApp: 3851
# info: 4425
# MedicationScheduleFrame: 4637
# DatePicker: 4960
# ReportFrame: 5013
# Report1: 5118
# Report2: 5393
# Wificonnect: 5648
# MainApp: 6061

def get_ranges(lines):
    return {
        "imports": lines[0:52] + lines[144:168],
        "Frame2": lines[2793:2995],
        "Frame3": lines[2995:3144],
        "HealthNumpad": lines[3144:3249],
        "Frame4": lines[3249:3410],
        "add_Frame": lines[3410:3662],
        "AIgen": lines[3662:3773],
        "TimeNumpad": lines[3773:3850],
        "MedicationApp": lines[3850:4424],
        "info": lines[4424:4636],
        "MedicationScheduleFrame": lines[4636:4959],
        "DatePicker": lines[4959:5012],
        "ReportFrame": lines[5012:5117],
        "Report1": lines[5117:5392],
        "Report2": lines[5392:5647],
        "Wificonnect": lines[5647:6060],
    }

def write_view(filename, content_keys, ranges):
    base_dir = r"d:\test\GUI-SeniorCare-Pro\views"
    path = os.path.join(base_dir, filename)
    
    new_lines = []
    # Imports
    new_lines.extend(ranges["imports"])
    new_lines.append("\n# Helper and View Imports\n")
    new_lines.append("from utils.helpers import show_onboard, hide_onboard, create_entry_with_keyboard, toggle_language, get_role_theme\n")
    new_lines.append("from views.home_view import HomePage\n")
    new_lines.append("from models.voice_service import VoicePromptPlayer\n") 
    new_lines.append("\n")

    for key in content_keys:
        if key in ranges:
            new_lines.extend(ranges[key])
            new_lines.append("\n") # Spacer
        else:
            print(f"Warning: Key {key} not found in ranges")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Wrote {filename} with {len(new_lines)} lines.")

def main():
    if not os.path.exists(source_file):
        print(f"Source file not found: {source_file}")
        return

    with open(source_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    ranges = get_ranges(lines)

    # 1. Medication Stock View
    write_view("medication_stock_view.py", ["Frame2", "add_Frame", "MedicationApp"], ranges)

    # 2. Schedule Setup View
    write_view("schedule_setup_view.py", ["Frame3", "TimeNumpad", "MedicationScheduleFrame", "DatePicker"], ranges)

    # 3. Health View
    write_view("health_view.py", ["HealthNumpad", "Frame4", "AIgen"], ranges)

    # 4. Report View
    write_view("report_view.py", ["ReportFrame", "Report1", "Report2"], ranges)

    # 5. User Info View
    write_view("user_info_view.py", ["info", "Wificonnect"], ranges)

if __name__ == "__main__":
    main()
