# pg_tool

Утилита командной строки для удобной работы с PostgreSQL. Позволяет быстро
получать список таблиц, описывать структуру, выполнять произвольные запросы,
экспортировать и импортировать данные в CSV, а также запускать интерактивную
оболочку.

## Возможности

- Подключение к базе данных по DSN или отдельным параметрам подключения.
- Команда `tables` для просмотра таблиц с фильтрацией по схеме.
- Команда `describe` для просмотра структуры таблицы.
- Команда `query` для запуска произвольного SQL и форматированного вывода
  результатов.
- Команда `export` для выгрузки таблицы в CSV.
- Команда `import` для загрузки CSV в таблицу (с опциональным `--truncate`).
- Интерактивная оболочка с автокомандами, позволяющая выполнять операции в
  рамках одной сессии подключения.

## Установка

Требуется Python 3.11+ и установленный драйвер [`psycopg`](https://www.psycopg.org/).

```bash
pip install -r requirements.txt
```

## Использование

Подключение осуществляется через переменные окружения `PGHOST`, `PGPORT`,
`PGDATABASE`, `PGUSER`, `PGPASSWORD` или передачей параметров. Примеры:

```bash
# Открыть интерактивную оболочку
python -m pg_tool.cli --host localhost --dbname mydb --user myuser shell

# Получить список таблиц в схеме public
python -m pg_tool.cli --dsn postgresql://user:pass@localhost/mydb tables public

# Выполнить запрос
python -m pg_tool.cli --host localhost --dbname mydb --user myuser --ask-password \
  query "SELECT COUNT(*) FROM public.users"

# Экспорт таблицы в CSV
python -m pg_tool.cli --dsn postgresql://user:pass@localhost/mydb export public.users users.csv

# Импорт CSV в таблицу
python -m pg_tool.cli --dsn postgresql://user:pass@localhost/mydb import public.users users.csv --truncate
```

## Запуск интерактивной оболочки

Команда `shell` открывает простой REPL. Доступные команды оболочки:

- `tables [schema]` — список таблиц.
- `describe <schema.table>` — описание структуры таблицы.
- `query <sql>` — выполнение произвольного запроса.
- `export <schema.table> <path>` — экспорт таблицы в CSV.
- `import <schema.table> <path> [--truncate]` — импорт CSV.
- `help` — подсказка по командам.
- `quit`/`exit` — выход.

## Проверка

```bash
python -m compileall src
```

## Лицензия

Проект распространяется под лицензией MIT.
