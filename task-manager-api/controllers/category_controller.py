"""Tradução protocolo ↔ domínio para Category."""
from flask import jsonify, request

from dto.category_dto import category_list_item, category_public


class CategoryController:
    def __init__(self, category_service, pagination):
        self._service = category_service
        self._pagination = pagination

    def list_categories(self):
        limit, offset = self._pagination.from_request(request.args)
        return jsonify([category_list_item(c, count)
                        for c, count in self._service.list_categories(limit=limit,
                                                                     offset=offset)]), 200

    def create_category(self):
        category = self._service.create_category(request.get_json(silent=True))
        return jsonify(category_public(category)), 201

    def update_category(self, cat_id):
        category = self._service.update_category(cat_id, request.get_json(silent=True))
        return jsonify(category_public(category)), 200

    def delete_category(self, cat_id):
        self._service.delete_category(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200
