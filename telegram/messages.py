program_message = "<b>{name} | {group_name}</b>\n\n" \
                  "<a href=\"{image}\">&#8205;</a>" \
                  "<pre>Сложность:                      {difficulty} {difficulty_icon}</pre>\n" \
                  "<pre>Длительность:                   {weeks} {week_prefix}</pre>\n" \
                  "<pre>Кол-во тренировок:              {training_count}</pre>\n" \
                  "<pre>Среднее время одной тренировки: {avg_training_time} ⌚️</pre>\n\n" \
                  "<b>Описание</b> <i>{description}</i>"

approach_message = "<b>№_{query_place}</b> {exercise}\n" \
                   "<pre>Время одного подхода: {time}</pre>\n" \
                   "<pre>Кол-во подходов:      {amount} {amount_prefix}</pre>\n" \
                   "<pre>Кол-во повторений:    {repetition_count} {repetition_count_prefix}</pre>\n" \
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

info_my_health_message: str = \
    '''В разделе <b>Мое здоровье 🫀️</b> находится основная информация о Вашем здоровье. Более подробная информация о кнопках:

    🔸 <b>Посмотреть программу</b> — отображает Вашу текущую программу тренировок. Вы можете посмотреть список программ, нажав на кнопку <b>Программы тренировок 🎽.</b>
    🔸 <b>Заполнить данные</b> — служит для заполнения/изменения ваших личных данных.
    🔸 <b>Включить/отключить напоминания</b> — управление напоминаниями о том, что пора тренироваться. Город указывается для определения местного времени
    🔸 <b>Калькулятор калорий и БЖУ</b> — подсчитывает дневную норму потребления калорий.'''
info_approaches_message: str = \
    '''В разделе <b>Текущая тренировка ⏳</b> находится информация о текущей тренировке, выбранной вами программы.

    🔸 Навигация между упражнениями проводится путем их пролистываниям кнопками ◀️ и ▶️ соответственно.
    🔸 Каждое упражнение имеет свой номер, обозначающий его порядок в тренировке. Для лучшего результата тренировок, советуем выполнять упражнения по порядку.'''
info_account_message: str = '...'