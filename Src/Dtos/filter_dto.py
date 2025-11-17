from Src.Core.abstract_dto import abstract_dto
from Src.Core.validator import argument_exception, validator
from enum import Enum

#операторы фильтрации
class FilterOperator(Enum):
    EQUALS = "EQUALS"
    LIKE = "LIKE"
    LESS = "LESS"
    MORE = "MORE"
    NOT_EQUALS = "NOT_EQUALS"

class filter_dto(abstract_dto):
    def __init__(self):
        self.__field_name: str = ""
        self.__value = None
        self.__operator: FilterOperator = FilterOperator.EQUALS

    #Название поля
    @property
    def field_name(self):
        return self.__field_name
    @field_name.setter
    def field_name(self, value):
        validator.validate(value, str)
        self.__field_name = value.strip()

    #значение поля
    @property
    def value(self):
        return self.__value
    @value.setter
    def value(self, value):
        self.__value = value

    #оператор фильтрации
    @property
    def operator(self):
        return self.__operator
    @operator.setter
    def operator(self, value):
        if isinstance(value, FilterOperator):
            self.__operator = value
        elif isinstance(value, str):
            try:
                self.__operator = FilterOperator[value.upper()]
            except KeyError:
                raise argument_exception(f"неверный оператор фильтрации: {value}")
        else:
            raise argument_exception(f"оператор фильтрации должен быть FilterOperator или str")

    #функция сравнения по оператору
    def get_operator_function(self):
        mapping = {
            FilterOperator.EQUALS: lambda x, y: str(x) == str(y),
            FilterOperator.LIKE: lambda x, y: str(y) in str(x),
            FilterOperator.LESS: lambda x, y: float(x) <= float(y),
            FilterOperator.MORE: lambda x, y: float(x) >= float(y),
            FilterOperator.NOT_EQUALS: lambda x, y: str(x) != str(y),
        }
        return mapping[self.__operator]

    # Фабричные методы для создания фильтров
    @staticmethod
    def create_equals_filter(field_name: str, value) -> "filter_dto":
        """Создать фильтр полного совпадения"""
        filter_obj = filter_dto()
        filter_obj.field_name = field_name
        filter_obj.value = value
        filter_obj.operator = FilterOperator.EQUALS
        return filter_obj

    @staticmethod
    def create_like_filter(field_name: str, value: str) -> "filter_dto":
        """Создать фильтр вхождения строки"""
        filter_obj = filter_dto()
        filter_obj.field_name = field_name
        filter_obj.value = value
        filter_obj.operator = FilterOperator.LIKE
        return filter_obj

    @staticmethod
    def create_less_filter(field_name: str, value) -> "filter_dto":
        """Создать фильтр 'меньше или равно'"""
        filter_obj = filter_dto()
        filter_obj.field_name = field_name
        filter_obj.value = value
        filter_obj.operator = FilterOperator.LESS
        return filter_obj

    @staticmethod
    def create_more_filter(field_name: str, value) -> "filter_dto":
        """Создать фильтр 'больше или равно'"""
        filter_obj = filter_dto()
        filter_obj.field_name = field_name
        filter_obj.value = value
        filter_obj.operator = FilterOperator.MORE
        return filter_obj

    @staticmethod
    def create_not_equals_filter(field_name: str, value) -> "filter_dto":
        """Создать фильтр 'не равно'"""
        filter_obj = filter_dto()
        filter_obj.field_name = field_name
        filter_obj.value = value
        filter_obj.operator = FilterOperator.NOT_EQUALS
        return filter_obj

    @staticmethod
    def create_from_dict(data: dict) -> "filter_dto":
        """Фабричный метод для создания DTO из словаря"""
        filter_obj = filter_dto()
        if "field_name" in data:
            filter_obj.field_name = data["field_name"]

        #значение с преобразованием типов
        if "value" in data:
            value = data["value"]
            if isinstance(value, str):
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
            filter_obj.value = value
        #устанавливаем оператор
        if "operator" in data:
            filter_obj.operator = data["operator"]
        return filter_obj