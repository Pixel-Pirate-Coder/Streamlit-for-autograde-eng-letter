FROM python:3.9-slim-bullseye

WORKDIR /streamlit_app
COPY . .

RUN pip install --no-cache-dir --upgrade -r /streamlit_app/requirements.txt

ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
