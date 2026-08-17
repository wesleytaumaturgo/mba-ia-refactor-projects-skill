from database import db
from datetime import datetime

class Category(db.Model):
    __tablename__ = 'categories'

    DEFAULT_COLOR = '#000000'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), nullable=False, default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
