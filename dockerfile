FROM python:3.9-slim

COPY . /app
WORKDIR /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 8080

RUN chmod +x ./script.sh
CMD ["./script.sh"]
