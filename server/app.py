from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from config import app, db
from models import User, MealOption, Menu, Order
from flask import jsonify, request
from datetime import datetime, date

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
    is_admin = data.get('is_admin', False)
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password, is_admin=is_admin)
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
        return jsonify({
            'token': access_token,
            'is_admin': user.is_admin
        }), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# Meal Management (Admin Only)
@app.route('/api/meal-options', methods=['POST'])
@jwt_required()
def create_meal_option():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    if not User.query.get(current_user_id).is_admin:
        return jsonify({'message': 'Access forbidden: Admins only'}), 403
    if not data or 'name' not in data or 'price' not in data:
        return jsonify({'message': 'Invalid input: name and price are required'}), 422
    try:
        price = float(data['price'])
    except ValueError:
        return jsonify({'message': 'Invalid input: price must be a number'}), 422

    name = data['name']

    try:
        new_meal = MealOption(name=name, price=price)
        db.session.add(new_meal)
        db.session.commit()
        return jsonify(new_meal.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({'message': 'Failed to add meal option'}), 422

# Get meal options(Admin only)
@app.route('/api/meal-options', methods=['GET'])
@jwt_required()
def get_meal_options():
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        if not user or not user.is_admin:
            return jsonify({'message': 'Access forbidden: Admins only'}), 403

        meal_options = MealOption.query.all()
        return jsonify([meal.to_dict() for meal in meal_options]), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Update meal option(Admin only)
@app.route('/api/meal-options/<int:meal_id>', methods=['PUT'])
@jwt_required()
def update_meal_option(meal_id):
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        if not User.query.get(current_user_id).is_admin:
            return jsonify({'message': 'Access forbidden: Admins only'}), 403
        meal = MealOption.query.get_or_404(meal_id)
        if 'name' in data:
            meal.name = data['name']
        if 'price' in data:
            meal.price = data['price']
        db.session.commit()
        return jsonify(meal.to_dict()), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Delete meal option(Admin only)
@app.route('/api/meal-options/<int:meal_id>', methods=['DELETE'])
@jwt_required()
def delete_meal_option(meal_id):
    try:
        current_user_id = get_jwt_identity()
        if not User.query.get(current_user_id).is_admin:
            return jsonify({'message': 'Access forbidden: Admins only'}), 403
        meal = MealOption.query.get_or_404(meal_id)
        db.session.delete(meal)
        db.session.commit()
        return jsonify({"message": "Meal option deleted successfully"}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Menu Management (Admin Only)
@app.route('/api/menus/setDaily', methods=['POST'])
@jwt_required()
def update_daily_menu():
    data = request.json
    date_str = data.get('date')
    meal_ids = data.get('meal_ids', [])

    app.logger.info(f"Received date: {date_str}")
    app.logger.info(f"Received meal_ids: {meal_ids}")

    if not date_str:
        return {'message': 'Date is required'}, 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        app.logger.info(f"Parsed date: {date}")
    except ValueError:
        return {'message': 'Invalid date format'}, 400

    menu = Menu.query.filter_by(date=date).first()
    if not menu:
        menu = Menu(date=date)
        db.session.add(menu)

    meal_options = MealOption.query.filter(MealOption.id.in_(meal_ids)).all()
    app.logger.info(f"Meal options found: {[meal.id for meal in meal_options]}")

    menu.meal_options = meal_options
    db.session.commit()

    return {'message': 'Menu updated successfully'}, 200

# Get daily menu
@app.route('/api/menus/today', methods=['GET'])
@jwt_required()
def get_daily_menu():
    try:
        today = datetime.now().date()
        app.logger.info(f"Fetching menu for date: {today}")
        menu = Menu.query.filter_by(date=today).first()

        if menu is None:
            return jsonify([]), 200

        meals = [meal_option.to_dict() for meal_option in menu.meal_options]
        return jsonify(meals), 200

    except Exception as e:
        app.logger.error(f"Error fetching daily menu: {str(e)}")
        return jsonify({"error": "An error occurred while fetching the daily menu"}), 500

# Remove a meal from menu
@app.route('/api/menus/removeMeal/<int:meal_id>', methods=['DELETE'])
@jwt_required()
def remove_meal_from_menu(meal_id):
    try:
        menu = Menu.query.filter_by(date=datetime.now().date()).first()
        if not menu:
            return jsonify({'message': 'No menu set for today'}), 404

        meal_option = MealOption.query.get(meal_id)
        if not meal_option:
            return jsonify({'message': 'Meal not found'}), 404

        if meal_option in menu.meal_options:
            menu.meal_options.remove(meal_option)
            db.session.commit()
            return jsonify({'message': 'Meal removed from menu'}), 200
        else:
            return jsonify({'message': 'Meal not in menu'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# Retrieve Menu (Customer)
@app.route('/api/menus/<date>', methods=['GET'])
@app.route('/api/menus/<date>', methods=['GET'])
@jwt_required()
def get_menu(date):
    menu_date = datetime.strptime(date, '%Y-%m-%d').date()
    menu = Menu.query.filter_by(date=menu_date).first()
    if not menu:
        return jsonify({'message': 'No menu found for this date'}), 404
    meal_options = [meal.to_dict() for meal in menu.meal_options]
    return jsonify({'date': date, 'meal_options': meal_options}), 200

# Order Management (Customer)
@app.route('/api/orders', methods=['POST'])
@jwt_required()
def place_order():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    meal_id = data.get('meal_option_id')
    quantity = data.get('quantity')
    order = Order(user_id=current_user_id, meal_option_id=meal_id, quantity=quantity)
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201

# Update an existing order
@app.route('/api/orders/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    data = request.get_json()
    order = Order.query.get_or_404(order_id)
    if order.user_id != get_jwt_identity():
        return jsonify({'message': 'Access forbidden: You do not own this order'}), 403
    order.meal_option_id = data.get('meal_option_id', order.meal_option_id)
    order.quantity = data.get('quantity', order.quantity)
    db.session.commit()
    return jsonify(order.to_dict()), 200

# Get all orders for the authenticated user
@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    current_user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=current_user_id).all()
    orders_with_meal_details = []
    for order in orders:
        meal = order.meal_option
        orders_with_meal_details.append({
            'id': order.id,
            'meal_name': meal.name,
            'meal_price': meal.price,
            'quantity': order.quantity,
            'status': order.status,
            'total_price': meal.price * order.quantity
        })

    return jsonify({'orders': orders_with_meal_details}), 200

# Delete an existing order
@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != get_jwt_identity():
        return jsonify({'message': 'Access forbidden: You do not own this order'}), 403
    db.session.delete(order)
    db.session.commit()
    return jsonify({'message': 'Order deleted'}), 200

# Order Management (Admin only)
# Get all orders
@app.route('/api/orders/admin', methods=['GET'])
@jwt_required()
def get_all_orders():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user or not user.is_admin:
        return jsonify({'message': 'Access forbidden: Admins only'}), 403

    orders = Order.query.all()
    return jsonify({'orders': [order.to_dict() for order in orders]}), 200


# Update Order status(Admin only)
@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user or not user.is_admin:
        return jsonify({'message': 'Access forbidden: Admins only'}), 403

    data = request.get_json()
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    new_status = data.get('status')
    if new_status:
        order.status = new_status
    db.session.commit()
    return jsonify(order.to_dict()), 200


# Delete Order status(Admin only)
@app.route('/api/orders/admin', methods=['DELETE'])
@jwt_required()
def bulk_delete_orders():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user or not user.is_admin:
        return jsonify({'message': 'Access forbidden: Admins only'}), 403

    data = request.get_json()
    for order_id in data['order_ids']:
        order = db.session.get(Order, order_id)
        if order:
            db.session.delete(order)
    db.session.commit()

    return jsonify({'message': 'Orders deleted'}), 200


# Update all orders (Admin only)
@app.route('/api/orders/status', methods=['PUT'])
@jwt_required()
def bulk_update_order_status():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user or not user.is_admin:
        return jsonify({'message': 'Access forbidden: Admins only'}), 403

    data = request.get_json()
    for order_data in data:
        order = db.session.get(Order, order_data['order_id'])
        if order:
            order.status = order_data.get('status', order.status)
    db.session.commit()
    updated_orders = [order.to_dict() for order in Order.query.filter(Order.id.in_([d['order_id'] for d in data])).all()]
    return jsonify(updated_orders), 200


# Revenue Tracking (Admin Only)
@app.route('/api/revenue', methods=['GET'])
@jwt_required()
def track_revenue():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user or not user.is_admin:
        return jsonify({'message': 'Access forbidden: Admins only'}), 403

    today = date.today()
    orders_today = db.session.query(Order).filter_by(date=today).all()
    total_revenue_today = sum(order.total_price for order in orders_today)
    revenue_data = []
    orders = db.session.query(Order).all()
    date_to_revenue = {}
    for order in orders:
        order_date = order.date.strftime('%Y-%m-%d')
        if order_date not in date_to_revenue:
            date_to_revenue[order_date] = {'totalRevenue': 0, 'orderCount': 0}
        date_to_revenue[order_date]['totalRevenue'] += order.total_price
        date_to_revenue[order_date]['orderCount'] += 1

    for date_str, data in date_to_revenue.items():
        revenue_data.append({
            'date': date_str,
            'totalRevenue': data['totalRevenue'],
            'orderCount': data['orderCount']
        })

    return jsonify({
        'date': str(today),
        'totalRevenueToday': total_revenue_today,
        'revenueData': revenue_data
    }), 200



if __name__ == '__main__':
    app.run(port=5555, debug=True)
