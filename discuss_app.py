from flask import Blueprint, render_template, request, redirect, session, jsonify
from flask_pagination import Pagination
import pymongo
import user_app


discuss_app = Blueprint('discuss_app', __name__)

client = pymongo.MongoClient("mongodb://localhost:27017")
db_discuss = client['onlinejudge']
c_discuss = db_discuss['discuss']
c_user = db_discuss['user']

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
        return render_template('discuss/list.html', t_is_login=True, t_is_admin=is_admin, t_userhavebadge=userhavebadge, t_userbadge=user['userbadge'], t_usercolor=user['color'], t_username=username, t_discuss_list=discuss_list)
    else:
        condition['forum'] = request.args.get('forumname')
        if request.args.get('page') == None:
            page = 0
        else:
            page = request.args.get('page')
        alist = find_discuss(condition, page)
        for item in alist:
            owner = item['owner']
            lastcommenter = item['lastcommenter']
            item['owner'] = c_user.find_one({'uid': owner})
            item['lastcommenter'] = c_user.find_one({'uid': lastcommenter})
            discuss_list.append(item)
        return render_template('discuss/list.html', t_is_login=True, t_is_admin=is_admin, t_userhavebadge=userhavebadge, t_userbadge=user['userbadge'], t_usercolor=user['color'], t_username=username, t_discuss_list=discuss_list)


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
    alist = find_discuss(condition, page)
    discuss_list = []
    for item in alist:
        owner = item['owner']
        item['owner'] = c_user.find_one({'uid': owner})
        discuss_list.append(item)
    return render_template('discuss/discuss.html', t_is_login=True, t_is_admin=is_admin, t_userhavebadge=userhavebadge, t_userbadge=user['userbadge'], t_usercolor=user['color'], t_username=username, t_discuss_list=discuss_list)


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
