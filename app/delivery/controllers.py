from flask import Flask, Blueprint, request
from .models import Courier, CourierType, Region, db, courier_region, IntervalTime
import datetime
from jsonschema import validate, Draft6Validator
import time

# from ..database import db

module = Blueprint('delivery', __name__)


def isPositiveList(arr: [int]) -> bool:
    for x in arr:
        if x <= 0:
            return False
    return True


def isListStrIntervalTime(arr) -> bool:
    for item in arr:
        if not getIntervalByString(item):
            return False
    return True


def isValidCourierDescription(courier) -> bool:
    schema = {
        "type": "object",
        "properties": {
            "courier_id": {"type": "integer"},
            "courier_type": {"type": "string", "enum": ["foot", "bike", "car"]},
            "regions": {"type": "array", "items": {"type": "integer"}},
            "working_hours": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "courier_id",
            "courier_type",
            "regions",
            "working_hours"
        ]
    }
    if not Draft6Validator(schema).is_valid(courier):
        return False
    return courier["courier_id"] > 0 and isPositiveList(courier["regions"]) and isListStrIntervalTime(
        courier["working_hours"])


def isValidJsonAddCourier(json_):
    not_valid = []
    if json_ is None or not ('data' in json_.keys()):
        return False
    for item in json_['data']:
        if not isValidCourierDescription(item):
            not_valid.append({"id": item['courier_id']})
    return not_valid


def getCourierType(courier_type: str):
    if courier_type == 'foot':
        return CourierType.foot
    if courier_type == 'bike':
        return CourierType.bike
    if courier_type == 'car':
        return CourierType.car
    return None


def getIntervalByString(s: str):
    if len(s) != 11 or s.find('-') != 5 or len(s.split('-')) != 2:
        return False
    helper = s.split('-')
    try:
        left = datetime.datetime.strptime(helper[0], "%H:%M").time()
        right = datetime.datetime.strptime(helper[1], "%H:%M").time()
        return left, right
    except ValueError:
        return False


@module.route('/', methods=['GET'])
def index():
    # получить всех курьеров из региона 23
    # helper = db.session.query(Region).filter_by(region_id=23).first().courier
    return "DASHA, PRIVET "  # + str(helper)


@module.route('/couriers', methods=['POST'])
def add_couriers():
    error = isValidJsonAddCourier(request.json)
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

        intervals: [IntervalTime] = []
        for i in item["working_hours"]:
            interval = getIntervalByString(i)
            if interval:
                intervals.append(IntervalTime(start_time=interval[0], finish_time=interval[1]))
        regions = []
        for region in item["regions"]:
            helper = db.session.query(Region).get(region)
            if helper is None:
                helper = Region(region_id=region)
                db.session.add(helper)
            regions.append(helper)

        courier = Courier(
            courier_id=item["courier_id"],
            courier_type=getCourierType(item["courier_type"]),
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
def edit_courier(courier_id):
    return "EDIT COURIER #" + courier_id + "\n" + str(request.json)


@module.route('/orders', methods=["POST"])
def add_orders():
    return "ADD ORDERS\n" + str(request.json)


@module.route('/orders/assign', methods=["POST"])
def orders_assign():
    return "ORDERS ASSIGN"


@module.route('/orders/complete', methods=["POST"])
def order_complete():
    return "ORDER COMPLETE"


@module.route('/couriers/<courier_id>', methods=["GET"])
def get_info_courier(courier_id):
    return "GET INFO COURIER #" + courier_id
