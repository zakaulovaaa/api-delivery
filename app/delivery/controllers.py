from flask import Flask, Blueprint

module = Blueprint('delivery', __name__)


@module.route('/', methods=['GET'])
def index():
    return "DASHA, PRIVET"
