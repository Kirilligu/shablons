from Src.start_service import start_service
from Src.Logics.markdown_response import markdown_response
from Src.reposity import reposity
from Src.Logics.response_markdown import response_markdown
import unittest

# Набор тестов для проверки формирования данных
# в разных форматах
class test_responses(unittest.TestCase):

    # Проверить формирование Markdown 
    def test_response_markdown_build(self):
        # Подготовка
        service = start_service()
        service.start()
        response = response_markdown()
        data = service.data[ reposity.nomenclature_key() ]


        # Действие
        result = response.build( data )

        # Проверка
        assert len(result) > 0
        print(result)

  
if __name__ == '__main__':
    unittest.main()  