from curses.ascii import isdigit, islower, isupper
import json
from threading import local
from flask import Blueprint, render_template, request, redirect, session, jsonify
from flask_pagination import Pagination
import pymongo
import user_app
import markdown
import time
from difflib import SequenceMatcher


discuss_app = Blueprint('discuss_app', __name__)

client = pymongo.MongoClient("mongodb://localhost:27017")
db_discuss = client['onlinejudge']
c_discuss = db_discuss['discuss']
c_user = db_discuss['user']
c_captcha = db_discuss['captcha']
c_last = db_discuss['last']

per_page = 20
page_limit = 2000


@discuss_app.before_request
def before_request():
    if user_app.check_login():
        return redirect('/login')
    if user_app.check_user():
        return redirect('/')


@discuss_app.route('/discuss/list')
def discuss_list():
    username = session.get('username')
    user = db_discuss['user'].find_one({'username': username})
    userhavebadge = False
    if user['have_badge']:
        userhavebadge = True
    if user['state'] == 'admin':
        is_admin = True
    condition = {'status': 'public', 'parent': 0}

    if request.args.get('forumname') == None:
        if request.args.get('page') == None:
            page = 0
        else:
            page = request.args.get('page')
        alist = find_discuss(condition, page)
        discuss_list = []
        for item in alist:
            owner = item['owner']
            lastcommenter = item['lastcommenter']
            item['owner'] = c_user.find_one({'uid': owner})
            item['lastcommenter'] = c_user.find_one({'uid': lastcommenter})
            discuss_list.append(item)
        return render_template('discuss/list.html', t_is_login=True, t_is_admin=is_admin, t_userhavebadge=userhavebadge, t_userbadge=user['userbadge'], t_usercolor=user['color'], t_username=username, t_discuss_list=discuss_list,t_forum='all',t_canpost=0)
    else:
        condition['forum'] = request.args.get('forumname')
        if request.args.get('page') == None:
            page = 0
        else:
            page = request.args.get('page')
        alist = find_discuss(condition, page)
        discuss_list = []
        for item in alist:
            owner = item['owner']
            lastcommenter = item['lastcommenter']
            item['owner'] = c_user.find_one({'uid': owner})
            item['lastcommenter'] = c_user.find_one({'uid': lastcommenter})
            discuss_list.append(item)
        return render_template('discuss/list.html', t_is_login=True, t_is_admin=is_admin, t_userhavebadge=userhavebadge, t_userbadge=user['userbadge'], t_usercolor=user['color'], t_username=username, t_discuss_list=discuss_list,t_forum=request.args.get('forumname'),t_canpost=1)


@discuss_app.route('/discuss/<int:id>')
def discuss_view(id):
    username = session.get('username')
    user = db_discuss['user'].find_one({'username': username})
    userhavebadge = False
    if user['have_badge']:
        userhavebadge = True
    if user['state'] == 'admin':
        is_admin = True
    condition = {'status': 'public', 'parent': id}
    if request.args.get('page') == None:
        page = 0
    else:
        page = request.args.get('page')
    discuss = c_discuss.find_one({'id': id})
    owner = discuss['owner']
    lastcommenter = discuss['lastcommenter']
    discuss['owner'] = c_user.find_one({'uid': owner})
    discuss['lastcommenter'] = c_user.find_one({'uid': lastcommenter})
    discuss['content'] = markdown.markdown(
        discuss['content'],extensions=["fenced_code", "tables", "codehilite"]
    )
    alist = find_discuss(condition, page)
    comment_list = []
    for item in alist:
        owner = item['owner']
        item['owner'] = c_user.find_one({'uid': owner})
        item['content'] = markdown.markdown(
            item['content'],extensions=["fenced_code", "tables", "codehilite"]
        )
        comment_list.append(item)
    return render_template('discuss/discuss.html', t_is_login=True, t_is_admin=is_admin, t_userhavebadge=userhavebadge, t_userbadge=user['userbadge'], t_usercolor=user['color'], t_username=username, t_comment_list=comment_list, t_discuss=discuss,t_parent=id)

def check_captcha(input_captcha, real_captcha):
    if len(input_captcha) != len(real_captcha):
        return False
    else:
        for i in range(len(real_captcha)):
            if real_captcha[i].islower() or real_captcha[i].isupper():
                if input_captcha[i].lower() == real_captcha[i].lower():
                    continue
                else:
                    return False
            else:
                if input_captcha[i] == real_captcha[i]:
                    continue
                else:
                    return False
    return True

