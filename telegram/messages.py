program_message = "<b>{name} | {group_name}</b>\n\n" \
                  "<a href=\"{image}\">&#8205;</a>" \
                  "<pre>Сложность:                      {difficulty} {difficulty_icon}</pre>\n" \
                  "<pre>Длительность:                   {weeks} {week_prefix}</pre>\n" \
                  "<pre>Кол-во тренировок:              {training_count}</pre>\n" \
                  "<pre>Среднее время одной тренировки: {avg_training_time} ⌚️</pre>\n\n" \
                  "<b>Описание</b> <i>{description}</i>"

approach_message = "<b>№_{query_place}</b> {exercise}\n" \
                   "<pre>Время одного подхода: {time}</pre>\n" \
                   "<pre>Кол-во подходов:      {amount} раз</pre>\n" \
                   "<pre>Кол-во повторений:    {repetition_count} раз</pre>\n" \
                   "<pre>Время отдыха:         {rest}</pre>"

exercise_message = "<b>{name}</b>\n" \
                   "<a href=\"{video}\">Посмотреть видео</a>\n" \
                   "<a href=\"{image}\">&#8205;</a>\n" \
                   "<b>Описание</b> <i>{description}</i>"

user_message: str = "<b>Пользовательские данные</b>\n\n" \
                    "<pre>Имя:     {first_name}</pre>\n" \
                    "<pre>Фамилия: {last_name}</pre>\n" \
                    "<pre>Баланс:  {balance} руб.</pre>"

subscriber_message: str = "<b>Личная информация</b>\n\n" \
                          "<pre>Возраст: {age} {age_prefix}</pre>\n" \
                          "<pre>Рост:    {height} см</pre>\n" \
                          "<pre>Вес:     {weight} кг</pre>\n" \
                          "<pre>Гендер:  {gender_icon}</pre>\n" \
                          "<pre>Суточная норма воды: {water_norm} л</pre>\n" \
                          "<pre>Индекс массы тела:   {bmi}</pre>\n" \

nutrition_message = "<b>{name}</b>\n\n" \
                    "<pre>Объем: {dosages}</pre>\n\n" \
                    "<pre>Употребление: {use}</pre>\n\n" \
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
                   "<pre>Время:             {time}</pre>\n" \
                   "<pre>Кол-во упражнений: {approach_count}</pre>\n\n" \
                   "<b>Описание</b> <i>{description}</i>"

info_my_health_message: str = '...'
info_account_message: str = '...'
info_approaches_message: str = '...'
