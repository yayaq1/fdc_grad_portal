from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
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
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{username}:{password}@postgres_container/studentdirectory'
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

    def check_password(self, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return self.password_hash == password_hash
    
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

class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    user = db.relationship('User', backref=db.backref('experiences', lazy=True))


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
    
    if not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    user = User.query.filter_by(email=email).first()

    token = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))
    
    return jsonify({'token': token}), 200

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

@app.route('/search', methods=['GET'])
def search():
    name = request.args.get('Name')
    class_of = request.args.get('ClassOf')
    program = request.args.get('Program')
    skills = request.args.get('Skills')
    minor = request.args.get('Minor')
    achievements = request.args.get('Achievements')
    project_title = request.args.get('ProjectTitle')
    interest = request.args.get('Interest')

    query = Profile.query.join(User).filter(User.is_admin == False)

    if name:
        query = query.filter(Profile.full_name.ilike(f'%{name}%'))
    if class_of:
        query = query.filter(Profile.graduation_year == class_of)
    if program:
        query = query.filter(Profile.major == program)
    if skills:
        query = query.join(UserSkill).join(Skill).filter(Skill.skill_name.in_(skills.split(',')))
    if minor:
        query = query.filter(Profile.minor == minor)
    if achievements:
        query = query.join(Achievement).filter(Achievement.title.ilike(f'%{achievements}%'))
    if project_title:
        query = query.join(FinalYearProject).filter(FinalYearProject.title.ilike(f'%{project_title}%'))
    if interest:
        query = query.filter(Profile.aspiration_statement.ilike(f'%{interest}%'))

    results = query.all()

    response = []
    for result in results:
        response.append({
            'user_id': result.user_id,
            'name': result.full_name,
            'graduation_year': result.graduation_year,
            'major': result.major
        })

    return jsonify(response), 200

@app.route('/retrieve-info', methods=['GET'])
def retrieve_info():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({'error': 'User not found'}), 404
    
    skills = Skill.query.join(UserSkill).filter(UserSkill.user_id == user_id).all()
    skill_list = [skill.skill_name for skill in skills]
    
    project = FinalYearProject.query.filter_by(user_id=user_id).first()

    achievements_list = []
    

    achievements = Achievement.query.filter_by(user_id=user_id).all()
    for achievement in achievements:
        achievements_list.append({
            'Title': achievement.title,
            'Description': achievement.description,
            'DateAchieved': achievement.date_achieved
        })

        # NEW: Query for experiences
    experiences = Experience.query.filter_by(user_id=user_id).all()
    experience_list = [{
        'Title': exp.title,
        'Description': exp.description,
        'StartDate': exp.start_date.isoformat() if exp.start_date else None,
        'EndDate': exp.end_date.isoformat() if exp.end_date else None,
    } for exp in experiences]

    response = {
        'Name': profile.full_name,
        'ProfilePictureURL': profile.profile_picture_url,
        'ClassOf': profile.graduation_year,
        'Program': profile.major,
        'Skills': skill_list,
        'Minor': profile.minor,
        'AspirationStatement': profile.aspiration_statement,
        'LinkedInURL': profile.linkedin_url,
        'ResumeURL': profile.resume_url,
        'Achievements': achievements_list,
        'ProjectDetails': project.title if project else None,
        'ProjectImages': project.images if project else None,
        'Experiences': experience_list,  # Include the experiences in the response
        'Email': User.query.get(user_id).email,
        'FinalYearProject': {
            'Title': project.title if project else None,
            'Description': project.description if project else None,
            'StartDate': project.start_date if project else None,
            'EndDate': project.end_date if project else None,
            'ProjectURL': project.project_url if project else None,
            'Images': project.images if project else None
        }
    }
    


    return jsonify(response), 200

