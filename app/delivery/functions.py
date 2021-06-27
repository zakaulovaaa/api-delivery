from .models import Courier, CourierType, Region, db, courier_region, IntervalTime, Order, ReadinessStatus, GroupOrder
import datetime
from .DateTimeHelper import DateTimeHelper
from sqlalchemy import or_


def get_courier_type(courier_type: str):
    if courier_type == 'foot':
        return CourierType.foot
    if courier_type == 'bike':
        return CourierType.bike
    if courier_type == 'car':
        return CourierType.car
    return None


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


def get_info_courier(courier: Courier):
    return {
        "courier_id": courier.courier_id,
        "courier_type": courier.courier_type.name,
        "regions": get_list_id_regions(courier.regions),
        "working_hours": DateTimeHelper.get_list_str_working_hours(courier.interval)
    }


def getQueryOrdersByInterval(interval: IntervalTime, query):
    intervals_courier_norm = DateTimeHelper.get_list_interval_for_filter(interval, 1)
    intervals_courier_2 = DateTimeHelper.get_list_interval_for_filter(interval, -1)

    finish_day_time = datetime.datetime.strptime("23:59", "%H:%M").time()
    start_day_time = datetime.datetime.strptime("00:00", "%H:%M").time()

    query = query.filter(or_(
        *[IntervalTime.start_time.between(x.start_time, x.finish_time) for x in intervals_courier_norm],
        *[IntervalTime.finish_time.between(x.start_time, x.finish_time) for x in intervals_courier_norm],
        *[IntervalTime.start_time.between(x.start_time, finish_day_time) for x in intervals_courier_2],
        *[IntervalTime.start_time.between(start_day_time, x.finish_time) for x in intervals_courier_2],
        *[IntervalTime.finish_time.between(start_day_time, x.finish_time) for x in intervals_courier_2],
        *[IntervalTime.finish_time.between(start_day_time, x.finish_time) for x in intervals_courier_2]
    ))

    return query


def getQueryOrdersByStatusNew(query):
    query = query.filter(Order.status == ReadinessStatus.new)
    return query


def getQueryOrdersByWeight(query, weight):
    return query.filter()


def getQuerySuitableOrders(courier: Courier):
    orders = []
    if len(courier.interval) == 0:
        return orders

    intervals_courier_norm = DateTimeHelper.get_list_interval_for_filter(courier.interval, 1)
    intervals_courier_2 = DateTimeHelper.get_list_interval_for_filter(courier.interval, -1)

    finish_day_time = datetime.datetime.strptime("23:59", "%H:%M").time()
    start_day_time = datetime.datetime.strptime("00:00", "%H:%M").time()

    regions_list = get_list_id_regions(courier.regions)
    orders = db.session.query(Order).filter(Order.status == ReadinessStatus.new). \
        filter(Order.weight <= courier.courier_type.value). \
        filter(Order.region.in_(regions_list)).join(Order.interval). \
        filter(or_(
        *[IntervalTime.start_time.between(x.start_time, x.finish_time) for x in intervals_courier_norm],
        *[IntervalTime.finish_time.between(x.start_time, x.finish_time) for x in intervals_courier_norm],
        *[IntervalTime.start_time.between(x.start_time, finish_day_time) for x in intervals_courier_2],
        *[IntervalTime.start_time.between(start_day_time, x.finish_time) for x in intervals_courier_2],
        *[IntervalTime.finish_time.between(start_day_time, x.finish_time) for x in intervals_courier_2],
        *[IntervalTime.finish_time.between(start_day_time, x.finish_time) for x in intervals_courier_2]
    ))
    return orders


def findSuitableOrders(courier: Courier) -> [Order]:
    query = getQuerySuitableOrders(courier)
    return query.all()


def list_order_to_list_id(orders: [Order]):
    ids = []
    for item in orders:
        ids.append({"id": item.order_id})
    return ids


def check_is_ready_group_order(group: GroupOrder):
    orders = group.orders
    for order in orders:
        if order.status == ReadinessStatus.in_working:
            return False
    return True


def findSuitableOrderInGroup(courier: Courier, groupId: int):
    query = getQuerySuitableOrders(courier).filter(Order.group == groupId)
    return query.all()


def get_group_in_working(groups: [GroupOrder]):
    for group in groups:
        if group.status == ReadinessStatus.in_working:
            return group
    return None
