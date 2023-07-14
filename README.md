# MyHealth


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