import mysql.connector
from mysql.connector import Error
class Database:
    def __init__(self):
        try:
            self.conn  = mysql.connector.connect(
                host ='localhost',
                port = '5000',
                user = 'root',
                password = 'root',
                database = 'ctnphrae_medic',
            )

            if self.conn.is_connected():
                self.cursor = self.conn.cursor(dictionary=True, buffered=True);
        except Error as e :
            print(f"❌ เชื่อมต่อฐานข้อมูลล้มเหลว: {e}");
