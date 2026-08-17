"""Acesso a dados do agregado Category."""
from models.category import Category


class CategoryRepository:
    def __init__(self, db):
        self._db = db

    def get(self, category_id):
        return self._db.session.get(Category, category_id)

    def list_all(self, limit=None, offset=None):
        query = Category.query.order_by(Category.id)
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def count(self):
        return Category.query.count()

    def add(self, category):
        self._db.session.add(category)
        return category

    def delete(self, category):
        self._db.session.delete(category)
