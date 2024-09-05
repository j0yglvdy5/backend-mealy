from sqlalchemy_serializer import SerializerMixin
from config import db
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey

# Association table for many-to-many relationship between MealOption and Menu
meal_menu = Table('meal_menu', db.metadata,
    Column('meal_option_id', Integer, ForeignKey('meal_options.id'), primary_key=True),
    Column('menu_id', Integer, ForeignKey('menus.id'), primary_key=True)
)

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Relationship to Order
    orders = db.relationship('Order', back_populates='user')

    serialize_only = ('id', 'username', 'email', 'is_admin')

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin
        }

class MealOption(db.Model, SerializerMixin):
    __tablename__ = 'meal_options'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

    # Relationships to Order and Menu
    orders = db.relationship('Order', back_populates='meal_option')
    menus = db.relationship('Menu', secondary=meal_menu, back_populates='meal_options')

    serialize_only = ('id', 'name', 'price')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price
        }

class Menu(db.Model, SerializerMixin):
    __tablename__ = 'menus'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    meal_options = db.relationship('MealOption', secondary=meal_menu, back_populates='menus')

    serialize_only = ('id', 'date', 'meal_options')

    def serialize(self):
        serialized_data = super().serialize()
        serialized_data['meal_options'] = [meal_option.serialize() for meal_option in self.meal_options]
        return serialized_data

class Order(db.Model, SerializerMixin):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meal_option_id = db.Column(db.Integer, db.ForeignKey('meal_options.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Pending')

    # Relationships to User and MealOption
    user = db.relationship('User', back_populates='orders')
    meal_option = db.relationship('MealOption', back_populates='orders')

    serialize_only = ('id', 'user_id', 'meal_option_id', 'date', 'quantity', 'total_price', 'status')

    @property
    def total_price(self):
        return self.quantity * self.meal_option.price

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.username,
            'meal': self.meal_option.name,
            'quantity': self.quantity,
            'totalPrice': self.total_price,
            'status': self.status
        }
