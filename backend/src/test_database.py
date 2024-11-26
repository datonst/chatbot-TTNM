import sqlite3

db_name = "./dishes.db"
# try:
connection = sqlite3.connect(db_name)
cursor = connection.cursor()

if cursor:
    print('True')
else:
    print('False')
# print('sql_query --->', sql_query)

cursor.execute("SELECT * FROM dishes")
result = cursor.fetchall()
#
print('all database : ', result)