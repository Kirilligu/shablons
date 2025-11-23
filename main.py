import connexion
from flask import request, Response
from Src.start_service import start_service
from Src.Logics.prototype_report import PrototypeReport
from Src.Dtos.filter_dto import filter_dto, FilterOperator

app = connexion.FlaskApp(__name__)
service = start_service()


# Проверка доступности REST API
@app.route("/api/accessibility", methods=['GET'])
def check_api():
    return "SUCCESS"


# Фильтрация любых данных по DTO
@app.route("/api/info/<data_type>/<format>", methods=['POST'])
def filter_data(data_type, format):
    payload = request.get_json()
    if not payload:
        return Response("Отсутствует JSON!", status=400, content_type="text/plain;charset=utf-8")
    raw_filters = payload.get("filters")
    if not raw_filters:
        return Response("Отсутствуют фильтры!", status=400, content_type="text/plain;charset=utf-8")

    filters = []

    for filter_data in raw_filters:
        try:
            #используем фабричный метод
            filter_obj = filter_dto.create_from_dict(filter_data)
            filters.append(filter_obj)
        except Exception as e:
            return Response(f"Ошибка создания фильтра: {str(e)}", status=400)
    if data_type not in service.data:
        return Response(f"Неправильный тип данных: {data_type}", status=400, content_type="text/plain;charset=utf-8")

    data_list = service.data[data_type]
    prot = PrototypeReport(data_list)
    for filter_obj in filters:
        prot = prot.filter(filter_obj)
    #форматы ответа
    content_types = {
        "json": "application/json",
        "xml": "text/xml",
        "csv": "text/plain",
        "md": "text/plain"
    }

    return Response(str([str(item) for item in prot.data]), status=200,
                    content_type=content_types.get(format, "text/plain"))

@app.route("/api/report", methods=['POST'])
def filtered_report():
    payload = request.get_json()
    if not payload:
        return Response("Отсутствует JSON!", status=400, content_type="text/plain;charset=utf-8")

    raw_filters = payload.get("filters")
    if not raw_filters:
        return Response("Отсутствуют фильтры!", status=400, content_type="text/plain;charset=utf-8")
    filters = []
    for filter_data in raw_filters:
        try:
            #обработка дат перед созданием фильтра
            if "date" in filter_data.get("field_name", "").lower():
                from datetime import datetime
                filter_data["value"] = datetime.strptime(filter_data["value"], "%d-%m-%Y")

            #используем фабричный метод
            filter_obj = filter_dto.create_from_dict(filter_data)
            filters.append(filter_obj)
        except Exception as e:
            return Response(f"Ошибка создания фильтра: {str(e)}", status=400)
    osv = service.create_osv_with_filters(filters)
    csv_lines = [f"{item.nomenclature.name}: {item.start_num} -> {item.end_num}" for item in osv.osv_items]
    return Response("\n".join(csv_lines), status=200, content_type="text/plain;charset=utf-8")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)