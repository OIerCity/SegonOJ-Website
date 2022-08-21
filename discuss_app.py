from flask import Blueprint, render_template, request, redirect, session, jsonify
from flask_pagination import Pagination
import pymongo
import user_app


discuss_app = Blueprint('discuss_app', __name__)

client = pymongo.MongoClient("mongodb://localhost:27017")
db_discuss = client['onlinejudge']
c_discuss = db_discuss['discuss']

per_page = 20
page_limit = 2000

@discuss_app.before_request
def before_request():
    if user_app.check_login():
        return render_template('user/login.html')
    if user_app.check_user():
        username = session.get('username')
        return render_template('user/banned.html', t_username=username)

@discuss_app.route('/discuss/list')
def discuss_list():
    username = session.get('username')
    user = db_discuss['user'].find_one({'username': username})
    userhavebadge = False
    if user['have_badge']:
        userhavebadge = True
    if user['state'] == 'admin':
        is_admin = True
    condition = {'status': 'public'}
    
    if request.args.get('forumname') == None:
        if request.args.get('page') == None:
            page = 0
        else: page = request.args.get('page')
        alist = find_discuss(condition, page)
        discuss_app.logger.info(alist)
        return render_template('discuss/list.html',t_is_login=True, t_is_admin=is_admin, t_userhavebadge=userhavebadge, t_userbadge=user['badge'], t_usercolor=user['color'], t_username=username, t_discuss_list=alist)
    else:
        return

@discuss_app.route('/discuss/<int:id>')
def discuss_view(id):
    return

def find_discuss(condition,page = 0):
    if page == 0:
        res = c_discuss.find(condition).sort([("sticky",pymongo.DESCENDING), ("date", pymongo.DESCENDING)]).limit(20)
    else:
        res = c_discuss.find(condition).sort({"date",pymongo.DESCENDING}).skip((page-1)*per_page).limit(per_page)
    return res