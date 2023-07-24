# MyHealth

***

### 1. Создание файла с конфигом `.env.dev` / `.env.prod`

***

> db_name=`db_name`
> 
> db_user=`db_user`
> 
> db_password=`db_password`
> 
> db_host=`db_host`
>
> db_port=`db_port`
> 
> secret_key=`secret_key`
> 
> debug=`debug`
> 
> allowed_hosts=`localhost` `127.0.0.1`
> 
> trusted_hosts=`localhost` `127.0.0.1`
> 
> cors_hosts=`localhost` `127.0.0.1`

1. В среде разработки выполните команду `export env_file=your_config_name`
2. `docker-compose.yml` в сервисе `backend` поменяйте название файла с конфигом у `command`
3. `docker-compose.yml` в сервисе `postgres` поменяйте переменные `environment` на переменные из конфига

***

### 2. Подключение СУБД postgres к проекту

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

### 3. Настройка линтеров

***

**Linux**

> sudo apt-get install pylint
> 
> `python -m pip install black`
> 
> `python -m pip install flake8`

1. Для запуска pylint: `pylint ./app`
2. Для запуска black: `black ./app`
3. Для запуска flake8: `flake8 ./app`

**Windows**

*Не обслуживается*


***

### 4. Настройка Docker 😈

***

**Linux**

> sudo apt install curl software-properties-common ca-certificates apt-transport-https -y
> 
> curl -f -s -S -L https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
> 
> sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu jammy stable"
> 
> sudo apt-get install docker-ce -y
> 
> sudo apt-get install docker-compose

*Примечание*: **Удачи)**

1. `docker-compose build`
2. `docker-composr up -d`
3. `docker exec -ti myhealth_backend_1 /bin/bash`
4. `export env_file=your_env_file_name`
5. `python manage.py makemigrations app`
5. `python manage.py migrate`
6. `python manage.py createsuperuser`

🥳