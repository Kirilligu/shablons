from Src.Core.validator import validator, argument_exception
from Src.Dtos.filter_dto import filter_dto, FilterOperator
from abc import ABC
from Src.Core.common import common

class Prototype(ABC):
    def __init__(self, data: list):
        self.data = data  #валидируется в сеттере

    @property
    def data(self) -> list:
        return self.__data
    @data.setter
    def data(self, value: list):
        validator.validate(value, list)
        self.__data = value

    #клонирование прототипа
    def clone(self, data: list = None) -> "Prototype":
        new_data = data if data is not None else self.data
        return Prototype(new_data)

    #получение значения поля, включая вложенные поля
    def get_field_value(self, obj, field: str):
        parts = field.split(".")
        value = obj
        for part in parts:
            fields_list = common.get_fields(value)
            if part in fields_list:
                value = getattr(value, part)
            else:
                try:
                    value = getattr(value, part)
                except AttributeError:
                    raise argument_exception(f"Поле '{part}' отсутствует в объекте {type(value).__name__}")

        return value

    #универсальная фильтрация
    def filter(self, filter_obj: filter_dto) -> "Prototype":
        validator.validate(filter_obj, filter_dto)
        result = []
        for item in self.data:
            try:
                item_value = self.get_field_value(item, filter_obj.field_name)
                func = filter_obj.get_operator_function()
                #приводим типы для сравнения
                if isinstance(item_value, (int, float)) and isinstance(filter_obj.value, str):
                    try:
                        filter_value = float(filter_obj.value)
                    except ValueError:
                        filter_value = filter_obj.value
                else:
                    filter_value = filter_obj.value

                #преобразуем в строки для LIKE оператора
                if filter_obj.operator == FilterOperator.LIKE:
                    item_value = str(item_value)
                    filter_value = str(filter_value)
                if func(item_value, filter_value):
                    result.append(item)
            except Exception as e:
                continue
        return self.clone(result)