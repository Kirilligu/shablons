#DTO для отдельной строки ОСВ
class osv_item_dto:
    def __init__(self):
        self.nomenclature_name = ""
        self.start_num = 0.0
        self.addition = 0.0
        self.substraction = 0.0
        self.end_num = 0.0

#DTO для всей модели ОСВ
class osv_dto:
    def __init__(self):
        self.osv_items = []
        self.start_date = None
        self.end_date = None
        self.storage_id = ""
