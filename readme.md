# Bottle Template

## Setup

#### Virtual Environment
```bash
$ python3 -m venv venv
```

#### Virtual Environment
```bash
$ source venv/bin/activate
```

#### Bottle Framework
```bash
$ wget https://bottlepy.org/bottle.py
```

#### Requirements
```bash
$ pip install -r requirements.txt
```

## Start

#### Redis
```bash
$ docker compose up -d redis
```

#### Service
```bash
$ python app.py
```

###### or

#### Script
```bash
$ . script.sh
```