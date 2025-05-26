from server.Database import Database
from mysql.connector import Error


class eat_medicine_report:
    def __init__(self):
        self.Database = Database()
    
    def get_eatmedic(self,id):
        try:
            sql = '''SELECT 
                        e.time_get,
                        e.medicine_get,
                        m1.medicine_name AS medicine_1,
                        m2.medicine_name AS medicine_2,
                        m3.medicine_name AS medicine_3,
                        m4.medicine_name AS medicine_4
                    FROM tb_data_eat_medicine e
                    LEFT JOIN tb_medicine m1 ON e.medicine_id = m1.medicine_id
                    LEFT JOIN tb_medicine m2 ON e.medicine_id2 = m2.medicine_id
                    LEFT JOIN tb_medicine m3 ON e.medicine_id3 = m3.medicine_id
                    LEFT JOIN tb_medicine m4 ON e.medicine_id4 = m4.medicine_id
                    WHERE e.id = %s
                    ORDER BY e.time_get ASC '''
            self.Database.cursor.execute(sql, (id,))
            result = self.Database.cursor.fetchall()
            return {'status': True, 'data': result}
        except Error as e:
            return {'status': False, 'message': str(e)}