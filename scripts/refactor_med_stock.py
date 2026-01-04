
import os

target_file = r"d:\test\GUI-SeniorCare-Pro\views\medication_stock_view.py"

def refactor_file():
    with open(target_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []

    # 1. Keep Imports (1-52)
    # Note: lists are 0-indexed, so lines[0:52] covers 1-52
    new_lines.extend(lines[0:52])

    # Add new component imports
    new_lines.append("\n# Helper and View Imports\n")
    new_lines.append("from utils.helpers import show_onboard, hide_onboard, create_entry_with_keyboard, toggle_language, get_role_theme\n")
    # new_lines.append("from views.home_view import HomePage\n") 
    # NOTE: HomePage might cause circular import if HomePage imports Frame2. 
    # Use local import inside methods if needed, or rely on controller.show_frame class reference (which might be passed as type)
    # But usually views import each other for Navigation keys.
    # To be safe, we add it, but if circular, we move to inside functions.
    
    # 2. Keep Server Imports (145-168)
    # 53-144 was VoicePromptPlayer (Deleted)
    new_lines.extend(lines[144:168])

    # 169-413 was Helpers (Deleted, now imported)
    
    # 414-736 was login (Deleted)
    # 737-2472 was HomePage (Deleted)

    # 3. Keep Frame2 (2473-2995)
    # Adjust indices: 2472 to 2995
    new_lines.extend(lines[2472:2995])

    # 2996-3410 was Frame3, HealthNumpad, Frame4 (Deleted)

    # 4. Keep add_Frame (3411-3662)
    # Adjust indices: 3410 to 3662
    new_lines.extend(lines[3410:3662])

    # 3663-End was AIgen, MainApp etc (Deleted)

    # Write back
    with open(target_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print(f"Refactoring complete. New line count: {len(new_lines)}")

if __name__ == "__main__":
    refactor_file()
