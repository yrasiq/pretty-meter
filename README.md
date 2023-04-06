# pretty-meter
Проект сервиса для оценки того, насколько человек хорошо выглядит на фото от 0 до 10. Репозиторий включает набор инструментов для обучения моделей, inferenceService с REST api и frontend. Dataset и обученые модели здесь не представлены. Интерпретатор python 3.10.6

## [Frontend](/frontend)
Обычное React js UI приложение одностраничник. Сжимает фото и делает запрос к [inferenceService](/inferenceService)  
TODO: Вынести настройки и яндекс метрику куда-нибудь в отдельный файл

## [inferenceService](/inferenceService)
REST api к моделям на фреймворке FASTapi и тесты к данному сервису. Тесты не тестируют результаты предсказаний модели, а только корректность работы REST api сервиса.
  - [/.cfg](/.cfg) - файл конфигов сервиса
  - [Dockerfile.inferenceService-cpu](/Dockerfile.inferenceService-cpu) - докерфайл для сборки docker image. Вариант для работы на cpu, но сервис так же готов работать и на gpu, в случае работы в docker container нужно лишь подкорректировать Dockerfile и изменить настройку "device = gpu" в конфиге.
API спецификацию можно посмотреть стандартным способом для FASTapi "\<protocol\>://\<host\>:\<port\>/docs", либо просто в коде

## Обучение модели
### Dataset
Должен быть представлен в виде директории с файлами изображений. Лейблы должны содержаться в самом названии файла по шаблону:
  \<uuid\>\_\<gender\>\_\<country\>\_\<rate\>\_\<voices\>.\<extension\>  
На пример cdcbdbc019944d589e346a67d5431f89_w_unknown_8.7_100.png
- gender: "m" или "w"
- country: эти данные не используются, но должны быть указаны. Можно указать, на пример unknown
- rate: число с десятичной точностью от 0.0 до 10.0
- voices: положительное целое число, характеризующее достоверность оценки, на пример 100 означало бы, что это средняя оценка от 100 человек
### Препроцессинг данных
- [/scripts/removeDuplicates.py](/scripts/removeDuplicates.py): Удаляет дубликаты из Dataset директории "./dataset"  
TODO: Добавить аргумент командной строки "--ds" для возможности выбора директории
- [/scripts/load_df.py](/scripts/load_df.py): Скрипт загрузки датасета из директории (--ds аргумент) в parquet файл (--dst аргумент)
- [/scripts/add_faces_data.py](/scripts/add_faces_data.py): Добавляет в parquet файл столбец с данными по количеству лиц на переднем плане фото при помощи [insightface](https://github.com/deepinsight/insightface)
  - --ds: исходный parquet файл
  - --dst: путь к новому parquet файлу с результатом. Может совпадать с --ds для перезаписи исходного файла
- [/scripts/update_df_manual.py](/scripts/update_df_manual.py): Добавить новые данные из директории Dataset в существующий parquet файл. Количество лиц в новых данных будет указано 1
  - Включает аргументы из [/scripts/add_faces_data.py](/scripts/add_faces_data.py)
  - --transforming: если присутствует этот флаг - то изображения в результате будут трансформированы для оптимизации ресурсов во время обучения
- [/notebooks/normalize_data.ipynb](/notebooks/normalize_data.ipynb) нормализация данных с визуализацией различных показателей
  - Данные фильтруются по полу. Т.к. для каждого обучаются отдельные модели
  - Отсеиваются недостаточно достоверные данные по параметру voices
  - Оценки нормализуются в диапазон 0 - 1 по медиане
  - Оценкам проставляются веса, в зависимости от представленности в наборе данных согласно LDS подходу. [Источник](https://github.com/YyzHarry/imbalanced-regression)
  - Результат сохраняется в новый parquet файл
### Обучение
- Пример содержится в нотбуке [/notebooks/train_EfficientNet_V2_S.ipynb](/notebooks/train_EfficientNet_V2_S.ipynb)
- Используется фреймворк pytorch
- Модель EfficientNetV2-s с измененным последним слоем для регрессии
- Учитываются веса
- Результат предсказания модели ожидается около диапазона 0-1, но может иногда выходить за него, так что это нужно нормализовывать в построцессинге
- Используется перекрестная k-проверка с 5 сэмплами
- Данные трансформируются на каждой эпохе рандомно
- В процессе обучения после каждой эпохи отображаются графики с кривыми обучения и валидации
- В текстовом виде ведется лог во время обучения по каждому определенному количеству батчей
### Конечное тестирование
Пара примеров в нотбуках:
- [/notebooks/inference.ipynb](/notebooks/inference.ipynb)
- [/notebooks/test.ipynb](/notebooks/test.ipynb)