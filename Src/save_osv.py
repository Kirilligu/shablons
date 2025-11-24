from Src.start_service import start_service
MD_FILE = "osv_result.md"
service = start_service()
service.file_name = "settings.json"
service.load()
combined_osv = service.calculate_balances("2025-11-24")

#Markdown
def save_osv_to_markdown(osv, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("| Единица | Наименование | Склад | Код | Остаток |\n")
        f.write("|---------|-------------|-------|-----|---------|\n")
        for item in osv.osv_items:
            unit_name = item.range.name if item.range else "—"
            nom_name = item.nomenclature.name
            storage_name = item.storage.name if item.storage else "—"
            code = item.nomenclature.id
            end_num = item.end_num
            f.write(f"| {unit_name} | {nom_name} | {storage_name} | {code} | {end_num} |\n")
save_osv_to_markdown(combined_osv, MD_FILE)

print(f"файл сохранён в {MD_FILE}")
