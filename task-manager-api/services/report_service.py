"""Relatórios — regra de agregação do domínio, sem consulta por item.

Todas as contagens são expressas na própria consulta (GROUP BY / WHERE), não em laço
sobre a tabela inteira carregada em memória.
"""
from datetime import datetime, timedelta

from services.errors import NotFound
from services.task_service import completion_rate

RECENT_WINDOW_DAYS = 7

# Vocabulário de prioridade: única tradução valor→rótulo do projeto.
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}
HIGH_PRIORITY_THRESHOLD = 2


class ReportService:
    def __init__(self, task_repository, user_repository, category_repository):
        self._tasks = task_repository
        self._users = user_repository
        self._categories = category_repository

    def summary(self, now=None):
        now = now or datetime.utcnow()
        by_status = self._tasks.count_by_status()
        by_priority = self._tasks.count_by_priority()
        overdue = self._tasks.list_overdue(now)
        since = now - timedelta(days=RECENT_WINDOW_DAYS)

        task_counts = self._tasks.count_by_user()
        done_counts = self._tasks.count_done_by_user()

        productivity = []
        for user in self._users.list_all():
            total = task_counts.get(user.id, 0)
            done = done_counts.get(user.id, 0)
            productivity.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': done,
                'completion_rate': completion_rate(done, total),
            })

        return {
            'generated_at': now,
            'overview': {
                'total_tasks': self._tasks.count(),
                'total_users': self._users.count(),
                'total_categories': self._categories.count(),
            },
            'tasks_by_status': {status: by_status.get(status, 0)
                                for status in ('pending', 'in_progress', 'done', 'cancelled')},
            'tasks_by_priority': {label: by_priority.get(value, 0)
                                  for value, label in sorted(PRIORITY_LABELS.items())},
            'overdue_tasks': overdue,
            'recent_activity': {
                'tasks_created_last_7_days': self._tasks.count_created_since(since),
                'tasks_completed_last_7_days': self._tasks.count_done_since(since),
            },
            'user_productivity': productivity,
            'now': now,
        }

    def user_report(self, user_id, now=None):
        now = now or datetime.utcnow()
        user = self._users.get(user_id)
        if user is None:
            raise NotFound('Usuário não encontrado')

        tasks = self._tasks.list_by_user(user_id)
        counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
        overdue = 0
        high_priority = 0
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
            if task.priority is not None and task.priority <= HIGH_PRIORITY_THRESHOLD:
                high_priority += 1
            if task.is_overdue(now):
                overdue += 1

        total = len(tasks)
        return {
            'user': user,
            'statistics': {
                'total_tasks': total,
                'done': counts['done'],
                'pending': counts['pending'],
                'in_progress': counts['in_progress'],
                'cancelled': counts['cancelled'],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': completion_rate(counts['done'], total),
            },
        }
