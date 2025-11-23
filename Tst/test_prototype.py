import unittest
from Src.start_service import start_service
from Src.Logics.prototype_report import PrototypeReport
from Src.reposity import reposity
from Src.Core.validator import operation_exception
from Src.Dtos.filter_dto import filter_dto, FilterOperator

class TestPrototype(unittest.TestCase):

    def setUp(self):
        """Настройка перед каждым тестом"""
        self.start_service = start_service()
        self.start_service.start()  # загружаем тестовые данные

    def test_filter_by_nomenclature(self):
        """Тест фильтрации по номенклатуре"""
        # Подготовка: получаем транзакции
        transactions = self.start_service.data.get(reposity.transaction_key(), [])
        start_prototype = PrototypeReport(transactions)
        nomenclatures = self.start_service.data.get(reposity.nomenclature_key(), [])
        if len(nomenclatures) == 0:
            raise operation_exception("Список номенклатуры пуст!")
        first_nomenclature = nomenclatures[0]

        # Действие: фильтр по конкретной номенклатуре
        next_prototype = PrototypeReport.filter_by_nomenclature(start_prototype, first_nomenclature)

        # Проверка
        self.assertTrue(len(next_prototype.data) > 0)
        self.assertTrue(len(start_prototype.data) > 0)
        self.assertGreaterEqual(len(start_prototype.data), len(next_prototype.data))

    def test_universal_filter(self):
        """Тест универсального фильтра"""
        # Подготовка: получаем номенклатуру
        nomenclatures = self.start_service.data.get(reposity.nomenclature_key(), [])
        start_prototype = PrototypeReport(nomenclatures)
        if len(nomenclatures) == 0:
            raise operation_exception("Список номенклатуры пуст!")

        first_nomenclature = nomenclatures[0]

        #сздаем DTO фильтра
        dto = filter_dto()
        dto.field_name = "name"
        dto.value = first_nomenclature.name
        dto.operator = FilterOperator.EQUALS

        #Действие: универсальный фильтр
        next_prototype = start_prototype.filter(dto)

        #Проверка: результат должен содержать хотя бы один элемент
        self.assertGreaterEqual(len(next_prototype.data), 1)

    def test_like_operator(self):
        """Тест оператора LIKE"""
        nomenclatures = self.start_service.data.get(reposity.nomenclature_key(), [])
        start_prototype = PrototypeReport(nomenclatures)
        dto = filter_dto()
        dto.field_name = "name"
        dto.value = "мука"
        dto.operator = FilterOperator.LIKE
        result = start_prototype.filter(dto)

        #проверяем
        self.assertTrue(len(result.data) > 0)
        for item in result.data:
            self.assertIn("мука", item.name.lower())
    def test_multiple_filters(self):
        """Тест цепочки фильтров"""
        nomenclatures = self.start_service.data.get(reposity.nomenclature_key(), [])
        start_prototype = PrototypeReport(nomenclatures)

        #LIKE "а"
        filter1 = filter_dto()
        filter1.field_name = "name"
        filter1.value = "а"
        filter1.operator = FilterOperator.LIKE

        #NOT_EQUALS "Сахар"
        filter2 = filter_dto()
        filter2.field_name = "name"
        filter2.value = "Сахар"
        filter2.operator = FilterOperator.NOT_EQUALS
        result = start_prototype.filter(filter1).filter(filter2)

        self.assertTrue(len(result.data) > 0)
        for item in result.data:
            self.assertIn("а", item.name.lower())
            self.assertNotEqual("Сахар", item.name)

    def test_nested_field_filter(self):
        """Тест фильтрации по вложенным полям"""
        nomenclatures = self.start_service.data.get(reposity.nomenclature_key(), [])
        start_prototype = PrototypeReport(nomenclatures)

        #фильтр по вложенному полю range.name
        dto = filter_dto()
        dto.field_name = "range.name"
        dto.value = "Киллограмм"
        dto.operator = FilterOperator.EQUALS
        result = start_prototype.filter(dto)
        if len(result.data) > 0:
            for item in result.data:
                if hasattr(item, 'range') and item.range:
                    self.assertEqual(item.range.name, "Киллограмм")

    def test_empty_filter_result(self):
        """Тест фильтра с пустым результатом"""
        nomenclatures = self.start_service.data.get(reposity.nomenclature_key(), [])
        start_prototype = PrototypeReport(nomenclatures)

        #фильтр с несуществующим значением
        dto = filter_dto()
        dto.field_name = "name"
        dto.value = "НесущОбъ123"
        dto.operator = FilterOperator.EQUALS
        result = start_prototype.filter(dto)
        self.assertEqual(len(result.data), 0)

    def test_range_filter(self):
        """Тест фильтрации единиц измерения"""
        ranges = self.start_service.data.get(reposity.range_key(), [])
        start_prototype = PrototypeReport(ranges)
        dto = filter_dto()
        dto.field_name = "name"
        dto.value = "Грамм"
        dto.operator = FilterOperator.EQUALS
        result = start_prototype.filter(dto)

        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0].name, "Грамм")

if __name__ == "__main__":
    unittest.main(verbosity=2)