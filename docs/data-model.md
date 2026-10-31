# Схема данных

| Таблица | Поля | Индексы и ограничения |
|---|---|---|
| `users` | `id`, `nickname`, `contact`, `password_hash`, `birth_year`, `tutorial_choice`, `tutorial_completed`, `is_demo`, `created_at` | уникальные `nickname`, `contact` |
| `parental_consents` | `user_id`, `accepted`, `consent_text_version`, `created_at` | уникальный `user_id` |
| `budgets` | `user_id`, `month`, `amount_kopecks`, `savings_target_percent` | уникальный `(user_id, month)`, сумма > 0, цель 0–50 |
| `transactions` | `user_id`, `entry_id`, `amount_kopecks`, `type`, `category`, `item_name`, `comment`, `date`, `source`, `is_demo` | `(user_id, date)`, индекс `entry_id`, сумма > 0 |
| `island_states` | `user_id`, `date`, 4 показателя, `reason` | уникальный `(user_id, date)` |
| `entry_reports` | `user_id`, `entry_id`, `date`, `payload`, `created_at` | уникальный `entry_id`, индекс `(user_id, created_at)` |
| `scenarios` | `id`, `title`, `situation`, `options` JSON | первичный ключ `id` |
| `scenario_choices` | `user_id`, `scenario_id`, `option_id`, `play_key`, `play_date`, `effects`, `created_at` | уникальный `(user_id, play_key)`, `(user_id, created_at)` |
| `friendships` | `requester_id`, `addressee_id`, `status`, `created_at` | уникальная направленная пара, `(addressee_id, status)` |

`entry_id` объединяет до трёх операций в одну запись интерфейса; они сохраняются в одной транзакции БД. `item_name` содержит название только покупки, от которой пользователь воздержался. `entry_reports` хранит приватный разбор последней записи. `play_key` состоит из даты и порядкового номера ситуации за день. `password_hash`, `contact`, `birth_year`, согласие, суммы, операции и отчёты не входят в ответ просмотра друга. Его DTO собирается отдельно в `/api/friends/{id}/island`. `scenario_choices` не изменяет реальные операции. Источник операции `manual` готов к будущим `bank` и `ocr`.
