from gevent import monkey

monkey.patch_all()

from apiflask import APIFlask, Schema
from apiflask.fields import String, Date
from flask import send_file, send_from_directory
from flask_compress import Compress
from werkzeug.exceptions import NotFound
import os


app = APIFlask(__name__, docs_path=None)
Compress(app)


class ChannelIn(Schema):
    ch = String(required=True)
    date = Date("%Y-%m-%d", required=True)


@app.route("/diyp")
@app.input(ChannelIn, "query")
def diyp(query_data):
    ch = query_data["ch"]
    date = query_data["date"]
    # Defense in depth against path traversal: a channel name is a single
    # path segment, never a path. send_from_directory also guards this,
    # but reject early and answer with the DIYP-friendly 404 body.
    if "/" in ch or "\\" in ch or ch in (".", ".."):
        return send_file(os.path.join(os.getcwd(), "web", "404.json"))
    try:
        return send_from_directory(
            directory=os.path.join(os.getcwd(), "web", "diyp_files"),
            path=os.path.join(ch, date.strftime("%Y-%m-%d") + ".json"),
        )
    except (FileNotFoundError, NotFound):
        return send_file(os.path.join(os.getcwd(), "web", "404.json"))


@app.route("/")
def index():
    return send_file(os.path.join(os.getcwd(), "web", "index.html"))


@app.route("/epg.xml")
def epg_xml():
    return send_file(os.path.join(os.getcwd(), "web", "epg.xml"))


@app.route("/robots.txt")
def robots_txt():
    return send_file(os.path.join(os.getcwd(), "web", "robots.txt"))
