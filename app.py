import re, bcrypt, jwt

from my_settings import SECRET
from decorator   import login_required
from flask       import Flask, render_template, jsonify, request
from pymongo     import MongoClient

app    = Flask(__name__)
client = MongoClient('localhost', 27017)
db     = client.dbnbc

# API 역할을 하는 부분

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/calender')
def calender():
    return render_template('calender.html')


# 체크인
@app.route('/check-in', methods=['POST'])
@login_required
def check_in():
    start_time = request.form['start_time']
    status     = request.form['status']
    year       = request.form['year']
    month      = request.form['month']
    day        = request.form['day']
    week       = request.form['week']

    user_nickname = request.user['nick_name']
    db.user.update_one({'nick_name': user_nickname}, {'$set': {
        'status': status,
        f'{year}.{month}.{day}.start_time': start_time,
        f'{year}.{month}.{day}.week'      : week,
    }})

    return jsonify({"msg": f'{start_time}에 {status} 하셨습니다'})


# 체크아웃
@app.route('/check-out', methods=['POST'])
@login_required
def check_out():
    year       = request.form['year']
    month      = request.form['month']
    day        = request.form['day']
    week       = request.form['week']
    stop_time  = request.form['stop_time']
    status     = request.form['status']
    study_time = request.form['study_time'][:8]

    user_nickname = request.user['nick_name']
    db.user.update_one({'nick_name': user_nickname}, {'$set': {
        'status': status,
        f'{year}.{month}.{day}.stop_time': stop_time,
        f'{year}.{month}.{day}.study_time': study_time,
        f'{year}.{month}.{day}.week': week,
    }})
    return jsonify({"msg": f'오늘 총 {study_time} 동안 업무를 진행하셨습니다.'})


@app.route('/wise', methods=['GET'])
def read_wise_sy():
    wise = list(db.wise_sy.find({}, {'_id': False}))
    return jsonify(wise)


# 회원가입
@app.route('/sign-up', methods=['POST'])
def sign_up():
    nick_name           = request.form['nick_name']
    password            = request.form['password']
    password_validation = re.compile('^[a-zA-Z0-9]{6,}$')

    # 닉네임 중복확인
    if db.user.find_one({'nick_name': nick_name}) is not None:
        return jsonify({'msg': '중복된 닉네임'})

    # 비밀번호 중복확인
    if not password_validation.match(password):
        return jsonify({"msg": "영어 또는 숫자로 6글자 이상으로 작성해주세요"})

    # 비밀번호 암호화
    byte_password   = password.encode("utf-8")
    encode_password = bcrypt.hashpw(byte_password, bcrypt.gensalt())
    decode_password = encode_password.decode("utf-8")
    doc = {
        'nick_name': nick_name,
        'password': decode_password
    }
    db.user.insert_one(doc)
    return jsonify({'msg': '저장완료'})


# 로그인
@app.route('/login', methods=['POST'])
def login():
    nick_name = request.form['nick_name']
    password  = request.form['password']

    # 닉네임 확인
    user = db.user.find_one({'nick_name': nick_name})
    if user is None:
        return jsonify({"msg": "INVALID_NICKNAME"})

    # 비밀번호 확인
    if not bcrypt.checkpw(password.encode("utf-8"), user['password'].encode("utf-8")):
        return jsonify({"msg": "INVALID_PASSWORD"})

    # JWT 토큰 발행
    access_token = jwt.encode({"id": str(user['_id'])}, SECRET, algorithm="HS256")
    return jsonify({"msg": "SUCCESS", "access_token": access_token}), 201


# 닉네임 중복체크
@app.route('/nickname', methods=['POST'])
def nickname_check():
    nick_name = request.form['nick_name']

    user = db.user.find_one({'nick_name': nick_name})
    if user is None:
        return jsonify({"msg": "사용할 수 있는 닉네임입니다."})

    return jsonify({'msg': '중복되는 닉네임입니다. 다시 입력해주세요.'})


# 날짜 클릭 함수입니다.
@app.route('/click_day', methods=['POST'])
@login_required
def clickedDay():
    receive_click_date = request.form['date_give']

    date_data = db.userdata.find_one({'date': receive_click_date})

    if date_data is None:
        resend_date_memo = ""
    else:
        resend_date_memo = date_data['Memo']

    return jsonify({'resend_date_memo': resend_date_memo})
# 날짜 클릭 함수 종료


# 캘린더 메모 변경 함수
@app.route('/change_memo_text', methods=['POST'])
@login_required
def changedMemo():
    receive_memo = request.form['change_memo_give']
    receive_key_class = request.form['key_class_give']

    date_data = db.userdata.find_one({'date': receive_key_class})

    if date_data is None:
        db.userdata.insert_one({'date': receive_key_class, 'Memo': receive_memo})
    else:
        db.userdata.update_one({'date': receive_key_class}, {'$set': {'Memo': receive_memo}})

    return jsonify(receive_key_class)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

