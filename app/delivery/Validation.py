from datetime import datetime

from jsonschema import validate, Draft7Validator, FormatChecker


def is_interval_time(s: str) -> bool:
    if len(s) != 11 or s.find('-') != 5 or len(s.split('-')) != 2:
        return False
    helper = s.split('-')
    try:
        datetime.strptime(helper[0], "%H:%M").time()
        datetime.strptime(helper[1], "%H:%M").time()
        return True
    except ValueError:
        return False


def is_str_datetime_iso8601(date: str):
    try:
        _ = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f%z')
        return True
    except ValueError:
        return False


def is_positive_int(x: int) -> bool:
    if x <= 0:
        return False
    return True


def is_available_weight(x: float):
    if x > 50 or x < 0.01:
        return False
    return True


class Validation:
    def __init__(self):
        self.checker = FormatChecker()
        self.checker.checks("interval_time")(is_interval_time)
        self.checker.checks("positive_int")(is_positive_int)
        self.checker.checks("available_weight")(is_available_weight)
        self.checker.checks("format_iso_8601")(is_str_datetime_iso8601)

    def is_valid_courier(self, courier) -> bool:
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
            ],
            "additionalProperties": False
        }
        return Draft7Validator(schema, format_checker=self.checker).is_valid(courier)

    def is_valid_order(self, order) -> bool:
        schema = {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "format": "positive_int"},
                "weight": {"type": "number", "format": "available_weight"},
                "region": {"type": "integer", "format": "positive_int"},
                "delivery_hours": {"type": "array", "items": {"type": "string", "format": "interval_time"}},
            },
            "required": [
                "order_id",
                "weight",
                "region",
                "delivery_hours"
            ],
            "additionalProperties": False
        }
        return Draft7Validator(schema, format_checker=self.checker).is_valid(order)

    def is_valid_json_add_courier(self, json_) -> bool:
        not_valid = []
        if json_ is None or not ('data' in json_.keys()):
            return False
        for item in json_['data']:
            if not self.is_valid_courier(item):
                not_valid.append({"id": item['courier_id']})
        return not_valid

    def is_valid_json_edit_info_courier(self, courier) -> bool:
        schema = {
            "type": "object",
            "properties": {
                "courier_type": {"type": "string", "enum": ["foot", "bike", "car"]},
                "regions": {"type": "array", "items": {"type": "integer", "format": "positive_int"}},
                "working_hours": {"type": "array", "items": {"type": "string", "format": "interval_time"}},
            },
            "additionalProperties": False
        }
        return Draft7Validator(schema, format_checker=self.checker).is_valid(courier)

    def is_valid_json_add_orders(self, order) -> bool:
        not_valid = []
        if order is None or not ('data' in order.keys()):
            return False
        for item in order['data']:
            if not self.is_valid_order(item):
                not_valid.append({"id": item['order_id']})
        return not_valid

    def is_valid_json_orders_assign(self, json_):
        schema = {
            "type": "object",
            "properties": {
                "courier_id": {"type": "integer", "format": "positive_int"}
            },
            "required": [
                "courier_id"
            ],
            "additionalProperties": False
        }

        return Draft7Validator(schema, format_checker=self.checker).is_valid(json_)

    def is_valid_json_order_complete(self, json_):
        schema = {
            "type": "object",
            "properties": {
                "courier_id": {
                    "type": "integer",
                    "format": "positive_int"
                },
                "order_id": {
                    "type": "integer",
                    "format": "positive_int"
                },
                "complete_time": {
                    "type": "string",
                    "format": "format_iso_8601"
                }
            },
            "additionalProperties": False
        }

        return Draft7Validator(schema, format_checker=self.checker).is_valid(json_)








