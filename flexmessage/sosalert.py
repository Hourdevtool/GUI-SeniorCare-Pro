def generateflexmessage(url):


    return   {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
            {
                "type": "text",
                "text": "Videocall"
            }
            ]
        },
        "hero": {
            "type": "image",
            "url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcThpqL5HiVQZB6-jZN_uVyd75dmzlfRaVV_Fw&s",
            "size": "full",
            "aspectRatio": "2:1"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
            {
                "type": "text",
                "text": "กดปุ่มด้านล่างเพื่อเริ่มต้นการสนทนา"
            },
             {
                "type": "button",
                "style": "primary",
                "action": {
                "type": "uri",
                "label": "เริ่มต้นการสนทนา",
                    "uri": url
                 }
             } 
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
            {
                "type": "text",
                "text": "SeniorCarePro",
                "align": "center"
            }
            ]
        }
        }



        