@app.route('/skills', methods=['POST'])
@jwt_required()
def add_skill():
    current_user = get_jwt_identity()
    if current_user != 'admin@sudo':
        return jsonify({'error': 'Unauthorized access'}), 401
    
    data = request.json
    skill_name = data.get('skill_name')
    if not skill_name:
        return jsonify({'error': 'Skill name is required'}), 400
    
    existing_skill = Skill.query.filter_by(skill_name=skill_name).first()
    if existing_skill:
        return jsonify({'error': 'Skill already exists'}), 400
    
    new_skill = Skill(skill_name=skill_name)
    db.session.add(new_skill)
    db.session.commit()
    
    return jsonify({'message': 'Skill added successfully'}), 201

@app.route('/skills/<int:skill_id>', methods=['PATCH'])
@jwt_required()
def update_skill(skill_id):
    current_user = get_jwt_identity()
    if current_user != 'admin@sudo':
        return jsonify({'error': 'Unauthorized access'}), 401
    
    data = request.json
    skill_name = data.get('skill_name')
    if not skill_name:
        return jsonify({'error': 'Skill name is required'}), 400
    
    skill = Skill.query.get(skill_id)
    if not skill:
        return jsonify({'error': 'Skill not found'}), 404
    
    skill.skill_name = skill_name
    db.session.commit()
    
    return jsonify({'message': 'Skill updated successfully'}), 200

@app.route('/skills/<int:skill_id>', methods=['DELETE'])
@jwt_required()
def delete_skill(skill_id):
    current_user = get_jwt_identity()
    if current_user != 'admin@sudo':
        return jsonify({'error': 'Unauthorized access'}), 401
    
    skill = Skill.query.get(skill_id)
    if not skill:
        return jsonify({'error': 'Skill not found'}), 404
    
    db.session.delete(skill)
    db.session.commit()
    
    return jsonify({'message': 'Skill deleted successfully'}), 200

@app.route('/skills', methods=['GET'])
def get_all_skills():
    skills = Skill.query.all()
    skill_list = [skill.skill_name for skill in skills]
    return jsonify(skill_list), 200

@app.route('/user/skills', methods=['POST'])
@jwt_required()
def add_user_skill():
    current_user = get_jwt_identity()
    data = request.json
    skill_name = data.get('skill_name')
    if not skill_name:
        return jsonify({'error': 'Skill name is required'}), 400
    
    skill = Skill.query.filter_by(skill_name=skill_name).first()
    if not skill:
        return jsonify({'error': 'Skill not found'}), 404
    
    user_skill = UserSkill.query.filter_by(user_id=current_user, skill_id=skill.id).first()
    if user_skill:
        return jsonify({'error': 'User skill already exists'}), 400
    
    new_user_skill = UserSkill(user_id=current_user, skill_id=skill.id)
    db.session.add(new_user_skill)
    db.session.commit()
    
    return jsonify({'message': 'User skill added successfully'}), 201

@app.route('/user/skills/<int:user_skill_id>', methods=['PATCH'])
@jwt_required()
def update_user_skill(user_skill_id):
    current_user = get_jwt_identity()
    data = request.json
    skill_name = data.get('skill_name')
    if not skill_name:
        return jsonify({'error': 'Skill name is required'}), 400
    
    skill = Skill.query.filter_by(skill_name=skill_name).first()
    if not skill:
        return jsonify({'error': 'Skill not found'}), 404
    
    user_skill = UserSkill.query.filter_by(id=user_skill_id, user_id=current_user).first()
    if not user_skill:
        return jsonify({'error': 'User skill not found'}), 404
    
    user_skill.skill_id = skill.id
    db.session.commit()
    
    return jsonify({'message': 'User skill updated successfully'}), 200

@app.route('/user/skills/<int:user_skill_id>', methods=['DELETE'])
@jwt_required()
def delete_user_skill(user_skill_id):
    current_user = get_jwt_identity()
    user_skill = UserSkill.query.filter_by(id=user_skill_id, user_id=current_user).first()
    if not user_skill:
        return jsonify({'error': 'User skill not found'}), 404
    
    db.session.delete(user_skill)
    db.session.commit()
    
    return jsonify({'message': 'User skill deleted successfully'}), 200

