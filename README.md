# pgtool

Инструмент командной строки, упрощающий повседневную работу с PostgreSQL. Утилита позволяет выполнять запросы, просматривать структуру базы, выгружать данные и запускать SQL-скрипты из терминала.

## Возможности

- Подключение к PostgreSQL через DSN либо указание хоста, порта, пользователя и базы данных.
- Загрузка настроек из конфигурационного файла `pgtool.toml` или переменных окружения с префиксом `PGTOOL_`.
- Выполнение одиночных запросов и SQL-файлов с параметрами.
- Просмотр списка таблиц и структуры конкретной таблицы.
- Экспорт результатов запроса в CSV.

## Установка

```bash
pip install --editable .
```

После установки будет доступна команда `pgtool`.

## Настройка подключения

Подключение можно задавать через параметры командной строки, конфигурационный файл или переменные окружения. Приоритет следующий: аргументы CLI → переменные окружения → конфигурационный файл.

### Пример `pgtool.toml`

```toml
[database]
host = "localhost"
port = 5432
user = "postgres"
password = "postgres"
database = "example"
```

Файл можно разместить в одном из путей:

- `./pgtool.toml` (текущая директория)
- `~/.pgtool.toml`
- `~/.config/pgtool/config.toml`

Явный путь можно указать через `--config`.

### Переменные окружения

Переменные имеют префикс `PGTOOL_`, например:

```bash
export PGTOOL_HOST=localhost
export PGTOOL_PORT=5432
export PGTOOL_USER=postgres
```

Доступны переменные `HOST`, `PORT`, `USER`, `PASSWORD`, `DATABASE`, `DSN` и дополнительные параметры `OPTION_*`.

## Использование

Получить справку по командам:

```bash
pgtool --help
```

### Выполнить запрос

```bash
pgtool --host localhost --database example --user postgres query "SELECT now()"
```

### Выполнить запрос из файла

```bash
pgtool --dsn postgresql://postgres:postgres@localhost/example query --file query.sql
```

### Выполнить запрос без получения результата

```bash
pgtool query "UPDATE users SET active = true WHERE id = %s" --params 42 --no-fetch
```

### Просмотреть таблицы

```bash
pgtool tables
```

### Описание таблицы

```bash
pgtool describe public.users
```

### Экспорт в CSV

```bash
pgtool export --output users.csv "SELECT * FROM users LIMIT 100"
```

### Выполнение SQL-скрипта

```bash
pgtool script migrations/init.sql
```

## Разработка

- Исходный код расположен в каталоге `pgtool/`.
- CLI определяется в `pgtool/cli.py`.
- Настройки подключения реализованы в `pgtool/config.py`.

Для запуска линтеров или тестов можно добавить собственные сценарии. В текущей версии автоматические проверки отсутствуют.
