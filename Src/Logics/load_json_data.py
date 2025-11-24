
from Src.start_service import start_service

service = start_service()
service.file_name = "settings.json"
service.load()  # автоматически загружаем справочники,номенклатуру,склады,транзакции и рецепт

# доступ к данным через сервис
storages = service.data.get("storages", [])
nomenclatures = service.data.get("nomenclatures", [])
transactions = service.data.get(service._start_service__repo.transaction_key(), [])

print(f"Данные успешно загружены: {len(storages)} складов, "
      f"{len(nomenclatures)} номенклатур, {len(transactions)} транзакций")