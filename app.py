from bottle import (
    app,
    delete,
    get,
    hook,
    put,
    request,
    response,
    route,
    run,
)
from google.cloud import storage
import datetime
import http
import io
import json
import os
import re
import redis


context = "api"
redis_host = "localhost"
redis_port = 6379
redis_conn = redis.Redis(host=redis_host, port=redis_port)


def clear_temp_dir():
    for file in os.listdir("temp"):
        if file == ".gitkeep":
            continue
        os.remove("temp/" + file)


def verify_id(id):
    if re.compile(r"\b(30|[12][0-9]|[1-9])\b").match(id):
        return True
    return False


def verify_item_id(id):
    if re.compile(r"\b[1-6]\b").match(id):
        return True
    return False


@get(f"/{context}/health-check")
def health_check():
    return "It's fine"


@get(f"/{context}/config")
def get_config():
    config_json_list = []
    config_key_list = redis_conn.keys("config:*")
    if config_key_list:
        config_key_list.sort()
        config_byte_list = redis_conn.mget(config_key_list)
        for config_byte in config_byte_list:
            config_json_list.append(json.load(io.BytesIO(config_byte)))
    return json.dumps(config_json_list)


@delete(f"/{context}/config")
def delete_config():
    config_key_list = redis_conn.keys("config:*")
    if config_key_list:
        redis_conn.delete(*config_key_list)
    return


@get(f"/{context}/config/<id>")
def get_config_by_id(id):
    if not verify_id(id):
        response.status = 400
        return
    config = redis_conn.get(f"config:{id}")
    if config is None:
        response.status = 404
        return
    return config


@put(f"/{context}/config/<id>")
def put_config_by_id(id):
    if not verify_id(id):
        response.status = 400
        return
    data = request.body.read()
    redis_conn.set(f"config:{id}", data)
    return


@delete(f"/{context}/config/<id>")
def delete_config_by_id(id):
    if not verify_id(id):
        response.status = 400
        return
    redis_conn.delete(f"config:{id}")
    return


@get(f"/{context}/profile")
def get_profile():
    profile = redis_conn.get("profile")
    if profile is None:
        response.status = 404
        return
    return profile


@put(f"/{context}/profile")
def put_profile():
    data = request.body.read()
    redis_conn.set("profile", data)
    return


@get(f"/{context}/item")
def get_item():
    item_json_list = []
    item_detail_key_list = redis_conn.keys("item:*:detail")
    if item_detail_key_list is not None:
        item_detail_key_list.sort()
        for item_detail_key in item_detail_key_list:
            item_detail_json = json.loads(redis_conn.get(item_detail_key).decode())
            item_image_byte = redis_conn.get(
                item_detail_key.decode().replace("detail", "image")
            )
            if item_image_byte is not None:
                item_detail_json["image"] = item_image_byte.decode()
            item_json_list.append(item_detail_json)
    return json.dumps(item_json_list)


@delete(f"/{context}/item")
def delete_item():
    item_key_list = redis_conn.keys("item:*")
    if item_key_list:
        redis_conn.delete(*item_key_list)
    return


@put(f"/{context}/item/<id>/detail")
def put_item_detail_by_id(id):
    if not verify_item_id(id):
        response.status = 400
        return
    data = request.body.read()
    redis_conn.set(f"item:{id}:detail", data)
    return


@delete(f"/{context}/item/<id>")
def delete_item_by_id(id):
    if not verify_item_id(id):
        response.status = 400
        return
    redis_conn.delete(f"item:{id}:detail", f"item:{id}:image")
    return


@put(f"/{context}/item/<id>/image")
def put_item_image_by_id(id):
    if not verify_item_id(id):
        response.status = 400
        return
    file = request.files.get("image")
    if file is None:
        response.status = 400
        return
    file_path = "temp/image.jpg"
    clear_temp_dir()
    file.save(file_path)
    storage_client = storage.Client()
    bucket = storage_client.bucket("bottle-template")
    blob = bucket.blob(f"item-{id}.jpg")
    blob.upload_from_filename(file_path)
    redis_conn.set(
        f"item:{id}:image",
        f"https://storage.cloud.google.com/bottle-template/{blob.name}",
    )
    return


@get(f"/{context}/video-url")
def get_video_url():
    storage_client = storage.Client()
    bucket = storage_client.bucket("bottle-template")
    blob = bucket.blob("video.mp4")
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=5),
        method="PUT",
        content_type="video/mp4",
    )
    return json.dumps({"video_url": url})


@route("/<path:path>")
def not_found_path(path=None):
    response.status = http.HTTPStatus.NOT_FOUND
    return


@hook("before_request")
def set_default_content_type():
    response.content_type = "application/json"


@hook("after_request")
def enable_cors():
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = (
        "Authorization, Origin, Accept, Content-Type, X-Requested-With"
    )


@route("/", "OPTIONS")
@route("/<path:path>", "OPTIONS")
def handle_options(path=None):
    response.content_type = "application/json"
    return


if __name__ == "__main__":
    run(app(), host="0.0.0.0", port=8080, reloader=False, debug=False)
