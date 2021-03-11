from ..database import db
from flask_sqlalchemy import SQLAlchemy
import enum


class CourierType(enum.Enum):
    foot = 1
    bike = 2
    car = 3


class Region(db.Model):
    __tablename__ = 'region'
    region_id = db.Column(db.Integer, primary_key=True, autoincrement=False)


class Courier(db.Model):
    __tablename__ = 'courier'
    courier_id = db.Column(db.Integer(), primary_key=True, autoincrement=False)
    courier_type = db.Column(db.Enum(CourierType))
    interval = db.relationship('IntervalTime', backref="courier")

    def __str__(self):
        return self.courier_type + " " + self.courier_type


class IntervalTime(db.Model):
    __tablename__ = 'interval_time'
    id = db.Column(db.Integer, primary_key=True)
    interval = db.Column(db.Interval)
    courier_id = db.Column(db.Integer(), db.ForeignKey(Courier.courier_id))


courier_region = db.Table('courier_region',
                          db.Column("courier_id", db.Integer, db.ForeignKey(Courier.courier_id)),
                          db.Column("region_id", db.Integer, db.ForeignKey(Region.region_id))
)

