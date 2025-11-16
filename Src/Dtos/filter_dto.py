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