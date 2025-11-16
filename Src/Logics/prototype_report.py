from Src.Logics.prototype import Prototype
from Src.Models.nomenclature_model import nomenclature_model
from Src.Core.validator import validator
from Src.Dtos.filter_dto import filter_dto

class PrototypeReport(Prototype):
    def __init__(self, items):
        super().__init__(items)

    @staticmethod
    def filter_by_nomenclature(source: Prototype, nomenclature: nomenclature_model) -> Prototype:
        validator.validate(source, Prototype)
        validator.validate(nomenclature, nomenclature_model)
        result = [item for item in source.data if hasattr(item, 'nomenclature') and item.nomenclature == nomenclature]
        return source.clone(result)

    def filter(self, filter_obj: filter_dto) -> "PrototypeReport":
        validator.validate(filter_obj, filter_dto)
        filtered_prototype = super().filter(filter_obj)
        return PrototypeReport(filtered_prototype.data)