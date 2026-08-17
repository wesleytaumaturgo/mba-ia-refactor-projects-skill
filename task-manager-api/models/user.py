from database import db
from datetime import datetime

from security.passwords import hash_password, needs_rehash, verify_password

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        # A projeção de saída vive em dto/user_dto.py, com allowlist explícita.
        # A credencial não atravessa a fronteira de resposta.
        from dto.user_dto import user_public
        return user_public(self)

    def set_password(self, pwd):
        self.password = hash_password(pwd)

    def check_password(self, pwd):
        return verify_password(self.password, pwd)

    def password_needs_rehash(self):
        return needs_rehash(self.password)

    def is_admin(self):
        if self.role == 'admin':
            return True
        else:
            return False
