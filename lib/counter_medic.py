import json
def countermidecine(count):

    try:
        with open('user_data.json','r',encoding='utf-8') as f:
            data = json.load(f)

            data['count_medicine'] = count

        with open('user_data.json','w',encoding='utf-8') as f:
            json.dump(data,f,indent=4,ensure_ascii=False)
    except Exception as e:
        print(f"Error updating count_medicine: {e}")