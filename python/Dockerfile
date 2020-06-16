FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY bs.py .
COPY utils.py .

EXPOSE 5000

CMD python bs.py
