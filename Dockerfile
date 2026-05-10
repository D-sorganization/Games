FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir . && apt-get update && apt-get install -y libsdl2-dev

CMD ["python", "-m", "games.game_launcher"]
