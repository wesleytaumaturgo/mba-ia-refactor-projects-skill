"""Tradução protocolo ↔ domínio para os relatórios."""
from flask import jsonify

from dto.task_dto import task_overdue_entry


class ReportController:
    def __init__(self, report_service):
        self._service = report_service

    def summary(self):
        data = self._service.summary()
        now = data.pop('now')
        overdue = data.pop('overdue_tasks')
        data['generated_at'] = str(data['generated_at'])
        data['overdue'] = {
            'count': len(overdue),
            'tasks': [task_overdue_entry(t, now) for t in overdue],
        }
        return jsonify(data), 200

    def user_report(self, user_id):
        report = self._service.user_report(user_id)
        user = report['user']
        return jsonify({
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': report['statistics'],
        }), 200
