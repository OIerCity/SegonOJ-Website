from flask import Blueprint, render_template, request, redirect, session, jsonify
import pymongo
import time
import user_app


judge_app = Blueprint('judge_app', __name__)

client = pymongo.MongoClient("mongodb://localhost:27017")
db_judge = client['onlinejudge']
c_judge_queue = db_judge['judge_queue']
c_last = db_judge['last']
c_user = db_judge['user']

def before_request():
    if user_app.check_login():
        return True
    if user_app.check_user():
        return True

@judge_app.route("/api/judge_queue")
def judge_queue():
    if request.args.get('judger') != 'H)!nn01!@sjf2-':
        return redirect('/')
    res = c_judge_queue.find({'status': '0'})
    queue = []
    cnt = 0
    for item in res:
        queue.append(item)
        cnt += 1
    return render_template('judge/queue.html', t_judge_count=cnt, t_judge_list=queue)

@judge_app.route('/api/submit_judge', methods=['POST'])
def submit_judge():
    if before_request():
        return jsonify({'status':'403','message':'用户未登录'})
    if time.time() - c_user.find_one({'username': session.get('username')})['last_judge'] < 15:
        return jsonify({'status':'403','message':'提交过于频繁，请等15秒再试'})
    code = request.form.get('code')
    size = len(code)/1024.0
    if size > 50:
        return jsonify({'status':'403','message':'代码长度不能超过50KB'})
    res = c_last.find()
    last_list = []
    for item in res:
        last_list.append(item)
    last_record = last_list[0]['record']
    rid = last_record+1
    c_last.update_one({}, {"$set": {'record': last_record + 1}})
    local_time = time.time()
    c_user.update_one({'username': session.get('username')}, {"$set": {'last_judge': local_time}})
    c_judge_queue.insert_one({'rid': rid, 'timestamp': time.time(), 'formated_time': time.strftime('%Y.%m.%d %H:%M'), 'code':code, 'size': size, 'status': '0', 'result': None, 'score': 0})
    return jsonify({'status':'200','message':'提交成功'})