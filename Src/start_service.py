from Src.reposity import reposity
from Src.Models.range_model import range_model
from Src.Models.group_model import group_model
from Src.Models.nomenclature_model import nomenclature_model
from Src.Core.validator import validator, argument_exception, operation_exception
import os
import json
from datetime import datetime
from Src.Models.receipt_model import receipt_model
from Src.Models.receipt_item_model import receipt_item_model
from Src.Dtos.nomenclature_dto import nomenclature_dto
from Src.Dtos.range_dto import range_dto
from Src.Dtos.category_dto import category_dto
from Src.Dtos.storage_dto import storage_dto
from Src.Models.storage_model import storage_model
from Src.Models.transaction_model import transaction_model
from Src.Dtos.transaction_dto import transaction_dto
from Src.Models.osv_model import osv_model
from Src.Logics.prototype_report import PrototypeReport
from Src.Models.osv_model import osv_model
from Src.Dtos.filter_dto import filter_dto, FilterOperator
from Src.settings_manager import settings_manager

class start_service:
    # Репозиторий
    __repo: reposity = reposity()

    # Рецепт по умолчанию
    __default_receipt: receipt_model

    # Словарь который содержит загруженные и инициализованные инстансы нужных объектов
    # Ключ - id записи, значение - abstract_model
    __cache = {}
    _cached_turnover_before_block: osv_model = None
    _cached_block_date: datetime = None
    # Наименование файла (полный путь)
    __full_file_name:str = ""

    # Описание ошибки
    __error_message:str = ""

    def __init__(self):
        self.__repo.initalize()
        self.load_settings()

    # Singletone
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(start_service, cls).__new__(cls)
        return cls.instance

    # Текущий файл
    @property
    def file_name(self) -> str:
        return self.__full_file_name

    # Полный путь к файлу настроек
    @file_name.setter
    def file_name(self, value:str):
        validator.validate(value, str)
        full_file_name = os.path.abspath(value)
        if os.path.exists(full_file_name):
            self.__full_file_name = full_file_name.strip()
        else:
            raise argument_exception(f'Не найден файл настроек {full_file_name}')

    # Информация об ошибке
    @property
    def error_message(self) -> str:
        return self.__error_message


    # Загрузить настройки из Json файла
    def load(self) -> bool:
        if self.__full_file_name == "":
            raise operation_exception("Не найден файл настроек!")

        try:
            with open(self.__full_file_name, 'r', encoding='utf-8') as file_instance:
                settings = json.load(file_instance)
                return self.convert(settings)
        except Exception as e:
            self.__error_message = str(e)
            return False

    # Сохранить элемент в репозитории
    def __save_item(self, key:str, dto, item):
        validator.validate(key, str)
        item.unique_code = dto.id
        self.__cache.setdefault(dto.id, item)
        self.__repo.data[ key ].append(item)

    def calculate_balances(self, target_date: str):
        """
        Рассчитать остатки на заданную дату с учетом даты блокировки
        """
        validator.validate(target_date, str)
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        #получаем дату блокировки
        block_period_str = self.__repo.settings.block_period if hasattr(self.__repo.settings,
                                                                        'block_period') else "1900-01-01"
        block_dt = datetime.strptime(block_period_str, "%Y-%m-%d")

        # берем сохраненные обороты до даты блокировки
        if "turnover_until_block" in self.__cache:
            osv_before_block = self.__cache["turnover_until_block"]
        else:
            osv_before_block = self.calculate_turnover_until_block()

        # берем транзакции после даты блокировки до target_date
        transactions = self.__repo.data.get(reposity.transaction_key(), [])
        # Фильтрация транзакций через PrototypeReport
        report = PrototypeReport(transactions)

        filter_from = filter_dto.create_more_filter("period", block_dt)
        filter_to = filter_dto.create_less_filter("period", target_dt)

        transactions_after_block = (
            report
                .filter(filter_from)
                .filter(filter_to)
                .data
        )
        osv_after_block = osv_model()
        nomenclatures = self.__repo.data.get(reposity.nomenclature_key(), [])
        osv_after_block.fill_empty_osv(nomenclatures)
        osv_after_block.fill_rows(transactions_after_block)

        #объединяем строки ОСВ до блокировки и после блокировки
        combined_osv = osv_model()
        combined_osv.fill_empty_osv(nomenclatures)

        #используем словарь для группировки по номенклатуре
        temp_dict = {}
        for item in osv_before_block.osv_items + osv_after_block.osv_items:
            key = item.nomenclature.unique_code
            if key not in temp_dict:
                temp_dict[key] = item
            else:
                temp_dict[key].start_num += item.start_num
                temp_dict[key].end_num += item.end_num

        combined_osv.osv_items = list(temp_dict.values())
        return combined_osv

    def calculate_turnover_until_block(self):
        block_date_str = self.__repo.settings.block_period if hasattr(self.__repo.settings,
                                                                      'block_period') else "1900-01-01"
        block_date = datetime.strptime(block_date_str, "%Y-%m-%d")
        if self._cached_block_date and block_date > self._cached_block_date:
            all_transactions = self.__repo.data.get(reposity.transaction_key(), [])
            new_transactions = [
                t for t in all_transactions
                if self._cached_block_date < t.period <= block_date
            ]
            self._cached_turnover_before_block.fill_rows(new_transactions)
            self._cached_block_date = block_date
            return self._cached_turnover_before_block

        #дата блокировки сдвинута влево
        all_transactions = self.__repo.data.get(reposity.transaction_key(), [])
        turnover_osv = osv_model()
        nomenclatures = self.__repo.data.get(reposity.nomenclature_key(), [])
        turnover_osv.fill_empty_osv(nomenclatures)

        transactions_before_block = [
            t for t in all_transactions if t.period <= block_date
        ]
        turnover_osv.fill_rows(transactions_before_block)
        self._cached_turnover_before_block = turnover_osv
        self._cached_block_date = block_date

        return turnover_osv

    # Загрузить единицы измерений
    def __convert_ranges(self, data: dict) -> bool:
        validator.validate(data, dict)
        ranges = data['ranges'] if 'ranges' in data else []
        if len(ranges) == 0:
            return False

        for range in ranges:
            dto = range_dto().create(range)
            item = range_model.from_dto(dto, self.__cache)
            self.__save_item( reposity.range_key(), dto, item )

        return True

    # Загрузить группы номенклатуры
    def __convert_groups(self, data: dict) -> bool:
        validator.validate(data, dict)
        categories =  data['categories'] if 'categories' in data else []
        if len(categories) == 0:
            return False

        for category in  categories:
            dto = category_dto().create(category)
            item = group_model.from_dto(dto, self.__cache )
            self.__save_item( reposity.group_key(), dto, item )

        return True

    # Загрузить склады
    def __convert_storages(self, data:dict) -> bool:
        validator.validate(data, dict)
        storages = data['storages'] if 'storages' in data else []
        if len(storages) == 0:
            return False

        for storage in storages:
            dto = storage_dto().create(storage)
            item = storage_model.from_dto(dto, self.__cache )
            self.__save_item( reposity.storage_key(), dto, item )

        return True

    # Загрузить тестовые транзакции
    def __convert_transactions(self, data:list) -> bool:
        validator.validate(data, list)
        if len(data) == 0:
            return False

        for transaction in data:
            dto = transaction_dto().create(transaction)
            item = transaction_model.from_dto(dto, self.__cache )
            self.__save_item( reposity.transaction_key(), dto, item )

        return True

    # Загрузить номенклатуру
    def __convert_nomenclatures(   self, data: dict) -> bool:
        validator.validate(data, dict)
        nomenclatures = data['nomenclatures'] if 'nomenclatures' in data else []
        if len(nomenclatures) == 0:
            return False

        for nomenclature in nomenclatures:
            dto = nomenclature_dto().create(nomenclature)
            item = nomenclature_model.from_dto(dto, self.__cache)
            self.__save_item( reposity.nomenclature_key(), dto, item )

        return True

    # Обработать справочники
    def __convert_references(self, data:dict) -> bool:
        validator.validate(data, dict)

        try:
            self.__convert_ranges(data)
            self.__convert_groups(data)
            self.__convert_nomenclatures(data)
            self.__convert_storages(data)
            return True
        except Exception as e:
            self.__error_message = str(e)
            return False

    # Обработать рецепт по умолчанию
    def __convert_receipt(self, data:dict) -> bool:
        validator.validate(data, dict)

        try:
            # 1 Созданим рецепт
            cooking_time = data['cooking_time'] if 'cooking_time' in data else ""
            portions = int(data['portions']) if 'portions' in data else 0
            name =  data['name'] if 'name' in data else "НЕ ИЗВЕСТНО"
            self.__default_receipt = receipt_model.create(name, cooking_time, portions  )

            # Загрузим шаги приготовления
            steps =  data['steps'] if 'steps' in data else []
            for step in steps:
                if step.strip() != "":
                    self.__default_receipt.steps.append( step )

            # Собираем рецепт
            compositions =  data['composition'] if 'composition' in data else []
            for composition in compositions:
                # TODO: Заменить код через Dto
                namnomenclature_id = composition['nomenclature_id'] if 'nomenclature_id' in composition else ""
                range_id = composition['range_id'] if 'range_id' in composition else ""
                value  = composition['value'] if 'value' in composition else ""
                nomenclature = self.__cache[namnomenclature_id] if namnomenclature_id in self.__cache else None
                range = self.__cache[range_id] if range_id in self.__cache else None
                item = receipt_item_model.create(  nomenclature, range, value)
                self.__default_receipt.composition.append(item)

            # Сохраняем рецепт
            self.__repo.data[ reposity.receipt_key() ].append(self.__default_receipt)
            return True
        except Exception as e:
            self.__error_message = str(e)
            return False


    # Обработать полученный словарь
    def convert(self, data: dict) -> bool:
        validator.validate(data, dict)
        loaded_references = True
        loaded_receipt = True
        loaded_transactions = True

        # Обработать справочники
        if "default_refenences" in data.keys():
                default_refenences = data["default_refenences"]
                loaded_references = self.__convert_references(default_refenences)

        # Обработать рецепт
        if "default_receipt" in data.keys():
                default_receipt = data["default_receipt"]
                loaded_receipt = self.__convert_receipt(default_receipt)

        # Загрузить транзакции
        if "default_transactions" in data.keys():
                default_transactions = data["default_transactions"]
                loaded_transactions = self.__convert_transactions(default_transactions)

        return loaded_references and loaded_receipt and loaded_transactions

    """
    Стартовый набор данных
    """
    @property
    def data(self):
        return self.__repo.data

    """
    Основной метод для генерации эталонных данных
    """

    def load_settings(self):
        settings = settings_manager()
        settings.file_name = "settings.json"
        if not settings.load():
            raise operation_exception("Ошибка загрузки настроек.")
        self.__repo.settings = settings.settings

    """
    Создание ОСВ
    """
    def create_osv(self, start, end, storage_id):
        transactions = self.__repo.data.get(reposity.transaction_key(), [])
        nomenclatures = self.__repo.data.get(reposity.nomenclature_key(), [])
        storage = self.__cache.get(storage_id, None)
        validator.validate(storage, storage_model)
        osv_instance = osv_model()
        osv_instance.storage = storage
        osv_instance.start_date = start
        osv_instance.end_date = end
        osv_instance.fill_empty_osv(nomenclatures)

        #заполняем строки ОСВ всеми транзакциями
        osv_instance.fill_rows(transactions)
        return osv_instance

    """
    Создание ОСВ с использованием фильтров DTO
    """
    def create_osv_with_filters(self, filters: list):
        """
        filters: список объектов filter_dto
        """
        transactions = self.__repo.data.get(reposity.transaction_key(), [])
        nomenclatures = self.__repo.data.get(reposity.nomenclature_key(), [])
        #создаем пустую модель ОСВ
        osv_instance = osv_model()
        osv_instance.fill_empty_osv(nomenclatures)
        #фильтруем транзакции через PrototypeReport
        prot = PrototypeReport(transactions)
        for f in filters:
            prot = prot.filter(f)
        #заполняем
        osv_instance.fill_rows(prot.data)

        return osv_instance


def save_osv_to_file(self, osv_instance, file_path: str):
    """
    Сохраняет объект osv_model
    """
    osv_data = []
    for item in osv_instance.osv_items:
        osv_data.append({
            "nomenclature": item.nomenclature.name if item.nomenclature else "",
            "nomenclature_id": item.nomenclature.unique_code if item.nomenclature else "",
            "start_num": item.start_num,
            "end_num": item.end_num,
            "range": item.range.name if item.range else "",
            "range_id": item.range.unique_code if item.range else "",
        })

    result = {
        "storage": osv_instance.storage.name if osv_instance.storage else "",
        "storage_id": osv_instance.storage.unique_code if osv_instance.storage else "",
        "start_date": osv_instance.start_date.strftime("%Y-%m-%d") if osv_instance.start_date else "",
        "end_date": osv_instance.end_date.strftime("%Y-%m-%d") if osv_instance.end_date else "",
        "osv_items": osv_data
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

