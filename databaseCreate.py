import sqlite3

#Create new database, enter the database name in name, and end it with a '.db'
name = ''
conn = sqlite3.connect(name)
c = conn.cursor()

#Create a table in the database
c.execute("""create stocks(name string, number integer, price integer)""")

conn.commit()
conn.close()
