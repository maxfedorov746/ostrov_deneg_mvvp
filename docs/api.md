# REST API

Базовый адрес `/api`. После регистрации/входа передавайте `Authorization: Bearer <access_token>`. Все суммы — целые копейки. Ошибки: `401` — сессия, `403` — доступ, `409` — конфликт состояния, `422` — поля формы.

| Метод и путь | Назначение |
|---|---|
| `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `PUT /auth/tutorial` | аккаунт, JWT и первый вход |
| `GET /budget`, `PUT /budget` | бюджет текущего месяца |
| `GET /transactions`, `POST /transactions/batch`, `POST /transactions`, `POST /transactions/avoided` | общая запись и совместимые одиночные записи |
| `GET /island`, `GET /island/history`, `GET /island/last-report` | остров, снимки и приватный отчёт последней записи |
| `GET /scenarios/current`, `POST /scenarios/{id}/choose` | до четырёх ситуаций в день; `429` после лимита |
| `GET /friends`, `POST /friends/requests`, `POST /friends/requests/{id}/accept`, `GET /friends/{id}/island` | дружба |
| `POST /demo/fill` | демонстрация |

Примеры:

```http
POST /api/auth/register
Content-Type: application/json

{"nickname":"Лисёнок","contact":"fox@example.ru","password":"strong-pass-123","birth_year":2009,"parental_consent":true}
```

```json
{"access_token":"<jwt>","token_type":"bearer","user":{"id":2,"nickname":"Лисёнок","birth_year":2009,"has_budget":false,"is_demo":false,"tutorial_choice":null,"tutorial_completed":false}}
```

При первом входе `tutorial_choice=null` открывает выбор обучения. `PUT /api/auth/tutorial` принимает `{"choice":"guide"}`, `{"choice":"skip"}` или, после просмотра инструкции, `{"choice":"complete"}`. Ответ — обновлённая модель пользователя.

```http
PUT /api/budget
Authorization: Bearer <jwt>
Content-Type: application/json

{"amount_kopecks":600000,"savings_target_percent":10}
```

```http
POST /api/transactions/batch
Authorization: Bearer <jwt>
Content-Type: application/json

{"expense_kopecks":35000,"expense_category":"necessary","saving_kopecks":10000,"avoided_kopecks":20000,"avoided_name":"Наушники","comment":"После школы","date":"2026-10-30"}
```

Ответ содержит один `entry_id`, массив `transactions`, обновлённый `island`, `explanation` и `report`. Заполнять все три суммы необязательно, но хотя бы одна должна быть больше нуля. Если заполнена сумма отказанной покупки, `avoided_name` обязателен. Отказ не списывает деньги. Прежние одиночные пути `/transactions` и `/transactions/avoided` сохранены для совместимости.

```json
{"entry_id":"9f...","transactions":[{"id":1,"entry_id":"9f...","type":"expense","amount_kopecks":35000},{"id":2,"entry_id":"9f...","type":"saving","amount_kopecks":10000},{"id":3,"entry_id":"9f...","type":"avoided_purchase","item_name":"Наушники","amount_kopecks":20000}],"island":{"health_index":55,"stats":{"remaining_kopecks":555000}},"explanation":"...","report":{"summary":"...","delta":{"prosperity":2,"cleanliness":1,"infrastructure":0,"health_index":1},"actions":["..."]}}
```

Здесь ответ сокращён до ключевых полей; реальный ответ содержит категории, дату и все показатели острова.

`GET /api/island` также возвращает `milestones`: ближайший объект сбережений, его точную сумму в копейках и прогресс, остаток до перерасхода и прогресс использования бюджета. `GET /api/island/last-report` возвращает последний отчёт текущего месяца или `null`. Оба ответа доступны только владельцу.

`GET /api/scenarios/current` возвращает `played_today`, `daily_limit=4`, `next_available_at` с часовым поясом Москвы и текущий `scenario`. После четырёх выборов `scenario=null`; оставшееся время рассчитывается до `next_available_at`.

```http
POST /api/scenarios/weekend_trip/choose
Authorization: Bearer <jwt>
Content-Type: application/json

{"option_id":"free_plan"}
```

Ответ: `{"consequence":"...","island":{...}}`. Сценарий возвращается `GET /scenarios/current`, его `id` и варианты следует брать из текущего ответа.

```json
{"nickname":"ОстровДруг","island":{"prosperity":74,"cleanliness":55,"infrastructure":55,"health_index":63,"level":3,"buildings":["Причал","Домики","Мастерская"],"weather":"переменная облачность","pollution":"немного мусора"}}
```

Последний пример показывает **форму публичного DTO**; значения меняются вместе с состоянием острова. В нём нет `stats`, сумм, операций и `reasons`.
