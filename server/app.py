from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from config import app, db
from models import User, MealOption, Menu, Order
from flask import jsonify, request
from datetime import datetime

# Setup Flask-JWT-Extended and Bcrypt
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

@app.before_request
def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/')
def index():
    return '<h1>Project Server</h1>'

# User Registration
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    existing_user = User.query.filter((User.username == data['username']) | (User.email == data['email'])).first()
    if existing_user:
        return jsonify({"message": "Username or email already exists"}), 400
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.serialize()), 201

# User Login
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({'token': access_token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# Meal Management (Admin Only)
@app.route('/api/meal-options', methods=['POST'])
@jwt_required()
def create_meal_option():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    if not User.query.get(current_user_id).is_admin:
        return jsonify({'message': 'Access forbidden: Admins only'}), 403
    new_meal = MealOption(name=data['name'], price=data['price'])
    db.session.add(new_meal)
    db.session.commit()
    return jsonify(new_meal.serialize()), 201

@app.route('/api/meal-options/<int:meal_id>', methods=['PUT'])
@jwt_required()
def update_meal_option(meal_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    if not User.query.get(current_user_id).is_admin:
        return jsonify({'message': 'Access forbidden: Admins only'}), 403
    meal = MealOption.query.get_or_404(meal_id)
    meal.name = data.get('name', meal.name)
    meal.price = data.get('price', meal.price)
    db.session.commit()
    return jsonify(meal.serialize()), 200

@app.route('/api/meal-options/<int:meal_id>', methods=['DELETE'])
@jwt_required()
def delete_meal_option(meal_id):
    current_user_id = get_jwt_identity()
    if not User.query.get(current_user_id).is_admin:
        return jsonify({'message': 'Access forbidden: Admins only'}), 403
    meal = MealOption.query.get_or_404(meal_id)
    db.session.delete(meal)
    db.session.commit()
    return jsonify({"message": "Meal option deleted successfully"}), 200

# Menu Management (Admin Only)
@app.route('/api/menus', methods=['POST'])
@jwt_required()
def create_menu():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    if not User.query.get(current_user_id).is_admin:
        return jsonify({'message': 'Access forbidden: Admins only'}), 403
    date_str = data.get('date')
    meal_options_ids = data.get('meal_options')
    menu_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    menu = Menu(date=menu_date)
    db.session.add(menu)
    db.session.commit()
    for meal_id in meal_options_ids:
        meal_option = MealOption.query.get_or_404(meal_id)
        menu.meal_options.append(meal_option)
    db.session.commit()
    return jsonify({'message': 'Menu created successfully'}), 201

if __name__ == '__main__':
    app.run(port=5555, debug=True)

