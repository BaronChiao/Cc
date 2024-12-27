from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from sqlalchemy import and_
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # 用于JWT加密
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    friends = db.relationship('Friendship',
                            foreign_keys=[Friendship.user_id],
                            backref='user',
                            lazy='dynamic')
    friend_requests = db.relationship('Friendship',
                                    foreign_keys=[Friendship.friend_id],
                                    backref='friend',
                                    lazy='dynamic')
    vip_level = db.Column(db.Integer, db.ForeignKey('vip_level.id'), nullable=True)
    vip_expire_date = db.Column(db.DateTime, nullable=True)
    created_circles = db.relationship('Circle', backref='creator', lazy='dynamic')
    circle_memberships = db.relationship('CircleMember', backref='user', lazy='dynamic')

# 好友关系模型
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 添加VIP等级模型
class VIPLevel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # VIP等级名称
    level = db.Column(db.Integer, nullable=False)    # 等级数值
    price = db.Column(db.Float, nullable=False)      # 价格
    max_private_circles = db.Column(db.Integer, nullable=False)  # 可创建的私密圈子数量

# 添加圈子模型
class Circle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = db.relationship('CircleMember', backref='circle', lazy='dynamic')
    posts = db.relationship('Post', backref='circle', lazy='dynamic')

# 圈子成员模型
class CircleMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    circle_id = db.Column(db.Integer, db.ForeignKey('circle.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # member, moderator, admin
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

# 帖子模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    circle_id = db.Column(db.Integer, db.ForeignKey('circle.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

# 评论模型
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 创建数据库表
with app.app_context():
    db.create_all()

# 注册路由
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'message': '用户名已存在'}), 400
    
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': '注册成功'}), 201

# 登录路由
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    # 生成JWT令牌
    token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }, app.config['SECRET_KEY'])
    
    return jsonify({
        'token': token,
        'username': user.username
    }), 200

# Socket.IO事件处理
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(message):
    emit('message', message, broadcast=True, skip_sid=request.sid)

# 添加好友相关的路由
@app.route('/api/friends/search', methods=['GET'])
def search_users():
    query = request.args.get('query', '')
    current_user_id = get_current_user_id()  # 从JWT token获取当前用户ID
    
    users = User.query.filter(
        and_(
            User.username.like(f'%{query}%'),
            User.id != current_user_id
        )
    ).all()
    
    return jsonify([{
        'id': user.id,
        'username': user.username
    } for user in users])

@app.route('/api/friends/request', methods=['POST'])
def send_friend_request():
    data = request.get_json()
    friend_id = data.get('friend_id')
    current_user_id = get_current_user_id()
    
    # 检查是否已经是好友
    existing = Friendship.query.filter(
        or_(
            and_(Friendship.user_id == current_user_id, Friendship.friend_id == friend_id),
            and_(Friendship.user_id == friend_id, Friendship.friend_id == current_user_id)
        )
    ).first()
    
    if existing:
        return jsonify({'message': '已经发送过好友请求或已经是好友'}), 400
    
    friendship = Friendship(user_id=current_user_id, friend_id=friend_id)
    db.session.add(friendship)
    db.session.commit()
    
    return jsonify({'message': '好友请求已发送'})

@app.route('/api/friends/requests', methods=['GET'])
def get_friend_requests():
    current_user_id = get_current_user_id()
    requests = Friendship.query.filter_by(
        friend_id=current_user_id,
        status='pending'
    ).all()
    
    return jsonify([{
        'id': req.id,
        'user_id': req.user_id,
        'username': User.query.get(req.user_id).username,
        'status': req.status,
        'created_at': req.created_at.isoformat()
    } for req in requests])

@app.route('/api/friends/respond', methods=['POST'])
def respond_friend_request():
    data = request.get_json()
    request_id = data.get('request_id')
    response = data.get('response')  # 'accept' or 'reject'
    
    friend_request = Friendship.query.get(request_id)
    if not friend_request:
        return jsonify({'message': '请求不存在'}), 404
    
    if response == 'accept':
        friend_request.status = 'accepted'
    else:
        friend_request.status = 'rejected'
    
    db.session.commit()
    return jsonify({'message': '已处理好友请求'})

@app.route('/api/friends', methods=['GET'])
def get_friends():
    current_user_id = get_current_user_id()
    friends = Friendship.query.filter(
        or_(
            and_(Friendship.user_id == current_user_id, Friendship.status == 'accepted'),
            and_(Friendship.friend_id == current_user_id, Friendship.status == 'accepted')
        )
    ).all()
    
    friend_list = []
    for friendship in friends:
        friend_id = friendship.friend_id if friendship.user_id == current_user_id else friendship.user_id
        friend = User.query.get(friend_id)
        friend_list.append({
            'id': friend.id,
            'username': friend.username
        })
    
    return jsonify(friend_list)

# 辅助函数：从JWT token获取当前用户ID
def get_current_user_id():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

