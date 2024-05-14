

def login_sql(username, password):
    sql = f"select * from administrator where username = '{username}' and password = '{password}'"
    return sql

def queryAdmin_sql(userid):
    sql = f"select * from administrator where id = {userid}"
    return sql

def change_password_sql(username, new_password,id):
    sql = f"update administrator set username = '{username}', password = '{new_password}' where id = {id}"
    return sql

def teacher_list_sql(condition):
    sql = f"select t.name,t.photo,t.position,t.gender,c.name,t.research_area from teacher t left join college c on t.department_id = c.College_id"
    if condition is not None:
        sql += condition
    return sql

def college_list_sql(condition):
    sql = f"select College_id, name,description,website from college"
    if condition is not None:
        sql += condition
    return sql

def query_college_byId_sql(college_id):
    sql = f"select name,description,website from college where College_id = {college_id}"
    return sql

def query_collegeId_byname_sql(name):
    sql = f"select College_id from college where name = '{name}'"
    return sql

def update_college_byId_sql(college_id, name, description, website):
    sql = f"update college set name = '{name}', description = '{description}', website = '{website}' where College_id = {college_id}"
    return sql

def delete_college_byId_sql(college_id):
    sql = f"delete from college where College_id = {college_id}"
    return sql

def insert_college_sql(id,name, description, website):
    sql = f"insert into college (College_id, name, description, website) values ({id}, '{name}', '{description}', '{website}')"
    return sql

def all_college_sql():
    sql = f"select name from college"
    return sql

def query_teacher_byId_sql(teacher_id):
    sql = f"select t.name,t.photo,t.position,t.gender,t.age,t.phone,c.name,t.research_area from teacher t left join college c on t.department_id = c.College_id where t.teacher_id = {teacher_id}"
    return sql

def update_teacher_byId_sql(teacher_id, name,photo_byte_arrary, position, gender, age, phone, college_id, research_area):
    sql = f"update teacher set name = '{name}', position = '{position}', photo = {photo_byte_arrary},gender = '{gender}', age = {age}, phone = '{phone}', department_id = {college_id}, research_area = '{research_area}' where teacher_id = {teacher_id}"
    return sql

def delete_teacher_byId_sql(teacher_id):
    sql = f"delete from teacher where teacher_id = {teacher_id}"
    return sql


if __name__ == '__main__':
    sql = login_sql('admin', '123456')
    print(sql)