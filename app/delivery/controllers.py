from flask import Flask, Blueprint, request
from .models import Courier, CourierType, Region, db, courier_region, IntervalTime
import datetime
from jsonschema import validate, Draft7Validator, FormatChecker

module = Blueprint('delivery', __name__)


def is_interval_time(s: str) -> bool:
    if len(s) != 11 or s.find('-') != 5 or len(s.split('-')) != 2:
        return False
    helper = s.split('-')
    try:
        datetime.datetime.strptime(helper[0], "%H:%M").time()
        datetime.datetime.strptime(helper[1], "%H:%M").time()
        return True
    except ValueError:
        return False


def is_positive_int(x) -> bool:
    if x <= 0:
        return False
    return True


checker = FormatChecker()
checker.checks("interval_time")(is_interval_time)
checker.checks("positive_int")(is_positive_int)


def is_valid_courier(courier) -> bool:
    schema = {
        "type": "object",
        "properties": {
            "courier_id": {"type": "integer", "format": "positive_int"},
            "courier_type": {"type": "string", "enum": ["foot", "bike", "car"]},
            "regions": {"type": "array", "items": {"type": "integer", "format": "positive_int"}},
            "working_hours": {"type": "array", "items": {"type": "string", "format": "interval_time"}},
        },
        "required": [
            "courier_id",
            "courier_type",
            "regions",
            "working_hours"
        ]
    }
    if not Draft7Validator(schema, format_checker=checker).is_valid(courier):
        return False
    return True


def is_valid_json_add_courier(json_):
    not_valid = []
    if json_ is None or not ('data' in json_.keys()):
        return False
    for item in json_['data']:
        if not is_valid_courier(item):
            not_valid.append({"id": item['courier_id']})
    return not_valid


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


def is_valid_json_edit_info_courier(courier) -> bool:
    schema = {
        "type": "object",
        "properties": {
            "courier_type": {"type": "string", "enum": ["foot", "bike", "car"]},
            "regions": {"type": "array", "items": {"type": "integer", "format": "positive_int"}},
            "working_hours": {"type": "array", "items": {"type": "string", "format": "interval_time"}},
        },
        "additionalProperties": False
    }

    if not Draft7Validator(schema, format_checker=checker).is_valid(courier):
        return False
    return True


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


@module.route('/', methods=['GET'])
def index():
    # получить всех курьеров из региона 23
    # helper = db.session.query(Region).filter_by(region_id=23).first().courier
    return "DASHA, PRIVET "  # + str(helper)


@module.route('/couriers', methods=['POST'])
def add_couriers():
    error = is_valid_json_add_courier(request.json)
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
    if courier is None or not is_valid_json_edit_info_courier(request.json):
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
    return "ADD ORDERS\n" + str(request.json)


@module.route('/orders/assign', methods=["POST"])
def orders_assign():
    return "ORDERS ASSIGN"


@module.route('/orders/complete', methods=["POST"])
def order_complete():
    return "ORDER COMPLETE"


# @module.route('/couriers/<courier_id>', methods=["GET"])
# def get_info_courier(courier_id):
#     return "GET INFO COURIER #"
