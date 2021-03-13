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


class Region(db.Model):
    __tablename__ = 'region'
    region_id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    courier = db.relationship("Courier", secondary=courier_region)


class Courier(db.Model):
    __tablename__ = 'courier'
    courier_id = db.Column(db.Integer(), primary_key=True, autoincrement=False)
    courier_type = db.Column(db.Enum(CourierType))
    regions = db.relationship("Region", secondary=courier_region)
    interval = db.relationship('IntervalTime', backref="courier")

    def __str__(self):
        return self.courier_type + " " + self.courier_type


class IntervalTime(db.Model):
    __tablename__ = 'interval_time'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time())
    finish_time = db.Column(db.Time())
    courier_id = db.Column(db.Integer(), db.ForeignKey(Courier.courier_id))




