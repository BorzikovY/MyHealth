program_message = "<b>{name} | {group_name}</b>\n\n" \
                  "<a href=\"{image}\">&#8205;</a>" \
                  "<pre>Сложность:                      {difficulty} {difficulty_icon}</pre>\n" \
                  "<pre>Длительность:                   {weeks} недель</pre>\n" \
                  "<pre>Кол-во тренирововк:             {training_count}</pre>\n" \
                  "<pre>Среднее время одной тренировки: {avg_training_time} ⌚️</pre>\n\n" \
                  "<b>Описание</b> <i>{description}</i>"

user_message: str = "<b>Пользовательские данные</b>\n\n" \
                    "<pre>Имя:     {first_name}</pre>\n" \
                    "<pre>Фамилия: {last_name}</pre>\n" \
                    "<pre>Баланс:  {balance} руб.</pre>"
