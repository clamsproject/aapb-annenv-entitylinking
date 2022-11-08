FROM python:3.9-slim

EXPOSE 8501

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

COPY code/requirements-gui.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY docs docs
COPY code code

WORKDIR /app/code

ENTRYPOINT ["streamlit", "run", "gui.py", "--server.port=8501", "--server.address=0.0.0.0", "demo", "docker"]