@discuss_app.route('/api/post_discuss', methods=['POST'])
def discuss_post():
    content = request.form['content']
    title = request.form['title']
    captcha = request.form['captcha']
    forum = request.form['forum']
    username = session.get('username')
    user = c_user.find_one({'username':username})
    uid=user['uid']
    if (check_captcha(captcha, c_captcha.find_one({'uid':uid})['captcha'])) is not True:
        return jsonify({'status':403,'message':'验证码错误'})
    if content == '':
        return jsonify({'status':403,'message':'内容不能为空'})
    if title == '':
        return jsonify({'status':403,'message':'标题不能为空'})
    if len(title) > 18:
        return jsonify({'status':403,'message':'标题不能超过18个字'})
    if forum is 'announcement' and user['state'] is not 'admin':
        return jsonify({'status':403,'message':'您无权限在此处发帖'})
    if forum != 'water' and forum != 'site' and forum != 'problem' and forum != 'academics' and forum != 'service' and forum != 'announcement':
        return jsonify({'status':403,'message':'板块未找到'})
    forumname = ''
    if forum is 'announcement':
        forumname = '公告板'
    if forum is 'water':
        forumname = '划水版'
    if forum is 'site':
        forumname = '站务版'
    if forum is 'problem':
        forumname = '题目总版'
    if forum is 'academics':
        forumname = '学术版'
    if forum is 'service':
        forumname = '反馈版'
    discuss = {}
    local_time = time.time()
    format_time = time.strftime('%Y.%m.%d %H:%M')
    last = c_last.find_one({})
    last_id = last['discussid']
    discuss['lastcommenter'] = 0
    discuss['owner'] = uid
    discuss['time'] = format_time
    discuss['title'] = title
    discuss['lastcommenttime'] = '1970.1.1 00:00'
    discuss['content'] = content
    discuss['forum'] = forum
    discuss['status'] = 'public'
    discuss['sticky'] = 0
    discuss['timestamp'] = local_time
    discuss['parent'] = 0
    discuss['id'] = last_id + 1
    discuss['comments'] = 0
    discuss['forumname'] = forumname
    c_discuss.insert_one(discuss)
    c_last.update_one({},{'$set':{'discussid':last_id + 1}})
    return jsonify({'status':'200','message':'/discuss/' + str(last_id + 1)})

@discuss_app.route('/api/post_comment', methods=['POST'])
def comment_post():
    content = request.form['content']
    captcha = request.form['captcha']
    parent = request.form['parent']
    parent = int(parent)
    username = session.get('username')
    user = c_user.find_one({'username':username})
    uid=user['uid']
    if ( captcha == c_captcha.find_one({'uid':uid})['captcha'] ) is not True:
        return jsonify({'status':403,'message':'验证码错误'})
    if c_discuss.find_one({'id':parent}) == None:
        return jsonify({'status':403,'message':'帖子未找到'})
    if content == '':
        return jsonify({'status':403,'message':'内容不能为空'})
    discuss = {}
    local_time = time.time()
    format_time = time.strftime('%Y.%m.%d %H:%M')
    discuss['owner'] = uid
    discuss['time'] = format_time
    discuss['content'] = content
    discuss['status'] = 'public'
    discuss['timestamp'] = local_time
    discuss['parent'] = parent
    c_discuss.insert_one(discuss)
    c_discuss.update_one({'id':parent},{'$set':{'comments':c_discuss.find_one({'id':parent})['comments']+1,'lastcommenttime':format_time,'lastcommenter':uid}})
    return jsonify({'status':'200','message':'/discuss/' + str(parent)})


def find_discuss(condition, page=0):
    if page == 0:
        res = c_discuss.find(condition).sort(
            [("sticky", pymongo.DESCENDING), ("timestamp", pymongo.DESCENDING)]).limit(20)
    else:
        res = c_discuss.find(condition).sort("timestamp", pymongo.DESCENDING).skip(
            (page-1)*per_page).limit(per_page)
    alist = []
    for item in res:
        alist.append(item)
    return alist

def find_comment(condition, page=0):
    if page == 0:
        res = c_discuss.find(condition).sort("timestamp", pymongo.ASCENDING).limit(20)
    else:
        res = c_discuss.find(condition).sort("timestamp", pymongo.ASCENDING).skip(
            (page-1)*per_page).limit(per_page)
    alist = []
    for item in res:
        alist.append(item)
    return alist
