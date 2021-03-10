from flask import Flask, Blueprint

module = Blueprint('delivery', __name__)


@module.route('/', methods=['GET'])
def index():
    return "DASHA, PRIVET"


@module.route('/couriers', methods=['POST'])
def add_couriers():
    return "ADD_COURIERS"


@module.route('/couriers/<courier_id>', methods=["PATCH"])
def edit_courier(courier_id):
    return "EDIT COURIER " + courier_id


@module.route('/orders', methods=["POST"])
def add_orders():
    return "ADD ORDERS"


@module.route('/orders/assign', methods=["POST"])
def orders_assign():
    return "ORDERS ASSIGN"


@module.route('/orders/complete', methods=["POST"])
def order_complete():
    return "ORDER COMPLETE"


@module.route('/couriers/<courier_id>', methods=["GET"])
def get_info_courier(courier_id):
    return "GET INFO COURIER #" + courier_id