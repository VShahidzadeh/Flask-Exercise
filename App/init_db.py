# init_db.py
import sqlite3
import os

os.makedirs( 'instance', exist_ok=True)
# do not touch db if it exists
if os.path.exists('App/instance/database.db'):
    print('Database already exists. Leaving it alone.')
# configure db if does not exist
else:
    connection = sqlite3.connect('instance/database.db')
    with open('schema.sql') as f:
        connection.executescript(f.read())
    connection.execute(
        """INSERT INTO notes (topic, description, issue_details, status, attempts) VALUES (?, ?, ?, ?, ?)""",
        ('Login page crashes' ,
        'App throws an error on the login route' ,
        'Clicking submit throws a 500 error instead of logging in or showing an invalid-credentials message.' ,
        'open' ,
        'Checked the server logs; confirmed username/password fields are being read correctly.'))
    connection.commit()
    connection.close()
    print('Created instance/database.db with one sample note.')