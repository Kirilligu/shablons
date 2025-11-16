from Src.Dtos.filter_dto import filter_dto

class filter_sorting_dto:
    __filters = [] # filter_dto
    __sorting = [] # sttring


    {
        "filters":
        [
            {
                "field_name":"name",
                "value":"Пщеничная мука",
                "type":"LIKE"
            },

            {
                "field_name":"range_name",
                "value":"кг",
                "type":"EQUALS"
            }
        ],
        "sorting":[
            "range_name"
        ]
    }
