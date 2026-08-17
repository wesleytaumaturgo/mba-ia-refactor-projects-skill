from database import db
from datetime import datetime

from security.passwords import hash_password, needs_rehash, verify_password

class User(db.Model):
    __tablename__ = 'users'

    VALID_ROLES = ('user', 'admin', 'manager')
    MIN_PASSWORD_LENGTH = 4

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @classmethod
    def is_valid_role(cls, role):
        return role in cls.VALID_ROLES

    def set_password(self, pwd):
        self.password = hash_password(pwd)

    def check_password(self, pwd):
        return verify_password(self.password, pwd)

    def password_needs_rehash(self):
        return needs_rehash(self.password)

    def is_admin(self):
        return self.role == 'admin'
