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
    for rf in raw_filters:
        f = filter_dto()
        f.field_name = rf.get("field_name")
        value = rf.get("value")

        #преобразование типов
        if isinstance(value, str) and value.isdigit():
            value = float(value)
        f.value = value

        #преобразуем строку к Enum
        try:
            f.operator = FilterOperator[rf.get("operator").upper()]
        except KeyError:
            return Response(f"Неверный оператор фильтра: {rf.get('operator')}", status=400)
        filters.append(f)
    if data_type not in service.data:
        return Response(f"Неправильный тип данных: {data_type}", status=400, content_type="text/plain;charset=utf-8")

    data_list = service.data[data_type]
    prot = PrototypeReport(data_list)
    for f in filters:
        prot = prot.filter(f)

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
    for rf in raw_filters:
        f = filter_dto()
        f.field_name = rf.get("field_name")
        value = rf.get("value")

        #обработка дат
        if "date" in f.field_name.lower():
            from datetime import datetime
            value = datetime.strptime(value, "%d-%m-%Y")
        f.value = value

        try:
            f.operator = FilterOperator[rf.get("operator").upper()]
        except KeyError:
            return Response(f"Неверный оператор фильтра: {rf.get('operator')}", status=400)
        filters.append(f)
    osv = service.create_osv_with_filters(filters)
    csv_lines = [f"{item.nomenclature.name}: {item.start_num} -> {item.end_num}" for item in osv.osv_items]
    return Response("\n".join(csv_lines), status=200, content_type="text/plain;charset=utf-8")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)