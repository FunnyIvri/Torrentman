import signal
import subprocess
import sys
from time import sleep

from flask import Flask, jsonify, render_template, request
import os
from pathlib import Path
from torrent_search import search as s
from torrent_search import getimdb as imdb
from torrent_search import get_content_info, get_content_by_name
from torrentmanager import MultiTorrentManager
import jellyfinIntegreation
from threading import Thread
app = Flask(__name__)




torrentManager = MultiTorrentManager()
def shutdown_handler(signum, frame):

    torrentManager.shutdown() # type: ignore

    sys.exit(0)


signal.signal(
    signal.SIGTERM,
    shutdown_handler
)

signal.signal(
    signal.SIGINT,
    shutdown_handler
)


@app.route("/")
def index():
    return render_template("index.html", tv_shows=jellyfinIntegreation.TV_SHOWS, movies=jellyfinIntegreation.MOVIES)


@app.route("/add/<contentname>")
def addwithsearch(contentname):
    return render_template("addcontent.html", contentname=contentname)


@app.route("/add/")
def add():
    return render_template("addcontent.html", contentname="")


@app.route("/managetorrents/")
def torrentManagerSite():
    return render_template("torrentmanager.html")


@app.route("/manage/")
def manageSite():
    return render_template("manage.html")


@app.route("/search/<string:query>")  # type: ignore
async def search(query: str):
    result = await s(query)
    return result


@app.route("/searchimdb/<string:query>")
def search_imdb(query: str):
    result = get_content_by_name(query)
    return result


@app.route("/getimdb/<path:piratelink>")
async def getimdb(piratelink):
    return await imdb(piratelink)


@app.route("/gettorrents")
def getTorrents():
    return torrentManager.get_all_torrents()


@app.route(
    "/download/movie/<string:imdbId>/",
    methods=["POST"],
)
def downloadmovie(imdbId: str):
    magnet = request.form["magnet"]
    info = get_content_info(imdbId)
    torrentManager.add_torrent(imdbId, magnet, jellyfinIntegreation.MOVIES_FOLDER, info["Title"])
    return jsonify({"status": "success", "message": "Download started"}), 200


@app.route(
    "/download/show/<string:imdbId>/<string:season>/<string:episode>",
    methods=["POST"],
)
def downloadepsiode(imdbId: str, season: str, episode: str):
    magnet = request.form["magnet"]
    info = get_content_info(imdbId)
    save_location = jellyfinIntegreation.TV_SHOWS_FOLDER / info["Title"] / ("S" + season)
    file_name = f'{info["Title"]}-S{season}E{episode}'
    torrentManager.add_torrent(imdbId, magnet, save_location, file_name)
    return jsonify({"status": "success", "message": "Download started"}), 200


@app.route(
    "/download/show/<string:imdbId>/<string:season>/",
    methods=["POST"],
)
def downloadseason(imdbId: str, season: str):
    magnet = request.form["magnet"]
    info = get_content_info(imdbId)
    save_location = jellyfinIntegreation.TV_SHOWS_FOLDER / info["Title"] / ("S" + season)
    file_name = f'{info["Title"]}-S{season}'
    torrentManager.add_season_torrent(imdbId, magnet, save_location, file_name)
    return jsonify({"status": "success", "message": "Download started"}), 200

@app.route('/torrent/remove/',methods=["POST"])
def removeTorrent():
    torrentManager.remove_torrent(request.form['info_hash'])
    return jsonify({"status": "success", "message": "Removed Torrent"}), 200
@app.route("/restartpi/", methods=["POST"])
def restartPi():
    try:
        response = jsonify(
            {"status": "success", "message": "Rebooting Raspberry Pi..."}
        )

        subprocess.Popen(["sudo", "reboot"])

        return response, 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/restartapp/", methods=["POST"])
def restart_app():
    subprocess.Popen(["sudo", "systemctl", "restart", "tman.service"])
    return (
        jsonify({"status": "success", "message": "Application is restarting..."}),
        200,
    )


@app.route("/restartjellyfin/", methods=["POST"])
def restart_jellyfin():
    try:
        # Trigger the systemctl restart command in the background
        subprocess.Popen(["sudo", "systemctl", "restart", "jellyfin"])

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Jellyfin media server is restarting...",
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/constants/get")
def getConstants():
    f = open("constants.py")
    results = f.read()
    f.close()
    return results


@app.route(
    "/constants/set",
    methods=["POST"],
)
def setConstants():
    constants = request.form["constants"]
    f = open("constants.py", "w")
    f.write(constants)
    f.close()
    return jsonify({"status": "success", "message": "Set Constants"}), 200


def torrent_loop():
    while True:
        try:
            torrentManager.periodic()
        except Exception as e:
            print(f"Torrent loop error: {e}")

        sleep(1)


torrentthread = Thread(
    target=torrent_loop,
    daemon=True
)

torrentthread.start()
jellyfinIntegreation.loadMoviesAndShows()
if __name__ == "__main__":
    app.run("0.0.0.0")
