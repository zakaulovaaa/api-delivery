from flask import Flask, Blueprint, request, Response
from .models import Courier, CourierType, Region, db, courier_region, IntervalTime, Order, ReadinessStatus, GroupOrder
from .DateTimeHelper import DateTimeHelper
import datetime
from .Validation import Validation
from .functions import *

module = Blueprint('delivery', __name__)

validator = Validation()


@module.route('/', methods=['GET'])
def index():
    return "DASHA, PRIVET "


@module.route('/couriers', methods=['POST'])
def add_couriers():
    error = validator.is_valid_json_add_courier(request.json)
    if (type(error) == bool and not error) or len(error) != 0:
        return {
                   "validation_error": {
                       "couriers": error
                   }
               }, 400

    added_couriers = []
    for item in request.json["data"]:
        # Если пытаемся повторно кого-то добавить
        helper = db.session.query(Courier).get(item["courier_id"])
        if helper is not None:
            continue

        added_couriers.append({"id": item["courier_id"]})
        intervals: [IntervalTime] = DateTimeHelper.get_interval_time_list(item["working_hours"])
        courier = Courier(
            courier_id=item["courier_id"],
            courier_type=get_courier_type(item["courier_type"]),
            interval=intervals
        )
        db.session.add(courier)
        db.session.commit()

        regions = get_regions_list(item["regions"])
        for region in regions:
            helper = courier_region.insert().values(courier_id=courier.courier_id, region_id=region.region_id)
            db.session.execute(helper)
    db.session.commit()

    return {"couriers": added_couriers}, 201


@module.route('/couriers/<courier_id>', methods=["PATCH"])
def edit_courier(courier_id: str):
    if not courier_id:
        return Response(status=400)
    courier = db.session.query(Courier).get(courier_id)
    if courier is None or not validator.is_valid_json_edit_info_courier(request.json):
        return Response(status=400)

    json_ = request.json
    for key in json_:
        if key == "courier_type":
            courier.courier_type = get_courier_type(json_[key])
        if key == "working_hours":
            courier.interval = DateTimeHelper.get_interval_time_list(json_[key])
        if key == "regions":
            courier.regions = get_regions_list(json_[key])
    db.session.add(courier)
    db.session.commit()

    group = get_group_in_working(courier.group_order)

    if group is not None:
        orders = group.orders
        print(orders)
    # new_orders = findSuitableOrderInGroup(courier)



    return get_info_courier(courier), 200


@module.route('/orders', methods=["POST"])
def add_orders():
    error = validator.is_valid_json_add_orders(request.json)
    if type(error) == bool and not error:
        return {"validation_error": {}}, 400
    if len(error) != 0:
        return {
                   "validation_error": {
                       "orders": error
                   }
               }, 400

    added_orders = []
    for item in request.json["data"]:
        # Если пытаемся повторно кого-то добавить
        helper = db.session.query(Order).get(item["order_id"])
        if helper is not None:
            continue

        added_orders.append({"id": item["order_id"]})
        intervals: [IntervalTime] = DateTimeHelper.get_interval_time_list(item["delivery_hours"])
        region = get_region(item["region"])
        order = Order(
            order_id=item["order_id"],
            weight=item["weight"],
            region=region,
            interval=intervals,
            status=ReadinessStatus.new
        )
        db.session.add(order)
        db.session.commit()
    db.session.commit()
    return {"orders": added_orders}, 201


@module.route('/orders/assign', methods=["POST"])
def orders_assign():
    if not validator.is_valid_json_orders_assign(request.json):
        return {}, 400

    courier = db.session.query(Courier).get(request.json["courier_id"])
    if courier is None:
        return {}, 400

    # недоделанная выборка у курьера
    group = db.session.query(GroupOrder).filter(GroupOrder.courier == courier.courier_id).\
        filter(GroupOrder.status == ReadinessStatus.in_working).all()

    if len(group) == 0:
        orders = findSuitableOrders(courier)
        assign_time = datetime.datetime.now()
        ans = {
            "orders": list_order_to_list_id(orders),
            "assign_time": assign_time
        }
        for order in orders:
            order.status = ReadinessStatus.in_working
        group_order = GroupOrder(
            assign_time=assign_time,
            status=ReadinessStatus.in_working,
            courier=courier.courier_id,
            orders=orders
        )
        db.session.add(group_order)
        db.session.commit()
    else:
        orders = db.session.query(Order).filter(Order.group == group[0].id).\
            filter(Order.status == ReadinessStatus.in_working).all()
        ans = {
            "orders": list_order_to_list_id(orders),
            "assign_time": group[0].assign_time
        }

    return ans, 200


@module.route('/orders/complete', methods=["POST"])
def order_complete():

    data = request.json

    if not validator.is_valid_json_order_complete(request.json):
        return {}, 400

    order = db.session.query(Order).get(data["order_id"])
    # если заказ не был найден или не был распределен
    if order is None or order.group is None:
        return {}, 400

    group = db.session.query(GroupOrder).get(order.group)

    # если заказ был распределен на другого курьера
    if group.courier != data["courier_id"]:
        return {}, 400

    order.status = ReadinessStatus.ready
    order.finish_time = DateTimeHelper.get_datetime_by_iso_str(data["complete_time"])

    db.session.add(order)
    db.session.commit()

    if check_is_ready_group_order(group) is True:
        group.status = ReadinessStatus.ready

    db.session.add(order)
    db.session.commit()

    return {
        "order_id": order.order_id
    }, 200


# @module.route('/couriers/<courier_id>', methods=["GET"])
# def get_info_courier(courier_id):
#     return "GET INFO COURIER #"
