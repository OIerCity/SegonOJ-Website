from datetime import date, datetime
from email import message
import json
from sqlite3 import Timestamp
from flask import Blueprint, render_template, request, redirect, session, jsonify
import pymongo
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from random import randint

msg = '''
<p>您好，您的SegonOJ注册链接是：</p>
<p>http://segonoj.site/register_verify?email='''
esender = 'seojhelper@hotmail.com'
epwd = 'M=GC/J=|)>uY}d_'

user_app = Blueprint('user_app', __name__)

client = pymongo.MongoClient("mongodb://localhost:27017")
db_user = client['onlinejudge']
c_user = db_user['user']
c_online = db_user['online']
c_last = db_user['last']
c_verify = db_user['email_verify']


@user_app.route('/register')
def register():
    return render_template('user/register.html', t_found=False)


@user_app.route('/change_password')
def change_password():
    return render_template('user/change_password.html')

@user_app.route('/api/register_send', methods=['POST'])
def register_send():
    email = request.form['email']
    if len(find_user({'email': email})) == 1:
        return jsonify({'status': 403,'message':'此邮箱已被占用'})
    v_email = c_verify.find_one({'email': email})
    if v_email is not None:
        if v_email['used'] == 'yes':
            return jsonify({'status': 403,'message':'此邮箱已被占用'})
        if datetime.timestamp(datetime.now())-v_email['timestamp'] <= 60:
            return jsonify({'status': 403,'message':'验证码发送冷却中'})
    status, code = send_mail(email)
    if status:
        if v_email is not None:
            c_verify.update_one({'email': email}, {'$set': {'verify_code': code, 'passed': 'no', 'timestamp': datetime.timestamp(datetime.now())}})
            return jsonify({'status': 200,'message':'发送成功'})
        else:
            c_verify.insert_one({'email': email, 'verify_code': code, 'passed': 'no', 'used': 'no', 'timestamp': datetime.timestamp(datetime.now())})
            return jsonify({'status': 200,'message':'发送成功'})
    else:
        return jsonify({'status': 500,'message':'发生未知错误'})

@user_app.route('/register_verify')
def register_verify():
    email = request.args['email']
    verify_code = request.args['code']
    e_verify = c_verify.find_one({'email': str(email), 'verify_code': str(verify_code)})
    if e_verify == None:
        return render_template('user/register.html',t_found=False)
    elif e_verify['used'] == 'yes':
        return render_template('user/register.html',t_found=False,t_message='这邮箱被用过了')
    else:
        c_verify.update_one({'email': email, 'verify_code': verify_code}, {'$set': {'passed': 'yes'}})
        return render_template('user/register.html',t_found=True, t_email=email, t_verify_code=verify_code)

@user_app.route('/api/register_check', methods=['POST'])
def register_check():
    username = request.form['username']
    pwd = request.form['password']
    email = request.form['email']
    verify_code = request.form['verify_code']
    rcode = request.form['rcode']
    if rcode != 'Y9sj)j-0Jo9%_1M.*j.>':
        return jsonify({'status':403,'message':'授权码错误，请联系QQ3060272052（liucang）'})
    whitelist_str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"
    e_verify = c_verify.find_one({'email': email, 'passed': 'yes', 'used': 'no', 'verify_code': verify_code})
    if e_verify is None:
        return jsonify({'status': 403,'message':'邮箱验证错误'})
    if len(username) == 0 or len(pwd) == 0:
        return jsonify({'status': 403,'message':'用户名或密码不能为空'})
    pwd = encrypt(pwd)
    for i in username:
        if (i in whitelist_str) is not True:
            return jsonify({'status': 403,'message':'用户名不能包含特殊字符'})
    user_list = find_user({'username': username})
    if len(user_list) == 0:
        res = c_last.find()
        last_list = []
        for item in res:
            last_list.append(item)
        last_uid = last_list[0]['uid']
        c_last.update_one({}, {"$set": {'uid': last_uid + 1}})
        user = {'username': username, 'password': pwd, 'state': 'normal', 'uid': last_uid + 1, 'email': email, 'color': 'blue', 'have_badge': 0, 'userbadge': 'default', 'juan': 0}
        insert_user(user)
        c_verify.update_one({'email': email, 'passed': 'yes', 'used': 'no', 'verify_code': verify_code},{"$set": {'used': 'yes'}})
        return jsonify({'status': 200,'message':'注册成功！'})
    else:
        return jsonify({'status': 403,'message':'用户名已被使用'})
    