@app.route('/profile', methods=['POST'])
@jwt_required()
def add_profile():
    current_user = get_jwt_identity()
    data = request.json
    full_name = data.get('full_name')
    profile_picture_url = data.get('profile_picture_url')
    major = data.get('major')
    minor = data.get('minor')
    graduation_year = data.get('graduation_year')
    aspiration_statement = data.get('aspiration_statement')
    linkedin_url = data.get('linkedin_url')
    resume_url = data.get('resume_url')
    
    profile = Profile.query.filter_by(user_id=current_user).first()
    if profile:
        return jsonify(message='Profile already exists'), 400
    
    new_profile = Profile(user_id=current_user, full_name=full_name, profile_picture_url=profile_picture_url,
                            major=major, minor=minor, graduation_year=graduation_year,
                            aspiration_statement=aspiration_statement, linkedin_url=linkedin_url,
                            resume_url=resume_url)
    db.session.add(new_profile)
    db.session.commit()
    
    return jsonify(message='Profile added successfully'), 201


@app.route('/profile', methods=['PATCH'])
@jwt_required()
def update_profile():
    current_user = get_jwt_identity()
    data = request.json
    full_name = data.get('full_name')
    profile_picture_url = data.get('profile_picture_url')
    major = data.get('major')
    minor = data.get('minor')
    graduation_year = data.get('graduation_year')
    aspiration_statement = data.get('aspiration_statement')
    linkedin_url = data.get('linkedin_url')
    resume_url = data.get('resume_url')
    
    profile = Profile.query.filter_by(user_id=current_user).first()
    if not profile:
        return jsonify(message='Profile not found'), 404
    
    profile.full_name = full_name
    profile.profile_picture_url = profile_picture_url
    profile.major = major
    profile.minor = minor
    profile.graduation_year = graduation_year
    profile.aspiration_statement = aspiration_statement
    profile.linkedin_url = linkedin_url
    profile.resume_url = resume_url
    profile.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(message='Profile updated successfully'), 200


@app.route('/profile', methods=['DELETE'])
@jwt_required()
def delete_profile():
    current_user = get_jwt_identity()
    
    profile = Profile.query.filter_by(user_id=current_user).first()
    if not profile:
        return jsonify(message='Profile not found'), 404
    
    db.session.delete(profile)
    db.session.commit()
    
    return jsonify(message='Profile deleted successfully'), 200

@app.route('/achievements', methods=['POST'])
@jwt_required()
def add_achievement():
    current_user = get_jwt_identity()
    data = request.json
    title = data.get('title')
    description = data.get('description')
    date_achieved = data.get('date_achieved')
    
    achievement = Achievement(user_id=current_user, title=title, description=description, date_achieved=date_achieved)
    db.session.add(achievement)
    db.session.commit()
    
    return jsonify(message='Achievement added successfully'), 201

@app.route('/achievements/<int:achievement_id>', methods=['PATCH'])
@jwt_required()
def update_achievement(achievement_id):
    current_user = get_jwt_identity()
    data = request.json
    title = data.get('title')
    description = data.get('description')
    date_achieved = data.get('date_achieved')
    
    achievement = Achievement.query.filter_by(id=achievement_id, user_id=current_user).first()
    if not achievement:
        return jsonify(message='Achievement not found'), 404
    
    achievement.title = title
    achievement.description = description
    achievement.date_achieved = date_achieved
    db.session.commit()
    
    return jsonify(message='Achievement updated successfully'), 200

@app.route('/achievements/<int:achievement_id>', methods=['DELETE'])
@jwt_required()
def delete_achievement(achievement_id):
    current_user = get_jwt_identity()
    
    achievement = Achievement.query.filter_by(id=achievement_id, user_id=current_user).first()
    if not achievement:
        return jsonify(message='Achievement not found'), 404
    
    db.session.delete(achievement)
    db.session.commit()
    
    return jsonify(message='Achievement deleted successfully'), 200

