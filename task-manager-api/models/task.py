from database import db

from utils.helpers import utc_now

class Task(db.Model):
    __tablename__ = 'tasks'

    # Invariantes que valem para toda instância, em qualquer caso de uso.
    VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
    TERMINAL_STATUSES = ('done', 'cancelled')
    MIN_PRIORITY = 1
    MAX_PRIORITY = 5
    MIN_TITLE_LENGTH = 3
    MAX_TITLE_LENGTH = 200

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='pending')
    priority = db.Column(db.Integer, nullable=False, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now,
                           onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    @classmethod
    def is_valid_status(cls, status):
        return status in cls.VALID_STATUSES

    @classmethod
    def is_valid_priority(cls, priority):
        return isinstance(priority, int) and cls.MIN_PRIORITY <= priority <= cls.MAX_PRIORITY

    def is_overdue(self, now=None):
        """Regra de domínio única: vencida e ainda não terminal."""
        if not self.due_date:
            return False
        return (self.due_date < (now or utc_now())
                and self.status not in self.TERMINAL_STATUSES)