# 添加VIP相关路由
@app.route('/api/vip/levels', methods=['GET'])
def get_vip_levels():
    levels = VIPLevel.query.all()
    return jsonify([{
        'id': level.id,
        'name': level.name,
        'level': level.level,
        'price': level.price,
        'max_private_circles': level.max_private_circles
    } for level in levels])

@app.route('/api/vip/purchase', methods=['POST'])
def purchase_vip():
    data = request.get_json()
    level_id = data.get('level_id')
    current_user_id = get_current_user_id()
    
    user = User.query.get(current_user_id)
    vip_level = VIPLevel.query.get(level_id)
    
    if not vip_level:
        return jsonify({'message': 'VIP等级不存在'}), 404
    
    # 这里应该添加实际的支付逻辑
    # 假设支付成功
    user.vip_level = level_id
    user.vip_expire_date = datetime.utcnow() + timedelta(days=30)  # 30天会员期
    db.session.commit()
    
    return jsonify({'message': 'VIP购买成功'})

# 添加圈子相关路由
@app.route('/api/circles', methods=['GET'])
def get_circles():
    current_user_id = get_current_user_id()
    # 获取公开圈子和用户加入的私密圈子
    public_circles = Circle.query.filter_by(is_private=False).all()
    private_circles = Circle.query.join(CircleMember).filter(
        Circle.is_private==True,
        CircleMember.user_id==current_user_id
    ).all()
    
    circles = public_circles + private_circles
    return jsonify([{
        'id': circle.id,
        'name': circle.name,
        'description': circle.description,
        'is_private': circle.is_private,
        'creator': User.query.get(circle.creator_id).username,
        'member_count': circle.members.count()
    } for circle in circles])

@app.route('/api/circles', methods=['POST'])
def create_circle():
    data = request.get_json()
    current_user_id = get_current_user_id()
    user = User.query.get(current_user_id)
    
    if data.get('is_private'):
        if not user.vip_level:
            return jsonify({'message': '只有VIP用户才能创建私密圈子'}), 403
        
        vip_level = VIPLevel.query.get(user.vip_level)
        current_private_circles = Circle.query.filter_by(
            creator_id=current_user_id,
            is_private=True
        ).count()
        
        if current_private_circles >= vip_level.max_private_circles:
            return jsonify({'message': '已达到当前VIP等级可创建的私密圈子上限'}), 403
    
    circle = Circle(
        name=data.get('name'),
        description=data.get('description'),
        creator_id=current_user_id,
        is_private=data.get('is_private', False)
    )
    
    db.session.add(circle)
    # 创建者自动成为管理员
    member = CircleMember(
        circle=circle,
        user_id=current_user_id,
        role='admin'
    )
    db.session.add(member)
    db.session.commit()
    
    return jsonify({'message': '圈子创建成功', 'circle_id': circle.id})

@app.route('/api/circles/<int:circle_id>/invite', methods=['POST'])
def invite_to_circle(circle_id):
    data = request.get_json()
    current_user_id = get_current_user_id()
    user_id = data.get('user_id')
    
    circle = Circle.query.get(circle_id)
    if not circle:
        return jsonify({'message': '圈子不存在'}), 404
    
    # 检查权限
    member = CircleMember.query.filter_by(
        circle_id=circle_id,
        user_id=current_user_id
    ).first()
    
    if not member or member.role not in ['admin', 'moderator']:
        return jsonify({'message': '没有邀请权限'}), 403
    
    new_member = CircleMember(
        circle_id=circle_id,
        user_id=user_id
    )
    db.session.add(new_member)
    db.session.commit()
    
    return jsonify({'message': '邀请成功'})

@app.route('/api/circles/<int:circle_id>/posts', methods=['GET'])
def get_circle_posts(circle_id):
    current_user_id = get_current_user_id()
    circle = Circle.query.get(circle_id)
    
    if not circle:
        return jsonify({'message': '圈子不存在'}), 404
    
    if circle.is_private:
        member = CircleMember.query.filter_by(
            circle_id=circle_id,
            user_id=current_user_id
        ).first()
        if not member:
            return jsonify({'message': '没有权限查看该圈子'}), 403
    
    posts = Post.query.filter_by(circle_id=circle_id).order_by(Post.created_at.desc()).all()
    return jsonify([{
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'author': User.query.get(post.author_id).username,
        'created_at': post.created_at.isoformat(),
        'comment_count': post.comments.count()
    } for post in posts])

@app.route('/api/circles/<int:circle_id>/posts', methods=['POST'])
def create_post(circle_id):
    data = request.get_json()
    current_user_id = get_current_user_id()
    
    circle = Circle.query.get(circle_id)
    if not circle:
        return jsonify({'message': '圈子不存在'}), 404
    
    if circle.is_private:
        member = CircleMember.query.filter_by(
            circle_id=circle_id,
            user_id=current_user_id
        ).first()
        if not member:
            return jsonify({'message': '没有权限在该圈子发帖'}), 403
    
    post = Post(
        title=data.get('title'),
        content=data.get('content'),
        author_id=current_user_id,
        circle_id=circle_id
    )
    db.session.add(post)
    db.session.commit()
    
    return jsonify({'message': '发帖成功', 'post_id': post.id})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)