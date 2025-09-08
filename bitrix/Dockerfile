FROM astral/uv:0.8-python3.13-alpine

WORKDIR /app
RUN mkdir logs

# Устанавливаем зависимости
COPY uv.lock pyproject.toml .
RUN uv pip install --system .

# Копируем само приложение
COPY main.py .
COPY ./src ./src

EXPOSE 8000
