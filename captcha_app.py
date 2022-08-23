from flask import Blueprint, render_template, request, redirect, session, jsonify, send_from_directory
import pymongo
import user_app
from PIL import Image, ImageDraw, ImageFont
import string
import random

class Captcha():
    '''
    captcha_size: 验证码图片尺寸
    font_size: 字体大小
    text_number: 验证码中字符个数
    line_number: 线条个数
    background_color: 验证码的背景颜色
    sources: 取样字符集。验证码中的字符就是随机从这个里面选取的
    save_format: 验证码保存格式
    '''
    def __init__(self, captcha_size=(120,48), font_size=27,text_number=4, line_number=4, background_color=(255, 255, 255), sources=None, save_format='png'):
        self.text_number = text_number
        self.line_number = line_number
        self.captcha_size = captcha_size
        self.background_color = background_color
        self.font_size = font_size
        self.format = save_format
        if sources:
            self.sources = sources
        else:
            self.sources = string.ascii_letters + string.digits

    def get_text(self):
        text = random.sample(self.sources,k=self.text_number)
        return ''.join(text)

    def get_font_color(self):
        font_color = (random.randint(0, 150), random.randint(0, 150), random.randint(0, 150))
        return font_color

    def get_line_color(self):
        line_color = (random.randint(0, 250), random.randint(0, 255), random.randint(0, 250))
        return line_color

    def draw_text(self,draw, text, font, captcha_width, captcha_height, spacing=12):
        '''
        在图片上绘制传入的字符
        :param draw: 画笔对象
        :param text: 绘制的所有字符
        :param font: 字体对象
        :param captcha_width: 验证码的宽度
        :param captcha_height: 验证码的高度
        :param spacing: 每个字符的间隙
        :return:
        '''
        # 得到这一窜字符的高度和宽度
        text_width, text_height = font.getsize(text)
        # 得到每个字体的大概宽度
        every_value_width = int(text_width / 4)

        # 这一窜字符的总长度
        text_length = len(text)
        # 每两个字符之间拥有间隙，获取总的间隙
        total_spacing = (text_length-1) * spacing

        if total_spacing + text_width >= captcha_width:
            raise ValueError("字体加中间空隙超过图片宽度!")
        self.text = text
        # 获取第一个字符绘制位置
        start_width = int( (captcha_width - text_width - total_spacing) / 2 )
        start_height = int( (captcha_height - text_height) / 2 )

        # 依次绘制每个字符
        for value in text:
            position = start_width, start_height
            # 绘制text
            draw.text(position, value, font=font, fill=self.get_font_color())
            # 改变下一个字符的开始绘制位置
            start_width = start_width + every_value_width + spacing

    def draw_line(self, draw, captcha_width, captcha_height):
        '''
        绘制线条
        :param draw: 画笔对象
        :param captcha_width: 验证码的宽度
        :param captcha_height: 验证码的高度
        :return:
        '''
        # 随机获取开始位置的坐标
        begin = (random.randint(0,captcha_width/2), random.randint(0, captcha_height))
        # 随机获取结束位置的坐标
        end = (random.randint(captcha_width/2,captcha_width), random.randint(0, captcha_height))
        draw.line([begin, end], fill=self.get_line_color())

    def draw_point(self, draw, point_chance, width, height):
        '''
        绘制小圆点
        :param draw: 画笔对象
        :param point_chance: 绘制小圆点的几率 概率为 point_chance/100
        :param width: 验证码宽度
        :param height: 验证码高度
        :return:
        '''
        # 按照概率随机绘制小圆点
        for w in range(width):
            for h in range(height):
                tmp = random.randint(0, 100)
                if tmp < point_chance:
                    draw.point((w, h), fill=self.get_line_color())

    def make_captcha(self,uid):
        # 获取验证码的宽度， 高度
        width, height = self.captcha_size
        # 生成一张图片
        captcha = Image.new('RGB',self.captcha_size,self.background_color)
        # 获取字体对象
        font = ImageFont.truetype('/home/web/static/general/font/Lato-Regular-15.ttf',self.font_size)
        # 获取画笔对象
        draw = ImageDraw.Draw(captcha)
        # 得到绘制的字符
        text = self.get_text()

        # 绘制字符
        self.draw_text(draw, text, font, width, height)

        # 绘制线条
        for i in range(self.line_number):
            self.draw_line(draw, width, height)

        # 绘制小圆点 10是概率 10/100， 10%的概率
        self.draw_point(draw,10,width,height)

        # 保存图片
        captcha.save('captcha/'+str(uid)+'.png',format=self.format)

        return self.text


captcha_app = Blueprint('captcha_app', __name__)

client = pymongo.MongoClient("mongodb://localhost:27017")
db_captcha = client['onlinejudge']
c_user = db_captcha['user']
c_captcha = db_captcha['captcha']


@captcha_app.before_request
def before_request():
    if user_app.check_login():
        return redirect('/login')
    if user_app.check_user():
        return redirect('/')


@captcha_app.route('/captcha')
def captcha():
    username = session.get('username')
    user = db_captcha['user'].find_one({'username':username})
    captcha_text = Captcha().make_captcha(user['uid'])
    if len(c_captcha.find({'uid':user['uid']})):
        c_captcha.insert_one({'uid':user['uid'],'captcha':captcha_text})
        return send_from_directory('captcha',str(user['uid']),as_attachment=False)     
