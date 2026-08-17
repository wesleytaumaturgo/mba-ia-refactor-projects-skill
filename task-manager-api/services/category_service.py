"""Regra de negócio do agregado Category."""
from models.category import Category
from services.errors import NotFound


class CategoryService:
    def __init__(self, category_repository, task_repository, unit_of_work, validator):
        self._categories = category_repository
        self._tasks = task_repository
        self._uow = unit_of_work
        self._validator = validator

    def list_categories(self, limit=None, offset=None):
        """Devolve (categoria, nº de tasks) sem uma consulta por categoria."""
        categories = self._categories.list_all(limit=limit, offset=offset)
        counts = self._tasks.count_by_category()
        return [(category, counts.get(category.id, 0)) for category in categories]

    def get_category(self, category_id):
        category = self._categories.get(category_id)
        if category is None:
            raise NotFound('Categoria não encontrada')
        return category

    def create_category(self, payload):
        data = self._validator.validate_create(payload)
        category = Category()
        for field, value in data.items():
            setattr(category, field, value)
        with self._uow.transaction():
            self._categories.add(category)
        return category

    def update_category(self, category_id, payload):
        category = self.get_category(category_id)
        data = self._validator.validate_update(payload)
        with self._uow.transaction():
            for field, value in data.items():
                setattr(category, field, value)
        return category

    def delete_category(self, category_id):
        """Remove a categoria E desassocia as tasks na MESMA transação.

        Antes, a deleção deixava `tasks.category_id` apontando para uma linha
        inexistente — e a FK do SQLite não é aplicada em runtime (F-007/F-008).
        """
        category = self.get_category(category_id)
        with self._uow.transaction():
            self._tasks.clear_category(category_id)
            self._categories.delete(category)
