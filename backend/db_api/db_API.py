from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, request, jsonify
from datetime import datetime
import hashlib
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from config import username, password, secret_key

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{username}:{password}@localhost/db'
app.config['SECRET_KEY'] = secret_key
app.config['JWT_SECRET_KEY'] = secret_key
db = SQLAlchemy(app)

Compress(app)
CORS(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per minute"],
    storage_uri="memory://",
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP(timezone=True), default=datetime.utcnow)

class Profile(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    profile_picture_url = db.Column(db.Text)
    major = db.Column(db.String(255))
    minor = db.Column(db.String(255))
    graduation_year = db.Column(db.Integer)
    aspiration_statement = db.Column(db.Text)
    linkedin_url = db.Column(db.Text)
    resume_url = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP(timezone=True), default=datetime.utcnow)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(255), unique=True, nullable=False)

class UserSkill(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), primary_key=True)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date_achieved = db.Column(db.Date)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_description = db.Column(db.Text)
    activity_date = db.Column(db.TIMESTAMP(timezone=True), default=datetime.utcnow)

class FinalYearProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.TIMESTAMP(timezone=True))
    end_date = db.Column(db.TIMESTAMP(timezone=True))
    project_url = db.Column(db.Text)
    images = db.Column(db.ARRAY(db.Text))

with app.app_context():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'Email already registered'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    new_user = User(email=email, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if user.password_hash != password_hash:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    token = jwt.encode({'email': email, 'exp': datetime.utcnow() + timedelta(hours=1)}, app.config['SECRET_KEY'])
    
    return jsonify({'token': token.decode('utf-8')}), 200

@app.route('/check_token_status', methods=['GET'])
@jwt_required()
def check_token_status():
    if get_jwt_identity():
        try:
            verify_jwt_in_request()
            return jsonify({"token_status": True})
        except:
            return jsonify({"token_status": False})
    else:
        return jsonify({"token_status": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6001, debug=True)
