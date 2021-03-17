from flask import Flask, Blueprint, request
from .models import Courier, CourierType, Region, db, courier_region, IntervalTime, Order, ReadinessStatus, GroupOrder
import datetime
from .Validation import Validation
from sqlalchemy import or_, and_

from jsonschema import validate, Draft7Validator, FormatChecker

module = Blueprint('delivery', __name__)

validator = Validation()


def get_courier_type(courier_type: str):
    if courier_type == 'foot':
        return CourierType.foot
    if courier_type == 'bike':
        return CourierType.bike
    if courier_type == 'car':
        return CourierType.car
    return None


def get_interval_by_string(s: str):
    if len(s) != 11 or s.find('-') != 5 or len(s.split('-')) != 2:
        return False
    helper = s.split('-')
    try:
        left = datetime.datetime.strptime(helper[0], "%H:%M").time()
        right = datetime.datetime.strptime(helper[1], "%H:%M").time()
        return left, right
    except ValueError:
        return False


def get_interval_time_list(arr) -> [IntervalTime]:
    intervals: [IntervalTime] = []
    for i in arr:
        interval = get_interval_by_string(i)
        if interval:
            intervals.append(IntervalTime(start_time=interval[0], finish_time=interval[1]))
    return intervals


def get_regions_list(arr) -> [Region]:
    regions: [Region] = []
    for region in arr:
        helper = db.session.query(Region).get(region)
        if helper is None:
            helper = Region(region_id=region)
            db.session.add(helper)
        regions.append(helper)
    return regions


def get_region(region: int) -> Region:
    helper = db.session.query(Region).get(region)
    if helper is None:
        helper = Region(region_id=region)
        db.session.add(helper)
    return helper


def get_list_id_regions(regions: [Region]) -> [int]:
    ids_regions = []
    for region in regions:
        ids_regions.append(region.region_id)
    return ids_regions


def get_list_str_working_hours(intervals: [IntervalTime]) -> [str]:
    list_intervals = []
    for interval in intervals:
        list_intervals.append(str(interval))
    return list_intervals


def get_info_courier(courier: Courier):
    return {
        "courier_id": courier.courier_id,
        "courier_type": courier.courier_type.name,
        "regions": get_list_id_regions(courier.regions),
        "working_hours": get_list_str_working_hours(courier.interval)
    }


# получить список интервалов для фильтра. если х = 1, то start < finish, -1 -- start > finish
def get_list_interval_for_filter(arr: [IntervalTime], x: int):
    intervals = []
    for interval in arr:
        if x == 1 and interval.start_time < interval.finish_time:
            intervals.append(interval)
        if x == -1 and interval.start_time > interval.finish_time:
            intervals.append(interval)
    return intervals


def findSuitableOrders(courier: Courier) -> [Order]:
    orders = []
    if len(courier.interval) == 0:
        return orders

    intervals_courier_norm = get_list_interval_for_filter(courier.interval, 1)
    intervals_courier_2 = get_list_interval_for_filter(courier.interval, -1)

    finish_day_time = datetime.datetime.strptime("23:59", "%H:%M").time()
    start_day_time = datetime.datetime.strptime("00:00", "%H:%M").time()

    regions_list = get_list_id_regions(courier.regions)
    orders = db.session.query(Order).filter(Order.status == ReadinessStatus.new).\
        filter(Order.weight <= courier.courier_type.value).\
        filter(Order.region.in_(regions_list)).join(Order.interval).\
        filter(or_(
                *[IntervalTime.start_time.between(x.start_time, x.finish_time) for x in intervals_courier_norm],
                *[IntervalTime.finish_time.between(x.start_time, x.finish_time) for x in intervals_courier_norm],
                *[IntervalTime.start_time.between(x.start_time, finish_day_time) for x in intervals_courier_2],
                *[IntervalTime.start_time.between(start_day_time, x.finish_time) for x in intervals_courier_2],
                *[IntervalTime.finish_time.between(start_day_time, x.finish_time) for x in intervals_courier_2],
                *[IntervalTime.finish_time.between(start_day_time, x.finish_time) for x in intervals_courier_2]
            )
    ).all()
    return orders


def list_order_to_list_id(orders: [Order]):
    ids = []
    for item in orders:
        ids.append({"id": item.order_id})
    return ids


@module.route('/', methods=['GET'])
def index():
    # получить всех курьеров из региона 23
    # helper = db.session.query(Region).filter_by(region_id=23).first().courier
    return "DASHA, PRIVET "  # + str(helper)


@module.route('/couriers', methods=['POST'])
def add_couriers():
    error = validator.is_valid_json_add_courier(request.json)
    if type(error) == bool and not error:
        return {"validation_error": {}}, 400
    if len(error) != 0:
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
        intervals: [IntervalTime] = get_interval_time_list(item["working_hours"])
        regions = get_regions_list(item["regions"])
        courier = Courier(
            courier_id=item["courier_id"],
            courier_type=get_courier_type(item["courier_type"]),
            interval=intervals
        )
        db.session.add(courier)
        db.session.commit()
        for region in regions:
            helper = courier_region.insert().values(courier_id=courier.courier_id, region_id=region.region_id)
            db.session.execute(helper)
    db.session.commit()
    return {"couriers": added_couriers}, 201


@module.route('/couriers/<courier_id>', methods=["PATCH"])
def edit_courier(courier_id: str):
    # TODO: посмотреть, как возвращать 400 без {}
    if not courier_id:
        return {}, 400
    courier = db.session.query(Courier).get(courier_id)
    if courier is None or not validator.is_valid_json_edit_info_courier(request.json):
        return {}, 400

    # TODO: ДОБАВИТЬ УДАЛЕНИЕ ИЗ СПИСКА ЗАКАЗОВ ТЕ ЗАКАЗЫ, КОТОРЫЕ ЧУВАК УЖЕ НЕ МОЖЕТ ДОСТАВИТЬ
    json_ = request.json
    for key in json_:
        if key == "courier_type":
            courier.courier_type = get_courier_type(json_[key])
        if key == "working_hours":
            courier.interval = get_interval_time_list(json_[key])
        if key == "regions":
            courier.regions = get_regions_list(json_[key])

    db.session.add(courier)
    db.session.commit()

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
        intervals: [IntervalTime] = get_interval_time_list(item["delivery_hours"])
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
    return "ORDER COMPLETE"


# @module.route('/couriers/<courier_id>', methods=["GET"])
# def get_info_courier(courier_id):
#     return "GET INFO COURIER #"
