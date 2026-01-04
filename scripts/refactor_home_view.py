
import os

target_file = r"d:\test\GUI-SeniorCare-Pro\views\home_view.py"

def refactor_home():
    with open(target_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []

    # 1. Imports (1-52)
    new_lines.extend(lines[0:52])
    
    # 2. Skip VoicePromptPlayer (53-144)
    # 3. Imports/Helpers/HomePage (145-2653)
    # Check line 416 is HomePage?
    # Ensure we capture up to where Frame3 starts (2654)
    # indices: 144 to 2653 (lines 145 to 2654)
    
    # We want to keep everything from 145 up to 2653.
    # But wait, findstr 53: VoicePromptPlayer. 
    # findstr 416: HomePage. 
    # So 145-415 are helpers/login remnants? 
    # If login is gone, 145-415 must be helpers.
    
    chunk_middle = lines[144:2653]
    
    # Process chunk_middle to insert Frame2 import
    modified_chunk = []
    import_inserted = False
    
    for line in chunk_middle:
        modified_chunk.append(line)
        # Look for injection point
        if "if user_role in ['admin', 'user']:" in line and "reset_icon" not in line and not import_inserted:
            # Check context: inside create_counter_medicine_display (around line 1193 in previous view, likely different here)
            # We blindly insert. 
            modified_chunk.append("                    from views.medication_stock_view import Frame2\n")
            import_inserted = True
            
    new_lines.extend(modified_chunk)

    # 4. Skip Frame3+ (2654-End)
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    print(f"Refactor home_view complete. Lines: {len(new_lines)}")

if __name__ == "__main__":
    refactor_home()
