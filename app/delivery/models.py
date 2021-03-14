from ..database import db
from flask_sqlalchemy import SQLAlchemy
import enum


class CourierType(enum.Enum):
    foot = 1
    bike = 2
    car = 3


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

    def __str__(self):
        interval = ""
        for i in self.interval:
            interval += str(i) + ", "
        regions = ""
        for i in self.regions:
            regions += str(i) + ", "

        return "id: " + str(self.courier_id) + "||| type: " + str(self.courier_type.name) + "||| regions: " + regions + \
               "||| intervals: " + interval


class Region(db.Model):
    __tablename__ = 'region'
    region_id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    courier = db.relationship("Courier", secondary=courier_region)
    order = db.relationship("Order", backref="region_order")

    def __str__(self):
        return str(self.region_id)


class Order(db.Model):
    __tablename__ = "order"
    order_id = db.Column(db.Integer(), primary_key=True, autoincrement=False)
    weight = db.Column(db.Float())
    region = db.Column(db.Integer(), db.ForeignKey(Region.region_id))
    interval = db.relationship('IntervalTime', backref="order")


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




