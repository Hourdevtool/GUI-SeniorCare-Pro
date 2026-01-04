
import os

source_file = r"d:\test\GUI-SeniorCare-Pro\main.py" 
target_file = r"d:\test\GUI-SeniorCare-Pro\controllers\app_controller.py"

def extract_controller():
    if not os.path.exists(source_file):
        print("Source file not found based on current directory.")
        # Try absolute path
        if not os.path.exists(r"d:\test\GUI-SeniorCare-Pro\main.py"):
            print("Source file main.py definitely not found.")
            return

    with open(source_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 1. Imports (Lines 1-52 and 144-168 from original structure)
    new_lines = []
    new_lines.extend(lines[0:52])
    new_lines.extend(lines[144:168])
    
    # Add View Imports
    new_lines.append("\n# View Imports\n")
    new_lines.append("from views.login_view import login\n")
    new_lines.append("from views.home_view import HomePage\n")
    new_lines.append("from views.medication_stock_view import Frame2, add_Frame\n")
    new_lines.append("from views.schedule_setup_view import Frame3, MedicationScheduleFrame, TimeNumpad, DatePicker, MedicationApp\n")
    new_lines.append("from views.health_view import Frame4, HealthNumpad, AIgen\n")
    new_lines.append("from views.report_view import ReportFrame, Report1, Report2\n")
    new_lines.append("from views.user_info_view import info, Wificonnect\n")
    
    # Add Model/Utils Imports
    new_lines.append("from models.voice_service import VoicePromptPlayer\n")
    new_lines.append("import utils.helpers as helpers\n")
    new_lines.append("from utils.helpers import *\n")

    # 2. MainApp Class
    # Find start line
    start_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("class MainApp"):
            start_index = i
            break
            
    if start_index == -1:
        print("Could not find class MainApp")
        return

    controller_code = lines[start_index:]
    
    # Rename class MainApp to AppController within the definition line
    controller_code[0] = controller_code[0].replace("class MainApp", "class AppController")
    
    new_lines.extend(controller_code)
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print(f"AppController extracted to {target_file} with {len(new_lines)} lines.")

if __name__ == "__main__":
    extract_controller()
