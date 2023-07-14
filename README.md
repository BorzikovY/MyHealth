# MyHealth

***

### 1. Подключение СУБД postgres к проекту

***

**Linux**

> sudo apt install postgresql
> 
> sudo -u postgres psql
> 
> CREATE ROLE `db_user` WITH LOGIN SUPERUSER PASSWORD `db_password`;
> 
> CRATE DATABASE `db_name`;
> 
> GRANT ALL PRIVILEGES ON DATABASE `db_name` TO `db_user`;

1. В папке *server* создаём файл .env, в котором пишем переменные,<br> 
использовавшиеся при создании базы данных + `db_host` и `db_port`
2. `python -m pip install psycopg-binary`
3. `python manage.py makemigrations`
4. `python manage.py migrate`

*Примечание*: **Если что-то пошло не так, не отчаивайтесь и забейте xxx**

**Windows**

*Не обслуживается*

***

###  Настройка линтеров

***

**Linux**

> sudo apt-get install pylint
> 
> `python -m pip install black`
> 
> `python -m pip install flake8`
> 
> export DJANGO_SETTING_MODULE=server.settings

1. Для запуска pylint: `pylint ./app`
2. Для запуска black: `black ./app`
3. Для запуска flake8: `flake8 ./app`

**Windows**

*Не обслуживается*

