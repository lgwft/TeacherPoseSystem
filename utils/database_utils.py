import hashlib

from pymysql import connect

global con
con = None
def connectDB():
    try:
        con = connect(host='localhost',
                      port=3306,
                      user='root',
                      password='123456',
                      database='TeacherPoseSystem',)
    except Exception as e:
        print(e)
    return con

def sqlExecute(sql):
    global con
    if con is None:
        con = connectDB()
    cur = con.cursor()
    cur.execute(sql)
    result = cur.fetchall()
    return result

def md5(test):
    test = bytes(test, encoding='utf-8')
    return hashlib.md5(test).hexdigest()

if __name__ == '__main__':
    test = md5("123456")
    print(test)