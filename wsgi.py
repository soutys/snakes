import redis
import json
from flask import Flask, render_template, request, redirect, url_for


app = Flask(__name__)
r = redis.StrictRedis(host='localhost', port=6379, db=0)

SCRIPT = """\
import sys, random

WIDTH, HEIGHT = 80, 60

# Change here!
# ------------
# Board is a list of strings (board rows), where:
#  - o = apple
#  - # = snake
#  - H = head of our snake
#  - . = empty field
#
# Move should return 'left', 'right', 'up' or 'down'
def move(board):
    return random.choice(['left', 'right', 'up', 'down'])

# Don't touch (unless you know what you're doing :-))
while True:
    board = [sys.stdin.readline() for _ in range(HEIGHT)]
    sys.stdout.write(move(board))
    sys.stdout.write('\\n')
"""

@app.route('/')
@app.route('/snake/<key>')
def board(key=None):
    snake_name = 'Annonymous'
    snake_code = SCRIPT
    snake_color = '#fff'

    if key is not None:
        snake_name = r.get('snake:%s:name' % key) or ''
        snake_code = r.get('snake:%s:code' % key) or SCRIPT
        snake_color = r.get('snake:%s:color' % key) or '#fff'
    return render_template('board.html',
                           board=r.get('board'),
                           key=key or '',
                           name=snake_name,
                           code=snake_code,
                           color=snake_color)


@app.route('/board')
def check_board():
    return r.get('snakes') or json.dumps({'snakes': []})


def snake_name(key):
    name = r.get('snake:%s:name' % key)
    return name if name is not None else 'Annonymous'


@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html', members=[
        {'name': snake_name(s[0]), 'score': s[1]}
        for s in r.zrange('leaderboard', 1, -1, withscores=True)])


@app.route('/reload_slave', methods=['POST'])
def reload_code():
    if (';' in request.form['slave_name']
        or len(request.form['slave_id']) == 0
        or len(request.form['slave_name']) == 0
        or len(request.form['slave_code']) == 0):
        return redirect(url_for('board'))
    command = 'reload_slave;%s;%s;%s' % (request.form['slave_id'],
                                         request.form['slave_name'],
                                         request.form['slave_code'])
    r.rpush('commands', command)
    r.set('snake:%s:name' % request.form['slave_id'], request.form['slave_name'])
    r.set('snake:%s:code' % request.form['slave_id'], request.form['slave_code'])

    return redirect(url_for('board', key=request.form['slave_id']))


if __name__ == '__main__':
    app.run()
