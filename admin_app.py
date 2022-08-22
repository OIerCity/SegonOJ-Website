from flask import Blueprint, render_template, request, redirect, session, jsonify
import pymongo

admin_app = Blueprint('admin_app', __name__)

client = pymongo.MongoClient("mongodb://localhost:27017")
db_admin = client['onlinejudge']
c_user = db_admin['user']
c_web = db_admin['web']


@admin_app.route('/countrank')
def count_rank():
    res = c_user.find({}).sort("juan", pymongo.DESCENDING).limit(5)
    alist = []
    for item in res:
        alist.append(item)
    c_web.update_one({'type': 'ranktopers'},{'$set':{'top1': alist[0]['uid'],'top2': alist[1]['uid'],'top3': alist[2]['uid'],'top4': alist[3]['uid'],'top5': alist[4]['uid']}})
    return redirect('/')