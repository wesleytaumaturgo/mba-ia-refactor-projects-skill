"""Tradução protocolo ↔ domínio para Task. Parse, chama o service, mapeia a resposta."""

from utils.helpers import utc_now

from flask import jsonify, request

from dto.task_dto import task_list_item, task_public, task_with_overdue


class TaskController:
    def __init__(self, task_service, pagination):
        self._service = task_service
        self._pagination = pagination

    def list_tasks(self):
        limit, offset = self._pagination.from_request(request.args)
        now = utc_now()
        tasks = self._service.list_tasks(limit=limit, offset=offset)
        return jsonify([task_list_item(t, now) for t in tasks]), 200

    def get_task(self, task_id):
        task = self._service.get_task(task_id)
        return jsonify(task_with_overdue(task)), 200

    def create_task(self):
        task = self._service.create_task(request.get_json(silent=True))
        return jsonify(task_public(task)), 201

    def update_task(self, task_id):
        task = self._service.update_task(task_id, request.get_json(silent=True))
        return jsonify(task_public(task)), 200

    def delete_task(self, task_id):
        self._service.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    def search_tasks(self):
        limit, offset = self._pagination.from_request(request.args)
        tasks = self._service.search(
            text=request.args.get('q', ''),
            status=request.args.get('status', ''),
            priority=request.args.get('priority', ''),
            user_id=request.args.get('user_id', ''),
            limit=limit, offset=offset,
        )
        return jsonify([task_public(t) for t in tasks]), 200

    def task_stats(self):
        return jsonify(self._service.statistics()), 200
