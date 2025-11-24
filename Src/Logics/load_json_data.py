import json
from datetime import datetime
from Src.Models.storage_model import storage_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Models.range_model import range_model
from Src.Models.transaction_model import transaction_model
from Src.start_service import start_service
service = start_service()
with open("../patterns2025/Src/settings.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Загружаем диапазоны
service.ranges_cache = {}
for r in data["default_refenences"]["ranges"]:
    range_obj = range_model()
    range_obj.name = r["name"]
    range_obj.unique_code = r["id"]
    range_obj.base_id = r.get("base_id")
    range_obj.value = r["value"]
    service.ranges_cache[r["id"]] = range_obj

#Загружаем склады
service.storages_cache = {}
for s in data["default_refenences"]["storages"]:
    storage_obj = storage_model()
    storage_obj.name = s["name"]
    storage_obj.unique_code = s["id"]
    storage_obj.address = s.get("address", "")
    service.storages_cache[s["id"]] = storage_obj
# Загружаем номенклатуры
service.nomenclature_cache = {}
for n in data["default_refenences"]["nomenclatures"]:
    nom_obj = nomenclature_model()
    nom_obj.name = n["name"]
    nom_obj.unique_code = n["id"]
    nom_obj.range = service.ranges_cache[n["range_id"]]
    service.nomenclature_cache[n["id"]] = nom_obj

#Загружаем транзакции
service._start_service__repo.initalize()
transactions = []

for t in data["default_transactions"]:
    tr = transaction_model()
    tr.unique_code = t["id"]
    tr.storage = service.storages_cache[t["storage_id"]]          # объект склада
    tr.nomenclature = service.nomenclature_cache[t["nomenclature_id"]]  # объект номенклатуры
    tr.range = service.ranges_cache[t["range_id"]]                # объект диапазона
    tr.value = t["value"]
    tr.period = datetime.strptime(t["period"], "%Y-%m-%d")
    transactions.append(tr)
service.data["storages"] = list(service.storages_cache.values())
service.data["nomenclatures"] = list(service.nomenclature_cache.values())
service._start_service__repo.data[service._start_service__repo.transaction_key()] = transactions

print(f"Данные успешно загружены: {len(service.storages_cache)} складов, "
      f"{len(service.nomenclature_cache)} номенклатур, {len(transactions)} транзакций")
