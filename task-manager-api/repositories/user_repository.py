"""Acesso a dados do agregado User."""
from models.user import User


class UserRepository:
    def __init__(self, db):
        self._db = db

    def get(self, user_id):
        return self._db.session.get(User, user_id)

    def find_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def list_all(self, limit=None, offset=None):
        query = User.query.order_by(User.id)
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def count(self):
        return User.query.count()

    def email_taken_by_other(self, email, user_id):
        return (User.query.filter(User.email == email, User.id != user_id)
                .first() is not None)

    def add(self, user):
        self._db.session.add(user)
        return user

    def delete(self, user):
        self._db.session.delete(user)
