from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    sent_requests = db.relationship('GameRequest', foreign_keys='GameRequest.sender_id', backref='sender', lazy=True)
    received_requests = db.relationship('GameRequest', foreign_keys='GameRequest.receiver_id', backref='receiver', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class GameRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending')

    def __repr__(self):
        return f"GameRequest('{self.sender_id}', '{self.receiver_id}', '{self.status}')"


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    board = db.Column(db.String(9), nullable=False, default=' ' * 9)
    current_turn = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_finished = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

