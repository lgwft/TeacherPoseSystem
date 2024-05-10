from database_utils import md5

def login_sql(username, password):
    sql = f"select * from administrator where username = '{username}' and password = '{md5(password)}'"
    return sql


if __name__ == '__main__':
    sql = login_sql('admin', '123456')
    print(sql)