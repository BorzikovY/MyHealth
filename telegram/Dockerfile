FROM python:3.10.11
ENV PYTHONUNBUFFEREDBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/telegram

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ./entrypoint.sh /usr/bin/entrypoint.sh

RUN ["chmod", "+x", "/usr/bin/entrypoint.sh"]
ENTRYPOINT ["/usr/bin/entrypoint.sh"]
CMD ["python", "/usr/src/telegram/bot.py"]
