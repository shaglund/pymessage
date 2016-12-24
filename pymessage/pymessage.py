import os
import sqlite3
import sys
from flask import Flask, g, request, jsonify

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'messages.db')
))
app.config.from_envvar('MESSAGES_SETTINGS', silent=True)


def connect_db():
    dbh = sqlite3.connect(app.config['DATABASE'])
    dbh.row_factory = sqlite3.Row
    return dbh


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_cmd():
    init_db()
    print('Database initialized')


@app.route('/<string:user>', methods=['GET', 'POST'])
def send_message(user):
    db = get_db()
    cur = db.execute('SELECT id, lastread FROM user WHERE username=?', [user])
    userId = cur.fetchone()
    if userId is None:
        return "User not found", 404

    if request.method == 'POST':
        message = request.get_json(silent=True)
        db.execute('INSERT INTO messages(userId, message) VALUES (?,?)', [userId[0], message['message']])
        db.commit()
    else:
        ''' Fetch only users unread messages unless from/to query parameters are set '''
        from_id = request.args.get('from', userId[1]+1, type=int)
        to_id = request.args.get('to', sys.maxsize, type=int)
        sql = 'SELECT message, id FROM messages WHERE userId=? AND id BETWEEN ? and ? ORDER BY id'
        cur = db.execute(sql, [userId[0], from_id, to_id])
        ''' Format message(s) as json document '''
        all_messages = {}
        lastread = userId[1]
        for msg in cur.fetchall():
            all_messages[msg[1]]=msg[0]
            lastread = max(lastread, msg[1])
        ''' Update last read item for user '''
        db.execute('UPDATE user SET lastread=? WHERE id=?', [lastread, userId[0]])
        db.commit()
        return jsonify(all_messages)

    return "OK"


@app.route('/adduser/<string:username>', methods=['POST'])
def create_user(username):
    db = get_db()
    cur = db.execute('SELECT * FROM user WHERE username=?', [username])
    cur_user = cur.fetchone()
    if cur_user is None:
        cur = db.cursor()
        cur.execute('INSERT INTO user (username, lastread) VALUES (?, ?)', [username, 0])
        db.commit()
        cur.close()
    else:
        return "User already exists", 409
    return "OK"


@app.route('/<string:user>/<int:id>', methods=['DELETE'])
def delete_message(user, id):
    db = get_db()
    cur = db.execute('SELECT id FROM user WHERE username=?', [user])
    userId = cur.fetchone()
    if userId is None:
        return "User not found", 404
    cur = db.execute('SELECT id FROM messages WHERE id=? AND userId=?', [id, userId[0]])
    messageId = cur.fetchone()
    if messageId is None:
        return "Message not found", 404
    db.execute('DELETE FROM messages WHERE id=? AND userId=?', [id, userId[0]])
    db.commit()
    return "OK"