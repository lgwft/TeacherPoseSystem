import hashlib

from pymysql import connect

global con
con = None
def connectDB():
    global con
    try:
        con = connect(host='localhost',
                      port=3306,
                      user='root',
                      password='123456',
                      database='TeacherPoseSystem',
                      autocommit=True)
    except Exception as e:
        print(e)
    return con

def sqlExecute(sql, values=None):
    global con
    if con is None:
        con = connectDB()
    try:
        cur = con.cursor()
        if values:
            cur.execute(sql, values)
        else:
            cur.execute(sql)
        result = cur.fetchall()
    except Exception as e:
        print(e)
    # finally:
        # if con is not None:
            # con.close()
    return result,cur.rowcount

def md5(test):
    test = bytes(test, encoding='utf-8')
    return hashlib.md5(test).hexdigest()

if __name__ == '__main__':
    test = md5("123456")
    connectDB()
    print(con)