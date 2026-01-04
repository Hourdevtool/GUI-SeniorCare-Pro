import customtkinter as ctk

# Hospital-friendly, simple, high-contrast palette
WORD_COLOR = '#213547'        # Neutral dark for text
BOTTOM_HOVER_COLOR = "#E03131"      # Destructive hover (soft red)
HO_COLOR = "#2FBF71"          # Secondary accent (soft green)
SELECT_COLOR = '#A7E3C6'      # Selection/confirm accents

BACK_COLOR = '#F5FAFF'        # Very light blue background
FORCE_COLOR = '#2F6AA3'       # Primary action color (calm hospital blue)
TEXT_MAIN_COLOR = '#1E293B'         # Main text color
HOVER_COLOR = "#255A8A"       # Primary hover (slightly darker blue)
INPUT_bg_COLOR = "#FFFFFF"       # Inputs: white for cleanliness
INPUT_TEXT_COLOR = "#0B1220"       # Input text: near-black for readability

# Generic assignments (mapping back to original variable names if needed for easy refactoring)
word_color = WORD_COLOR
bottom_hover = BOTTOM_HOVER_COLOR
ho_color = HO_COLOR
select_color = SELECT_COLOR
back_color = BACK_COLOR
force_color = FORCE_COLOR
text_main = TEXT_MAIN_COLOR
hover_color = HOVER_COLOR
input_color = INPUT_bg_COLOR
input_text = INPUT_TEXT_COLOR


# Global UI style constants (scaled for 1024x600)
BUTTON_RADIUS = 15            # ปรับมุมโค้งให้เหมาะสม
TITLE_FONT_SIZE = 30          # ลดจาก 56
SECTION_TITLE_SIZE = 22
LABEL_FONT_FAMILY = "Arial"

# ===== Role-Based Theme System =====
# ระบบแต่งตกแยกตามระดับผู้ใช้ (Admin, User, Patient)
ROLE_THEMES = {
    'admin': {
        'name': 'ผู้ดูแลระบบ',
        'button': {
            'fg_color': '#F8FAFC',         # สีน้ำเงินจางลง - ดูนุ่มนวลขึ้น
            'hover_color': '#5A9BC4',      # สีน้ำเงินเข้มขึ้นเล็กน้อยเมื่อ hover
            'text_color': 'black',       # ข้อความสีขาว
            'border_color': '#5CA95C',     # ขอบสีน้ำเงินอ่อน
            'border_width': 2,
            'corner_radius': 0
        },
        'frame': {
            'fg_color': '#FFFFFF',         # พื้นหลังสีขาว
            'bg_color': '#000001',          # พื้นหลังหลัก
            'border_color': '#E2E8F0',     # ขอบสีเทาอ่อน
            'border_width': 2
        },
        'info_box': {
            'fg_color': '#F7FAFC',         # พื้นหลังกล่องข้อมูล
            'border_color': '#CBD5E0',     # ขอบกล่องข้อมูล
            'header_color': '#EDF2F7'      # สีหัวข้อ
        },
        'accent': '#2563EB',               # สีเน้น (น้ำเงิน)
        'layout': {
            'medicine_frame': {'x': 20, 'y': 280, 'width': 300, 'height': 300},
            'medication_frame': {'x': 340, 'y': 280, 'width': 340, 'height': 300},
            'user_info_frame': {'x': 700, 'y': 280, 'width': 300, 'height': 300},
            'menu_buttons': {'start_x': 30, 'start_y': 600, 'spacing': 40, 'btn_width': 100, 'btn_height': 90}
        }
    },
    'user': {
        'name': 'ผู้ใช้งาน',
        'button': {
            'fg_color': '#F8FAFC',         # สีน้ำเงินจางลง - ดูนุ่มนวลขึ้น
            'hover_color': '#5A9BC4',      # สีน้ำเงินเข้มขึ้นเล็กน้อยเมื่อ hover
            'text_color': 'black',       # ข้อความสีขาว
            'border_color': '#5CA95C',     # ขอบสีน้ำเงินอ่อน
            'border_width': 2,
            'corner_radius': 0
        },
        'frame': {
            'fg_color': '#FFFFFF',         # พื้นหลังสีขาว
            'bg_color': '#000001',         # พื้นหลังหลัก
            'border_color': '#B8D4F0',     # ขอบสีน้ำเงินอ่อน
            'border_width': 2
        },
        'info_box': {
            'fg_color': '#E8F4FD',         # พื้นหลังกล่องข้อมูล (น้ำเงินอ่อน)
            'border_color': '#A8DADC',     # ขอบกล่องข้อมูล
            'header_color': '#D1ECF1'      # สีหัวข้อ
        },
        'accent': '#2F6AA3',               # สีเน้น (น้ำเงิน)
        'layout': {
            'medicine_frame': {'x': 20, 'y': 280, 'width': 300, 'height': 300},
            'medication_frame': {'x': 340, 'y': 280, 'width': 340, 'height': 300},
            'user_info_frame': {'x': 700, 'y': 280, 'width': 300, 'height': 300},
            'menu_buttons': {'start_x':60, 'start_y': 600, 'spacing': 100, 'btn_width': 100, 'btn_height': 90}
        }
    },
    'patient': {
        'name': 'ผู้ป่วย',
        'button': {
            'fg_color': '#FFFFFF',         # สีขาว - ดูสะอาด
            'hover_color': '#E9ECEF',      # สีเทาอ่อนเมื่อ hover
            'text_color': '#1D3557',       # ข้อความสีน้ำเงินเข้ม
            'border_color': '#A8DADC',     # ขอบสีฟ้าอ่อน
            'border_width': 2,
            'corner_radius': 0
        },
        'frame': {
            'fg_color': '#FFFFFF',         # พื้นหลังสีขาว
            'bg_color': '#000001',         # พื้นหลังหลัก
            'border_color': '#E8F4FD',     # ขอบสีฟ้าอ่อนมาก
            'border_width': 2
        },
        'info_box': {
            'fg_color': '#F8F9FA',         # พื้นหลังกล่องข้อมูล
            'border_color': '#DEE2E6',     # ขอบกล่องข้อมูล
            'header_color': '#E8F4FD'      # สีหัวข้อ
        },
        'accent': '#8acaef',               # สีเน้น (ฟ้าอ่อน)
        'layout': {
            # ปรับตำแหน่งและขนาดให้เหมาะสมกับหน้าจอ 1024x600
            # จำนวนยาคงเหลือ - ด้านซ้าย, ขนาดใหญ่ขึ้น
            'medicine_frame': {'x': 20, 'y': 280, 'width': 360, 'height': 280},
            # การตั้งค่ายา - ตรงกลาง, ขนาดใหญ่ขึ้น
            'medication_frame': {'x': 400, 'y': 280, 'width': 600, 'height': 280},
            # ข้อมูลผู้ใช้ - ด้านขวา, ขนาดใหญ่ขึ้น
            'user_info_frame': {'x': 20, 'y': 570, 'width': 850, 'height': 220},
            # ปุ่มเมนู - ปรับตำแหน่งให้อยู่ด้านล่าง
            'menu_buttons': {'start_x': 910, 'start_y': 570, 'btn_width': 100, 'btn_height': 90}
        }
    }
}
