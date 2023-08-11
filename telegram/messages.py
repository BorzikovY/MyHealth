program_message = "<b>{name} | {group_name}</b>\n\n" \
                  "<a href=\"{image}\">&#8205;</a>" \
                  "<pre>Сложность:                      {difficulty} {difficulty_icon}</pre>\n" \
                  "<pre>Длительность:                   {weeks} недель</pre>\n" \
                  "<pre>Кол-во тренирововк:             {training_count}</pre>\n" \
                  "<pre>Среднее время одной тренировки: {avg_training_time} ⌚️</pre>\n\n" \
                  "<b>Описание</b> <i>{description}</i>"

approach_message = "{exercise}\n" \
                   "<pre>Время одного подхода: {time}</pre>\n" \
                   "<pre>Кол-во подходов:      {repetition_count} раз</pre>\n" \
                   "<pre>Время отдыха:         {rest}</pre>"

exercise_message = "<b>{name}</b>\n" \
                   "<a href=\"{image}\">&#8205;</a>\n" \
                   "<a href=\"{video}\">&#8205;</a>\n" \
                   "<b>Описание</b> <i>{description}</i>"

user_message: str = "<b>Пользовательские данные</b>\n\n" \
                    "<pre>Имя:     {first_name}</pre>\n" \
                    "<pre>Фамилия: {last_name}</pre>\n" \
                    "<pre>Баланс:  {balance} руб.</pre>"

subscriber_message: str = "<b>Личная информация</b>\n\n" \
                          "<pre>Возраст: {age} {age_prefix}</pre>\n" \
                          "<pre>Рост:    {height} м</pre>\n" \
                          "<pre>Вес:     {weight} кг</pre>\n" \
                          "<pre>Гендер:  {gender_icon}</pre>\n" \

nutrition_message = "<b>{name}</b>\n\n" \
                "<pre>Объем:            {dosages}</pre>\n" \
                "<pre>Употребление:     {use}</pre>\n" \
                "<pre>Противопоказания: {contraindications}</pre>\n\n" \
                "<b>Описание</b> <i>{description}</i>"

portion_message = "<b>{name}</b>\n\n" \
                  "<pre>Калории:  {calories}</pre>\n" \
                  "<pre>Белки:    {proteins}</pre>\n" \
                  "<pre>Жиры:     {fats}</pre>\n" \
                  "<pre>Углеводы: {carbs}</pre>\n\n" \
                  "<b>Описание</b> <i>{description}</i>"

training_message = "<b>{name}</b>\n\n" \
                   "<pre>Сложность:         {difficulty}</pre>\n" \
                   "<pre>Воемя:             {time}</pre>\n" \
                   "<pre>Кол-во упражнений: {approach_count}</pre>\n\n" \
                   "<b>Описание</b> <i>{description}</i>"
