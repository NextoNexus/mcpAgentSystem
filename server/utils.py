import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

class LoginValidater:
    '''用户登录验证器'''

    def __init__(self, db_name, db_username, db_password, db_host, db_port, table_name):
        self.db_name = db_name
        self.db_username = db_username
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.table_name = table_name

        self.cursor = None
        self.conn = None

    def connect_db(self):
        # 数据库连接参数
        conn_params = {
            'dbname': self.db_name,  # 你的数据库名
            'user': self.db_username,  # 你的数据库用户名
            'password': self.db_password,  # 你的数据库密码
            'host': self.db_host,  # 数据库服务器地址，通常是localhost或IP地址
            'port': self.db_port  # 端口号，默认是5432
        }
        self.conn = psycopg2.connect(**conn_params)
        self.cursor = self.conn.cursor()
        # 执行SQL查询
        self.cursor.execute("SELECT version();")

        # 获取查询结果
        record = self.cursor.fetchone()
        print("You are connected to : ", record)
        return True

    def validate_login(self, username, password):
        sql_script = f"SELECT username,password FROM {self.table_name} WHERE username = %s"
        self.cursor.execute(sql_script, (username,))
        rows = self.cursor.fetchall()  # 获取所有行
        if len(rows) == 0: return (False,False)
        for (usr, pwd) in rows:
            if pwd == password: return (True, True)
        return (True, False)

    def on_close(self):
        self.conn.close()
        self.cursor.close()


if __name__ == '__main__':
    print('start...')
    l = LoginValidater('dgjt', 'postgres', '123456', 'localhost', '5432', 'schema_user.user_login')
    res = l.connect_db()
    (a, b) = l.validate_login("邹浩男", "123456")
    print(a, b)
    l.on_close()
