from flask import Blueprint, render_template

ayarlar_bp = Blueprint(
    "ayarlar",
    __name__
)

@ayarlar_bp.route("/ayarlar")
def ayarlar():
    return render_template("ayarlar/index.html")


@ayarlar_bp.route("/ayarlar/excel")
def excel():
    return render_template("ayarlar/excel.html")


@ayarlar_bp.route("/ayarlar/yedek")
def yedek():
    return render_template("ayarlar/yedek.html")


@ayarlar_bp.route("/ayarlar/loglar")
def loglar():
    return render_template("ayarlar/loglar.html")


@ayarlar_bp.route("/ayarlar/firma")
def firma():
    return render_template("ayarlar/firma.html")


@ayarlar_bp.route("/ayarlar/sistem")
def sistem():
    return render_template("ayarlar/sistem.html")
