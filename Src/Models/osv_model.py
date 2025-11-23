from datetime import datetime
from Src.Models.transaction_model import transaction_model
from Src.Models.storage_model import storage_model
from Src.Dtos.osv_dto import osv_dto, osv_item_dto
from Src.Core.validator import validator, argument_exception
from Src.Logics.prototype_report import PrototypeReport
from Src.Dtos.filter_dto import filter_dto

#модель элемента ОСВ
class osv_item_model:
    def __init__(self, nomenclature, range, start_num=0.0, addition=0.0, substraction=0.0, end_num=0.0):
        self.nomenclature = nomenclature
        self.range = range
        self.start_num = start_num
        self.addition = addition
        self.substraction = substraction
        self.end_num = end_num

    @staticmethod
    def create(nomenclature, range, start_num=0.0, addition=0.0, substraction=0.0, end_num=0.0):
        return osv_item_model(nomenclature, range, start_num, addition, substraction, end_num)
    def to_dto(self):
        dto = osv_item_dto()
        dto.nomenclature_name = self.nomenclature.name
        dto.start_num = self.start_num
        dto.addition = self.addition
        dto.substraction = self.substraction
        dto.end_num = self.end_num
        return dto

#основная модель ОСВ
class osv_model:
    def __init__(self):
        self.storage: storage_model = None
        self.start_date: datetime = None
        self.end_date: datetime = None
        self.osv_items: list[osv_item_model] = []

    def fill_empty_osv(self, nomenclatures: list):
        """Создание пустых элементов ОСВ по номенклатуре"""
        self.osv_items = [
            osv_item_model.create(nomenclature, getattr(nomenclature, "range_count", None))
            for nomenclature in nomenclatures
        ]

    def fill_rows(self, transactions: list):
        """Заполнение ОСВ на основе списка транзакций"""
        validator.validate(transactions, list)

        #фильтруем по складу
        storage_filter = filter_dto.create_equals_filter("storage.id", self.storage.id)
        prot = PrototypeReport(transactions).filter(storage_filter)

        #фильтруем по дате
        start_filter = filter_dto.create_less_filter("date", self.start_date)
        end_filter = filter_dto.create_more_filter("date", self.end_date)
        start_prot = prot.filter(start_filter)
        end_prot = prot.filter(end_filter)

        #подсчёт ОСВ по номенклатуре
        for item in self.osv_items:
            nom_filter = filter_dto.create_equals_filter("nomenclature.name", item.nomenclature.name)

            #остатки
            start_items = start_prot.filter(nom_filter)
            for tr in start_items.data:
                num = tr.value
                if hasattr(tr, "range") and tr.range and tr.range.base_range == item.range:
                    num *= tr.range.coeff if hasattr(tr.range, "coeff") else 1
                item.start_num += num

            #добавления и списания
            end_items = end_prot.filter(nom_filter)
            for tr in end_items.data:
                if tr in start_items.data:
                    continue
                num = tr.value
                if hasattr(tr, "range") and tr.range and tr.range.base_range == item.range:
                    num *= tr.range.coeff if hasattr(tr.range, "coeff") else 1
                if num > 0:
                    item.addition += num
                else:
                    item.substraction += abs(num)
                item.end_num = item.start_num + item.addition - item.substraction

    @staticmethod
    def create(storage: storage_model, start_date: datetime, end_date: datetime, nomenclatures: list):
        validator.validate(storage, storage_model)
        osv = osv_model()
        osv.storage = storage
        osv.start_date = start_date
        osv.end_date = end_date
        osv.fill_empty_osv(nomenclatures)
        return osv

    @staticmethod
    def filters_osv(filters: list[filter_dto], transactions: list, nomenclatures: list):
        """Создание ОСВ с фильтрацией"""
        osv = osv_model()
        osv.fill_empty_osv(nomenclatures)
        prot = PrototypeReport(transactions)
        for f in filters:
            prot = prot.filter(f)
        osv.fill_rows(prot.data)
        return osv

    def to_dto(self):
        dto = osv_dto()
        dto.osv_items = [item.to_dto() for item in self.osv_items]
        dto.start_date = self.start_date
        dto.end_date = self.end_date
        dto.storage_id = self.storage.id
        return dto
