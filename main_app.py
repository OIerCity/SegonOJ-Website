import imp
from flask import Flask, render_template, session, request, jsonify, send_from_directory
from user_app import user_app
from discuss_app import discuss_app, find_discuss
from admin_app import admin_app
from captcha_app import captcha_app
from upload_app import upload_app
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
app.register_blueprint(upload_app)

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client['onlinejudge']
db_web = db['web']
c_user = db['user']
c_discuss = db['discuss']
c_last = db['last']

@app.route('/favicon.ico')#设置icon
def favicon():
    return send_from_directory(os.path.join('/home/web', 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def welcome():
    username = session.get('username')
    user = db['user'].find_one({'username': username})
    announcements = find_discuss({'forum': 'announcement'})
    rankTopers = db_web.find_one({'type': 'ranktopers'})
    rankTopersUserInfo = {}
    rankTopersUserInfo['top1'] = c_user.find_one({'uid': rankTopers['top1']})
    rankTopersUserInfo['top2'] = c_user.find_one({'uid': rankTopers['top2']})
    rankTopersUserInfo['top3'] = c_user.find_one({'uid': rankTopers['top3']})
    rankTopersUserInfo['top4'] = c_user.find_one({'uid': rankTopers['top4']})
    rankTopersUserInfo['top5'] = c_user.find_one({'uid': rankTopers['top5']})
    lastDiscussInfo = {}
    discussA = c_discuss.find_one({'id':c_last.find_one({})['discussid']})
    discussA['owner'] = c_user.find_one({'uid':discussA['owner']})
    discussA['lastcommenter'] = c_user.find_one({'uid':discussA['lastcommenter']})
    if len(discussA['content']) > 12:
        strtmp = discussA['content']
        strtmp = strtmp[:12]+'...'
        discussA['content'] = strtmp
    if len(discussA['title']) > 6:
        strtmp = discussA['title']
        strtmp = strtmp[:6]+'...'
        discussA['title'] = strtmp
    discussB = c_discuss.find_one({'id':c_last.find_one({})['discussid']-1})
    discussB['owner'] = c_user.find_one({'uid':discussB['owner']})
    discussB['lastcommenter'] = c_user.find_one({'uid':discussB['lastcommenter']})
    if len(discussB['content']) > 12:
        strtmp = discussB['content']
        strtmp = strtmp[:12]+'...'
        discussB['content'] = strtmp
    if len(discussB['title']) > 6:
        strtmp = discussB['title']
        strtmp = strtmp[:6]+'...'
        discussB['title'] = strtmp
    discussC = c_discuss.find_one({'id':c_last.find_one({})['discussid']-2})
    discussC['owner'] = c_user.find_one({'uid':discussC['owner']})
    discussC['lastcommenter'] = c_user.find_one({'uid':discussC['lastcommenter']})
    if len(discussC['content']) > 12:
        strtmp = discussC['content']
        strtmp = strtmp[:12]+'...'
        discussC['content'] = strtmp
    if len(discussC['title']) > 6:
        strtmp = discussC['title']
        strtmp = strtmp[:6]+'...'
        discussC['title'] = strtmp
    discussD = c_discuss.find_one({'id':c_last.find_one({})['discussid']-3})
    discussD['owner'] = c_user.find_one({'uid':discussD['owner']})
    discussD['lastcommenter'] = c_user.find_one({'uid':discussD['lastcommenter']})
    if len(discussD['content']) > 12:
        strtmp = discussD['content']
        strtmp = strtmp[:12]+'...'
        discussD['content'] = strtmp
    if len(discussD['title']) > 6:
        strtmp = discussD['title']
        strtmp = strtmp[:6]+'...'
        discussD['title'] = strtmp
    discussE = c_discuss.find_one({'id':c_last.find_one({})['discussid']-4})
    discussE['owner'] = c_user.find_one({'uid':discussE['owner']})
    discussE['lastcommenter'] = c_user.find_one({'uid':discussE['lastcommenter']})
    if len(discussE['content']) > 12:
        strtmp = discussE['content']
        strtmp = strtmp[:12]+'...'
        discussE['content'] = strtmp
    if len(discussE['title']) > 6:
        strtmp = discussE['title']
        strtmp = strtmp[:6]+'...'
        discussE['title'] = strtmp
    discussF = c_discuss.find_one({'id':c_last.find_one({})['discussid']-5})
    discussF['owner'] = c_user.find_one({'uid':discussF['owner']})
    discussF['lastcommenter'] = c_user.find_one({'uid':discussF['lastcommenter']})
    if len(discussF['content']) > 12:
        strtmp = discussF['content']
        strtmp = strtmp[:12]+'...'
        discussF['content'] = strtmp
    if len(discussF['title']) > 6:
        strtmp = discussF['title']
        strtmp = strtmp[:6]+'...'
        discussF['title'] = strtmp
    lastDiscussInfo['A'] = discussA
    lastDiscussInfo['B'] = discussB
    lastDiscussInfo['C'] = discussC
    lastDiscussInfo['D'] = discussD
    lastDiscussInfo['E'] = discussE
    lastDiscussInfo['F'] = discussF
    if username is not None:
        is_login = True
    else:
        is_login = False
        username = '游客'
        return render_template('main/main.html', t_is_login=False, t_announcements=announcements, t_is_admin=False, t_userhavebadge=False, t_username=username, t_ranktopers=rankTopersUserInfo, t_lastdiscuss=lastDiscussInfo)
    if user['state']=='banned':
        return render_template('user/banned.html', t_username=username)
    is_admin = False
    if user['state']=='admin':
        is_admin = True
    
    userhavebadge = False
    if user['have_badge']:
        userhavebadge = True
    
    return render_template('main/main.html', t_is_login=is_login, t_announcements=announcements, t_is_admin=is_admin, t_userhavebadge=userhavebadge, t_userbadge=user['userbadge'], t_usercolor=user['color'], t_username=username, t_ranktopers=rankTopersUserInfo, t_lastdiscuss=lastDiscussInfo)
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