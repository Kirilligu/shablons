import unittest
from datetime import datetime
from Src.start_service import start_service
from Src.Models.transaction_model import transaction_model
from Src.Models.range_model import range_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.storage_model import storage_model

class TestBalancesWithBlockDate(unittest.TestCase):
    """
    Тестовый класс для проверки корректности расчета остатков с учетом даты блокировки
    Методы:
        1.test_balances_stability_with_block_date_change: проверяет, что конечные остатки не меняются
          при изменении даты блокировки
        2.test_combined_turnover_calculation: проверяет правильность объединения оборотов до и после
          даты блокировки, и что все номенклатуры присутствуют в расчете
    """
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.service = start_service()
        self.service.start()

        #тестовая дата блокировки
        self.service._start_service__repo.settings.block_period = "2024-01-01"

    def test_balances_stability_with_block_date_change(self):
        """
        Проверяем, что при изменении даты блокировки конечный результат не меняется
        """
        target_date = "2024-10-01"
        #рассчитываем остатки с текущей датой
        balances_1 = self.service.calculate_balances(target_date)
        result_1 = {item.nomenclature.name: item.end_num for item in balances_1.osv_items}

        #меняем дату блокировки на более раннюю
        self.service._start_service__repo.settings.block_period = "2023-06-01"
        balances_2 = self.service.calculate_balances(target_date)
        result_2 = {item.nomenclature.name: item.end_num for item in balances_2.osv_items}
        #проверяем,что конечные остатки одинаковые
        self.assertEqual(result_1, result_2, "Остатки должны быть одинаковыми при изменении даты блокировки")

    def test_combined_turnover_calculation(self):
        """
        Проверка объединения оборотов до и после даты блокировки
        """
        target_date = "2025-01-15"
        balances = self.service.calculate_balances(target_date)
        # Проверяем что номенклатуры присутствуют
        nomenclatures = [n.name for n in self.service._start_service__repo.data.get("nomenclature_model", [])]
        balance_names = [b.nomenclature.name for b in balances.osv_items]
        for name in nomenclatures:
            self.assertIn(name, balance_names, f"{name} отсутствует в остатках")

if __name__ == "__main__":
    unittest.main()
