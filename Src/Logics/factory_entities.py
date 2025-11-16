from Src.Core.abstract_response import abstract_response
from Src.Logics.response_csv import response_scv
from Src.Core.validator import operation_exception
from Src.Core.response_formats import response_formats
from Src.Logics.response_markdown import response_markdown

"""
Фабрика для формирования различных ответов
"""
class factory_entities:

    # Сопоставление
    __match = {
       response_formats.csv():  response_scv,
       response_formats.markdown():  response_markdown
    }

    # Получить нужный тип
    def create(self, format:str) -> abstract_response:
        if format not in self.__match.keys():
            raise operation_exception("Формат не верный")
        
        return self.__match[  format ]

