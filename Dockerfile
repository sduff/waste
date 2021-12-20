FROM python:3.11.0a3-alpine3.15

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "waste.py" ]
