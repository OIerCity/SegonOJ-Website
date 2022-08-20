from flask import Blueprint, render_template, request, redirect, session, jsonify
import pymongo


discuss_app = Blueprint('discuss_app', __name__)

client = pymongo.MongoClient("mongodb://localhost:27017")
db_discuss = client['onlinejudge']
c_discuss = db_discuss['discuss']

@discuss_app.route('/discuss/list')
def discuss_list():
    if request.args['forumname'] == None:
        c_discuss
        return
    else:
        return

@discuss_app.route('/discuss/<int:id>')
def discuss_view(id):
    return