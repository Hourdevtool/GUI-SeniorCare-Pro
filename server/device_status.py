import requests
import json
class Devicestatus:

    def setstatus(self, id, status):
        url = f"http://medic.ctnphrae.com/php/status.php?device={id}&status={status}"
        json_text = "" 
        try:
            response = requests.get(url)
            response.raise_for_status()
            print(response.text )
            ral_text = response.text 
            json_start = ral_text.find('{')
            if json_start == -1:
                print(f"Error: ไม่พบ JSON ใน response: {ral_text}")
                return None
            json_text = ral_text[json_start:]
            return json.loads(json_text)
        except requests.exceptions.RequestException as e:
            print(f"Connection Error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Text ที่พยายามจะอ่าน: {json_text}")
            return None


