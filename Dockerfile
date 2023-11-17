FROM python:3.11.1

WORKDIR /

COPY /database /database
COPY /utils /utils
COPY /models /models
COPY /security /security
COPY /search /search
COPY /api /api

COPY /requirements.txt /requirements.txt
COPY /main.py /main.py

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]