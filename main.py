import connexion
from flask import request, Response
from Src.start_service import start_service
from Src.Logics.prototype_report import PrototypeReport
from Src.Dtos.filter_dto import filter_dto, FilterOperator
from flask import request, Response
from Src.Models.settings_model import settings_model
from Src.start_service import start_service
from Src.Logics.load_json_data import service
app = connexion.FlaskApp(__name__)
settings = settings_model()



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

# GET запрос даты блокировки
@app.route("/api/block_period", methods=['GET'])
def get_block_period():
    return {"block_period": settings.block_period}
# POST запрос для изменения даты блокировки
@app.route("/api/block_period", methods=['POST'])
def set_block_period():
    payload = request.get_json()
    if not payload or "block_period" not in payload:
        return Response("Отсутствует поле 'block_period'!", status=400,
                        content_type="text/plain;charset=utf-8")
    try:
        settings.block_period = payload["block_period"]
        return {"block_period": settings.block_period}
    except Exception as e:
        return Response(f"Ошибка установки даты блокировки: {str(e)}", status=400,
                        content_type="text/plain;charset=utf-8")
# GET запрос для остатков на указанную дату
@app.route("/api/balance", methods=['GET'])
def get_balance():
    from flask import request
    from datetime import datetime
    # Получаем параметры запроса
    date_str = request.args.get("date")
    storage_code = request.args.get("storage")

    if not date_str:
        return Response("Отсутствует параметр 'date'!", status=400,
                        content_type="text/plain;charset=utf-8")
    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return Response("Неверный формат даты! Используйте YYYY-MM-DD", status=400,
                        content_type="text/plain;charset=utf-8")

    try:
        #если склад не указан, берём любой или все
        if storage_code:
            osv = service.create_osv(settings.block_period, query_date, storage_code)
        else:
            balances = []
            for s in service._start_service__cache.values():
                if hasattr(s, "unique_code"):  # фильтруем склады
                    osv_instance = service.create_osv(settings.block_period, query_date, s.unique_code)
                    balances.extend(osv_instance.osv_items)
            osv = type('osv_dummy', (), {"osv_items": balances})()  # создаём временный объект

        #ответ
        response_data = [
            {
                "nomenclature": item.nomenclature.name,
                "storage": item.storage.name,
                "start_num": item.start_num,
                "end_num": item.end_num
            }
            for item in osv.osv_items
        ]

        return {"date": date_str, "balances": response_data}

    except Exception as e:
        return Response(f"Ошибка расчёта остатков: {str(e)}", status=400,
                        content_type="text/plain;charset=utf-8")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)