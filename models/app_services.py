# ------------------ ฝั่ง server------------------------
from server.auth import auth
from server.info import infoData
from server.managemedic import manageMedicData
from server.setting_time import setting_eat_time
from server.gemini import Gemini
from server.heart_report import heart_report
from server.eat_medicine_report import eat_medicine_report
# from server.exportpdf import generate_pdf_sync # might be a function
from server.setcounter import SetCounter
from server.device_status import Devicestatus

# Create instances
auth_service = auth()
manage_data = infoData()
manage_medic = manageMedicData()
set_dispensing_time = setting_eat_time()
ai_service = Gemini()
set_counter = SetCounter()
heart_report_service = heart_report()
medicine_report_service = eat_medicine_report()
device_status_service = Devicestatus()
