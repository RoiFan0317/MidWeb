from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import openai
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret-key'

db = SQLAlchemy()
db.init_app(app)

#註冊Start
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    avatar = db.Column(db.String(200), default='https://via.placeholder.com/150')
    messages = db.relationship('Message', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'avatar': self.avatar
        }

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Message {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'user_id': self.user_id,
            'user': User.query.get(self.user_id).to_dict()
        }

@app.route('/register', methods=['POST'])
def register():
    data = request.form
    username = data.get('username')
    password = data.get('password')
    avatar = data.get('avatar')

    if not username or not password:
        return 'Missing username or password',1400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return 'Username already exists', 1405

    new_user = User(username=username, avatar=avatar)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return 'Registration successful', 1201
    return jsonify({'success': True, 'message': '註冊成功'})
#註冊 End


#登入 Start


@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        return jsonify({'message': '登入成功', 'username': user.username, 'avatar': user.avatar})
    else:
        return jsonify({'message': '帳號或密碼錯誤'})
#登入End



#留言板 Start
@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if request.method == 'POST':
        data = request.form
        content = data.get('content')
        user_id = data.get('user_id')

        if not content or not user_id:
            return 'Missing content or user_id', 2400

        user = User.query.get(user_id)
        if not user:
            return 'User not found', 2404

        message = Message(content=content, user_id=user_id)
        db.session.add(message)
        db.session.commit()

        return jsonify(message.to_dict()), 2201

    elif request.method == 'GET':
        messages = Message.query.all()
        return jsonify([m.to_dict() for m in messages])

@app.route('/messages/<int:id>', methods=['DELETE'])
def delete_message(id):
    message = Message.query.get(id)
    if not message:
        return 'Message not found', 2404

    db.session.delete(message)
    db.session.commit()

    return 'Message deleted', 2204
#留言板 End

# OpenAI


# 請將以下 YOUR_API_KEY 替換為您的 OpenAI API 密鑰
openai.api_key = "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"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    print("user_message")
    if not user_message:
        return jsonify(error="請輸入訊息")

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"User: {user_message}\nAI:",
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.5,
    )
    ai_message = response.choices[0].text.strip()
    
    return jsonify(message=ai_message)

if __name__ == '__main__':
    app.run()
# OpenAI 

# Create the Tables 把上面的全部都定義完再 Create
with app.app_context():
    db.create_all()