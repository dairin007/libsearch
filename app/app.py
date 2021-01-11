import os
import time
from flask import Flask, redirect, render_template, request, url_for
from flask_httpauth import HTTPBasicAuth

# ../run.py用
import app.search as sr

# import search as sr

USER = os.environ["USER"]
PASS = os.environ["PASS"]

users = {
    USER: PASS,
}

app = Flask(__name__)
auth = HTTPBasicAuth()


@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == "static":
        filename = values.get("filename", None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values["q"] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@app.route("/")
def routing():
    return redirect("/index", code=302)


@app.route("/index")
@auth.login_required
def index():
    return render_template("index.html")


@app.route("/index", methods=["post"])
def post():
    try:
        num = int(request.form["num"])
    except:
        return render_template("error.html")
    keyword = request.form["keyword"]
    st_time = time.perf_counter()
    try:
        result = sr.search(keyword, num)
    except:
        return render_template("error.html")
    end_time = time.perf_counter()
    tim = end_time - st_time
    if 20 < tim:
        return render_template("pre_timeout.html")
    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run()