@app.route('/final-year-project', methods=['POST'])
@jwt_required()
def add_final_year_project():
    current_user = get_jwt_identity()
    data = request.json
    title = data.get('title')
    description = data.get('description')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    project_url = data.get('project_url')
    images = data.get('images')
    
    final_year_project = FinalYearProject(user_id=current_user, title=title, description=description,
                                            start_date=start_date, end_date=end_date, project_url=project_url,
                                            images=images)
    db.session.add(final_year_project)
    db.session.commit()
    
    return jsonify({'message': 'Project added successfully'}), 200

@app.route('/final-year-project/<int:project_id>', methods=['PATCH'])
@jwt_required()
def update_final_year_project(project_id):
    current_user = get_jwt_identity()
    data = request.json
    title = data.get('title')
    description = data.get('description')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    project_url = data.get('project_url')
    images = data.get('images')
    
    final_year_project = FinalYearProject.query.filter_by(id=project_id, user_id=current_user).first()
    if not final_year_project:
        return jsonify({'message': 'Project not found'}), 404
    
    final_year_project.title = title
    final_year_project.description = description
    final_year_project.start_date = start_date
    final_year_project.end_date = end_date
    final_year_project.project_url = project_url
    final_year_project.images = images
    db.session.commit()
    
    return jsonify({'message': 'Project updated successfully'}), 200

@app.route('/final-year-project/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_final_year_project(project_id):
    current_user = get_jwt_identity()
    
    final_year_project = FinalYearProject.query.filter_by(id=project_id, user_id=current_user).first()
    if not final_year_project:
        return jsonify({'message': 'Project not found'}), 404
    
    db.session.delete(final_year_project)
    db.session.commit()
    
    return jsonify({'message': 'Project deleted successfully'}), 200

@app.route('/user/experiences', methods=['POST'])
@jwt_required()
def add_experience():
    current_user_id = get_jwt_identity()
    data = request.json
    new_experience = Experience(
        user_id=current_user_id,
        title=data['title'],
        description=data['description'],
        start_date=data.get('start_date'),
        end_date=data.get('end_date')
    )
    db.session.add(new_experience)
    db.session.commit()
    return jsonify({'message': 'Experience added successfully', 'id': new_experience.id}), 201

@app.route('/user/experiences', methods=['GET'])
@jwt_required()
def get_experiences():
    current_user_id = get_jwt_identity()
    experiences = Experience.query.filter_by(user_id=current_user_id).all()
    experiences_data = [{
        'id': exp.id,
        'title': exp.title,
        'description': exp.description,
        'start_date': exp.start_date,
        'end_date': exp.end_date
    } for exp in experiences]
    return jsonify(experiences_data), 200

@app.route('/user/experiences/<int:exp_id>', methods=['PATCH'])
@jwt_required()
def update_experience(exp_id):
    current_user_id = get_jwt_identity()
    data = request.json
    experience = Experience.query.filter_by(id=exp_id, user_id=current_user_id).first()
    if not experience:
        return jsonify({'error': 'Experience not found'}), 404
    
    experience.title = data.get('title', experience.title)
    experience.description = data.get('description', experience.description)
    experience.start_date = data.get('start_date', experience.start_date)
    experience.end_date = data.get('end_date', experience.end_date)
    db.session.commit()
    return jsonify({'message': 'Experience updated successfully'}), 200

@app.route('/user/experiences/<int:exp_id>', methods=['DELETE'])
@jwt_required()
def delete_experience(exp_id):
    current_user_id = get_jwt_identity()
    experience = Experience.query.filter_by(id=exp_id, user_id=current_user_id).first()
    if not experience:
        return jsonify({'error': 'Experience not found'}), 404
    
    db.session.delete(experience)
    db.session.commit()
    return jsonify({'message': 'Experience deleted successfully'}), 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6001, debug=True)
