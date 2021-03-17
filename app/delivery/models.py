from ..database import db
from flask_sqlalchemy import SQLAlchemy
import enum


class CourierType(enum.Enum):
    foot = 10
    bike = 15
    car = 50


class ReadinessStatus(enum.Enum):
    new = 1
    in_working = 2
    ready = 3


courier_region = db.Table('courier_region',
                          db.Column("courier_id", db.Integer, db.ForeignKey("courier.courier_id")),
                          db.Column("region_id", db.Integer, db.ForeignKey("region.region_id"))
)


class Courier(db.Model):
    __tablename__ = 'courier'
    courier_id = db.Column(db.Integer(), primary_key=True, autoincrement=False)
    courier_type = db.Column(db.Enum(CourierType))
    regions = db.relationship("Region", secondary=courier_region)
    interval = db.relationship('IntervalTime', backref="courier")
    group_order = db.relationship('GroupOrder', backref="courier_groups_orders")


class Region(db.Model):
    __tablename__ = 'region'
    region_id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    courier = db.relationship("Courier", secondary=courier_region)
    order = db.relationship("Order", backref="region_order")

    def __str__(self):
        return str(self.region_id)


class GroupOrder(db.Model):
    __tablename__ = "group_order"
    id = db.Column(db.Integer(), primary_key=True)
    assign_time = db.Column(db.DateTime())
    status = db.Column(db.Enum(ReadinessStatus))
    courier = db.Column(db.Integer(), db.ForeignKey(Courier.courier_id))
    orders = db.relationship("Order", backref="group_order")


class Order(db.Model):
    __tablename__ = "order"
    order_id = db.Column(db.Integer(), primary_key=True, autoincrement=False)
    weight = db.Column(db.Float())
    region = db.Column(db.Integer(), db.ForeignKey(Region.region_id))
    interval = db.relationship('IntervalTime', backref="order")

    status = db.Column(db.Enum(ReadinessStatus))
    finish_time = db.Column(db.DateTime())
    group = db.Column(db.Integer(), db.ForeignKey(GroupOrder.id))


class IntervalTime(db.Model):
    __tablename__ = 'interval_time'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time())
    finish_time = db.Column(db.Time())
    courier_id = db.Column(db.Integer(), db.ForeignKey(Courier.courier_id))
    order_id = db.Column(db.Integer(), db.ForeignKey(Order.order_id))

    def __str__(self):
        start = self.start_time.strftime("%H:%M")
        finish = self.finish_time.strftime("%H:%M")
        return start + ":" + finish




