def generate_fall_alert_message():
    return {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box",
            "layout": "horizontal", # Icon and Text side by side
            "contents": [
                {
                    "type": "text",
                    "text": "⚠️",
                    "size": "xxl",
                    "flex": 0,
                    "align": "center",
                    "gravity": "center"
                },
                {
                    "type": "text",
                    "text": " แจ้งเตือนฉุกเฉิน",
                    "weight": "bold",
                    "color": "#FFFFFF",
                    "size": "xl",
                    "flex": 1,
                    "gravity": "center",
                    "margin": "sm"
                }
            ],
            "backgroundColor": "#C62828", # Red background like the image
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "ตรวจพบการล้ม (Fall Detected)",
                    "weight": "bold",
                    "size": "xl",
                    "wrap": True,
                    "color": "#000000"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": "#E0E0E0"
                },
                {
                    "type": "text",
                    "text": "กรุณาตรวจสอบผู้ป่วยและให้ความช่วยเหลือโดยด่วน",
                    "margin": "lg",
                    "wrap": True,
                    "color": "#666666",
                    "size": "md",
                    "lineSpacing": "6px"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "SeniorCarePro AI System",
                            "color": "#BFBFBF",
                            "size": "sm",
                            "align": "center"
                        }
                    ],
                    "margin": "xxl",
                    "paddingTop": "xl"
                }
            ],
            "paddingAll": "20px"
        }
    }
