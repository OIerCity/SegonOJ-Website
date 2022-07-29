from distutils import extension
from flask import Flask, render_template, session, request, jsonify
from user_app import user_app
import pymongo
import markdown

app = Flask(__name__)
app.secret_key = 'h4qfibuardfautrr8tdd5i8v7ah72d'
app.register_blueprint(user_app)

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client['onlinejudge']
db_web = db['web']

@app.route('/')
def welcome():
    username = session.get('username')
    if username is not None:
        is_login = True
    else:
        is_login = False
        username = '游客'
    if user_is_banned():
        return render_template('user/banned.html', t_username=username)
    is_admin = False
    if user_is_admin():
        is_admin = True
    notice = find_webdb({'key': 'notice'})
    notice['html'] = markdown.markdown(
        notice['content'], extensions=["fenced_code", "tables", "codehilite"]
    )
    return render_template('main/main.html', t_is_login=is_login, t_useravater=username, t_notice=notice['html'], t_is_admin=is_admin)
#TODO add useravater("<img src=\"/static/user/avater/" + uid + ".png\" class=\"avater\">")

@app.route('/notice_edit')
def notice_edit():
    notice = find_webdb({'key': 'notice'})
    return render_template('main/notice_edit.html',t_notice=notice)

@app.route('/edit', methods=['POST'])
def edit():
    if request.form['type']=='notice':
        if not user_is_admin():
            return jsonify({'code':'1'})
        db_web.update_one({'type': 'notice'}, {'$set': {'content': request.form['content']}})
        return jsonify({'code':'0'})

def user_is_banned():
    username = session.get('username')
    user_list = find_user({'username': username})
    if len(user_list) == 0:
        return False
    if user_list[0]['state'] == 'banned':
        return True
    return False

def user_is_admin():
    username = session.get('username')
    user_list = find_user({'username': username})
    if len(user_list) == 0:
        return False
    if user_list[0]['state'] == 'admin':
        return True
    return False

def find_user(condition):
    c_user = db['user']
    res = c_user.find(condition)
    user_list = []
    for item in res:
        user_list.append(item)
    return user_list

def find_webdb(condition):
    res = db_web.find_one(condition)
    return res