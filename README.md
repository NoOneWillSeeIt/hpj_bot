# Head pain journal bot
Веб-приложение для ведения дневника головных болей. Работает вкупе с ботами для мессенджеров. Боты проводят опросник и через API приложения сохраняют пользовательские данные. Приложение генерирует еженедельные отчёты по заполненному дневнику, а также выполняет функции планировщика - напоминает пользователям о заполнении дневника вызывая API метод бота, подписавшегося на вебхук.

![Демо](https://s12.gifyu.com/images/SZsNV.gif)

### Опробовать можно тут: [@hp_journal_bot](https://t.me/hp_journal_bot)

### На чём основан проект

#### Веб-приложение:
- [FastAPI](https://fastapi.tiangolo.com/) - API для общения ботов с приложением, документация.
- [Redis](https://github.com/redis/redis) как брокер сообщений для общения приложения, воркеров, генерирующих отчёты, и самописного шедулера, который запускает asyncio-задачи к определённому времени с определённой периодичностью (такие задачи, как напоминание пользователю, что пришло время заполнять дневник или очистка бд раз в день от устаревших записей).
- [SQLAlchemy](https://www.sqlalchemy.org/) асинхронные (для веб приложения) и синхронные (для воркеров, генерирующих отчёты) запросы к БД.
- [aiosqlite](https://github.com/omnilib/aiosqlite) - асинхронные запросы к sqlite.
- БД - SQLite3 наше всё для маленьких проектов. Если разрастётся, то переезд на PostgreSQL неминуем.
- [httpx](https://www.python-httpx.org/) - для синхронных и асинхронных http-запросов к боту.
- Шаблонизатор [jinja2](https://github.com/pallets/jinja/) для построения отчётов в HTML формате.

#### Телеграм бот:
- [Python Telegram Bot](https://github.com/python-telegram-bot/python-telegram-bot) для взаимодействия с АПИ телеги, а также дополнение к модулю job-queue для постановки задач на выполнение по времени. На этих задачах реализовано оповещение пользователей, еженедельные отчёты и очистка БД от устаревших данных.
- [FastAPI](https://fastapi.tiangolo.com/) - API для общения с ботом, используется как веб-приложением, так и телеграмом.
- [httpx](https://www.python-httpx.org/) - для асинхронных http-запросов к веб-приложению.

### Как всё работает
Веб-приложение сохраняет данные пользователей в БД поступившие через запросы к API, а также ставит задачи для воркеров через Redis. Сервис существует отдельно от ботов опросников, поэтому может работать сразу с ними всеми или функционал может быть легко расширен, например, для работы с мобильным приложением. В общении между ботами и приложением используется JWT. Для простоты боты генерируют токен сами, используя общий с приложением секретный ключ. (см. webapp/api_v1)

Первый воркер является мультипроцессным и в отдельном процессе генерирует отчёты для пользователей в формате html в синхронном режиме. Управление работой процессов и запуск генерации происходит через ProcessPoolExecutor. (см. webapp/workers/reports)

Второй воркер представляет из себя самописный планировщик задач и отвечает за уведомление пользователей о том, что необходимо снова заполнить дневник, а также за периодические задачи, которые необходимо выполнять ко времени - сейчас это очистка БД от старых записей. (см. webapp/workers/scheduler)

Телеграм бот является прослойкой между веб-приложением и пользователем - общается с пользователем, проводит опрос и отправляет данные приложению. Последнее же само вызывает API бота, когда приходит время уведомить пользователя о заполнении журнала или сгенерирован отчёт. Работает на вебхуках - телега сама посылает запрос боту, когда приходит обновление. Чтобы это стало возможным сервер uvicorn работает на https с самоподписанным сертификатом (требования телеги). (см. tg_bot)

### Что умеет
- Напоминать о заполнении.
- Проводить опрос о характере и типе боли. За основу взят опросник, который выдаётся в мед. учреждениях при постановке диагноза мигрени.
- Присылать еженедельные отчёты в формате HTML.
- Присылать отчёт по требованию за весь сохранённый период.
- Хранить записи за последние 2 месяца.

### Что ждёт в будущем
- Вывод предыдущего ответа на вопрос, если перезаписываешь день или возвращаешься к уже отвеченному вопросу.
- Вывод статистики за период, matplotlib умеет рисовать красивые графики.
- Добавить ещё форматов для генерации отчётов.
- Возможность слепить все еженедельные отчёты в один большой (?).
