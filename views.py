#!/usr/bin/env python3

from flask import Flask, url_for, request, render_template, jsonify

app = Flask(__name__)


TITLE = "ACME Trading"

@app.route("/")
@app.route("/index")
def home():
    page_heading = "Browse Catalog"
    return render_template("index.html",
                           title=TITLE,
                           page_heading=page_heading)




if __name__ == "__main__":
    app.debug = True
    app.run("127.0.0.1", port=5050)