@user_app.route('/api/change_submit', methods=['POST'])
def change_submit():
    username = session["username"]
    password = request.form['old_password']
    pwd = encrypt(password)
    user_list = find_user({'username': username, 'password': pwd})
    new_pwd = request.form['new_password']
    new_pwd2 = request.form['new_password2']
    if new_pwd != new_pwd2:
        return render_template('user/change_password.html', t_msg='新密码错误')
    elif len(user_list) == 1:
        c_user.update_one({'username': username}, {"$set": {'password': encrypt(new_pwd)}})
        session.pop('username')
        return render_template('user/login.html', t_error='密码修改成功，请重新登录')
    else:
        return render_template('user/change_password.html', t_msg='原密码错误')


'''
    --------与登录有关的路由--------

    /login           访问登录页面
    /login_check     处理登录表单，实现登录功能

'''



@user_app.route('/login')
def login():
    return render_template('user/login.html')


@user_app.route('/api/login_check', methods=['POST'])
def login_check():
    username = request.form['username']
    pwd = request.form['password']
    if pwd == None or username == None:
        return jsonify({'status':403,"message":"用户名或密码不能为空"})
    pwd = encrypt(pwd)
    user_list = find_user({'username': username, 'password': pwd})
    if len(user_list) == 1:
        # if user_list[0]['state'] == "2":
        #     return render_template('user/login.html', t_error='用户信息待审核', t_color='2')
        if user_list[0]['state'] != "banned":
            session['username'] = username
            if request.headers.getlist("X-Forwarded-For"):
                ip = request.headers.getlist("X-Forwarded-For")[0]
            else:
                ip = request.remote_addr
            c_user.update_one({'username': username}, {"$set": {'last_login_ip': ip}})
            return jsonify({'status':200})
        else:
            return redirect({'status':403,'message':'此用户已被封禁'})
    else:
        return jsonify({'status':403,'message':'用户名或密码错误'})

@user_app.route('/banned')
def banned():
    return render_template("user/banned.html")

@user_app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')


'''
    --------与登录、注册有关的自定义函数--------

    insert_user()     将注册用户数据存入数据库
    find_user()       根据条件查找注册用户信息
    encrypt()         对密码进行加密
    send_mail()       对邮箱发送邮件
'''


def insert_user(user):
    c_user.insert_one(user)


def find_user(condition):
    res = c_user.find(condition)
    user_list = []
    for item in res:
        user_list.append(item)
    return user_list


def encrypt(password):
    pwd = hashlib.md5(password.encode(encoding='UTF-8')).hexdigest()
    return pwd


def check_login():
    username = session.get('username')
    if username is None:
        return True


def check_user():
    username = session.get('username')
    user_list = find_user({'username': username})
    if len(user_list) == 0:
        return False
    if user_list[0]['state'] == 'banned':
        return True
    ts = datetime.timestamp(datetime.now())
    if c_online.count_documents({'username': username}) != 0:
        c_online.update_one({'username': username}, {"$set": {'time': ts}})
    else:
        c_online.insert_one({'username': username, 'time': ts})
    return False

def send_mail(ereciever):
    smtpObj = smtplib.SMTP('smtp.office365.com', 587)
    smtpObj.ehlo()
    smtpObj.starttls()
    smtpObj.login(esender, epwd)
    code = ''
    base_str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890'

    try:
        for i in range(20):
            code += base_str[randint(0, 61)]
        
        emsg = MIMEText(msg + ereciever + '''&code=''' + code + '''</p>''', 'html')
        emsg['From'] = Header("SegonOJ")
        emsg['To'] = Header(ereciever)
        emsg['Subject'] = Header('SegonOJ - 注册邮箱验证')
        smtpObj.sendmail(esender, ereciever, emsg.as_string())
        smtpObj.quit()
        return True, str(code)
    except:
        smtpObj.quit()
        return False, str(code)

'''
    --------用户个人页面--------
'''

@user_app.route('/user/<int:uid>')
def user_page():
    return render_template('user/selfpage.html')
