import json
from flask import Blueprint, render_template, request, redirect, session, jsonify
import pymongo
from PIL import Image

upload_app = Blueprint('upload_app', __name__)

client = pymongo.MongoClient("mongodb://localhost:27017")
db_upload = client['onlinejudge']
c_user = db_upload['user']
c_web = db_upload['web']


@upload_app.route('/upload_avater',methods=['POST'])
def upload_avater():
    username = session.get('username')
    uid = c_user.find_one({'username':username})
    user_avater = request.files.get('avater')
    if user_avater == None:
        return jsonify({'code':403,'message':'请问你上传了什么？'})
    im = Image.open(user_avater)
    im.thumbnail((50,50))
    im.save('/home/web/static/upload/avater/' + str(uid) + '.png', format='png')
    return jsonify({'code':200,'message':'头像上传成功'})