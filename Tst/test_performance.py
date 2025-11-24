import pytest
import random
from datetime import datetime, timedelta
import time
import uuid
from Src.Models.transaction_model import transaction_model
from Src.Models.range_model import range_model
from Src.Models.storage_model import storage_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.start_service import start_service

def generate_nomenclature(name="Товар"):
    n = nomenclature_model()
    n.name = name
    n.unique_code = str(uuid.uuid4())
    r = range_model.create("Штуки", 1, None)
    n.range = r
    return n

def generate_storage(name="Склад"):
    s = storage_model()
    s.name = name
    s.unique_code = str(uuid.uuid4())
    return s

def generate_transactions(nomenclature, storage, count=1000):
    transactions = []
    start_date = datetime(2024, 1, 1)
    for _ in range(count):
        t = transaction_model()
        t.unique_code = str(uuid.uuid4())
        t.nomenclature = nomenclature
        t.storage = storage
        t.range = nomenclature.range
        t.period = start_date + timedelta(days=random.randint(0, 365*2))
        t.value = round(random.uniform(-10, 50), 2)
        transactions.append(t)
    return transactions

# Нагрузочный тест

def test_performance_balances():
    service = start_service()
    nomenclature = generate_nomenclature()
    storage = generate_storage()
    transactions = generate_transactions(nomenclature, storage, count=2000)  #2000 транзакций
    # Инициализация репозитория и кэша
    service._start_service__repo.initalize()
    service._start_service__cache[nomenclature.unique_code] = nomenclature
    service._start_service__cache[storage.unique_code] = storage
    service._start_service__repo.data[service._start_service__repo.transaction_key()] = transactions
    # Даты блокировки для замеров
    block_dates = [
        datetime(2024, 1, 1),
        datetime(2024, 3, 1),
        datetime(2024, 6, 1),
        datetime(2024, 9, 1),
        datetime(2025, 1, 1)
    ]
    results = []

    for bd in block_dates:
        start_time = time.time()
        osv = service.create_osv(bd, datetime(2025, 12, 31), storage.unique_code)
        elapsed = time.time() - start_time
        print(f"Дата блокировки: {bd.strftime('%Y-%m-%d')}, Время расчета: {elapsed:.4f} сек")
        results.append((bd.strftime("%Y-%m-%d"), elapsed))

    #Markdown сохранение
    with open("performance_results.md", "w", encoding="utf-8") as f:
        f.write("| Дата блокировки | Время расчета (сек) |\n")
        f.write("|----------------|-------------------|\n")
        for bd, elapsed in results:
            f.write(f"| {bd} | {elapsed:.4f} |\n")
    assert len(results) == len(block_dates)
