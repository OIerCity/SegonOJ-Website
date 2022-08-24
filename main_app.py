from flask import Flask, render_template, session, request, jsonify, send_from_directory
from user_app import user_app
from discuss_app import discuss_app, find_discuss
from admin_app import admin_app
from captcha_app import captcha_app
from datetime import date, datetime
import pymongo
import markdown
import os

app = Flask(__name__)
app.secret_key = 'h4qfibuardfautrr8tdd5i8v7ah72d'
app.register_blueprint(user_app)
app.register_blueprint(discuss_app)
app.register_blueprint(admin_app)
app.register_blueprint(captcha_app)

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client['onlinejudge']
db_web = db['web']
c_user = db['user']

@app.route('/favicon.ico')#设置icon
def favicon():
    return send_from_directory(os.path.join('/home/web', 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def welcome():
    username = session.get('username')
    user = db['user'].find_one({'username': username})
    anncouncements = find_discuss({'forum': 'anncouncement'})
    rankTopers = db_web.find_one({'type': 'ranktopers'})
    rankTopersUserInfo = {}
    rankTopersUserInfo['top1'] = c_user.find_one({'uid': rankTopers['top1']})
    rankTopersUserInfo['top2'] = c_user.find_one({'uid': rankTopers['top2']})
    rankTopersUserInfo['top3'] = c_user.find_one({'uid': rankTopers['top3']})
    rankTopersUserInfo['top4'] = c_user.find_one({'uid': rankTopers['top4']})
    rankTopersUserInfo['top5'] = c_user.find_one({'uid': rankTopers['top5']})
    if username is not None:
        is_login = True
    else:
        is_login = False
        username = '游客'
        return render_template('main/main.html', t_is_login=False, t_anncouncements=anncouncements, t_is_admin=False, t_userhavebadge=False, t_username=username, t_ranktopers=rankTopersUserInfo)
    if user['state']=='banned':
        return render_template('user/banned.html', t_username=username)
    is_admin = False
    if user['state']=='admin':
        is_admin = True
    
    userhavebadge = False
    if user['have_badge']:
        userhavebadge = True
    
    return render_template('main/main.html', t_is_login=is_login, t_anncouncements=anncouncements, t_is_admin=is_admin, t_userhavebadge=userhavebadge, t_userbadge=user['userbadge'], t_usercolor=user['color'], t_username=username, t_ranktopers=rankTopersUserInfo)
#TODO add useravater("<img src=\"/static/user/avater/" + uid + ".png\" class=\"avater\">")

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