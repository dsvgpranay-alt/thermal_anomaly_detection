from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Asset(db.Model):
    __tablename__ = "assets"
    asset_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    warning_limit_C = db.Column(db.Float, nullable=False)
    critical_limit_C = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc),nullable=False)
    inspections = db.relationship("Inspection",backref="asset",lazy=True,cascade="all, delete-orphan")

class Inspection(db.Model):
    __tablename__ = "inspections"
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer,db.ForeignKey("assets.asset_id"),nullable=False)
    timestamp = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc),nullable=False)
    max_temp_C = db.Column(db.Float, nullable=False)
    mean_temp_C = db.Column(db.Float, nullable=False)
    image_ref = db.Column(db.String(255))
    idempotency_key = db.Column(db.String(100),unique=True,nullable=False)
    created_at = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc),nullable=False)
    alert= db.relationship("Alert",backref="inspection",uselist=False,cascade="all, delete-orphan")

class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer,db.ForeignKey("inspections.id"),unique=True,nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    created_at = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc),nullable=False)
    acknowledged_by = db.Column(db.String(100), nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    acknowledgement_history = db.relationship("AlertAcknowledgement",backref="alert",lazy=True,cascade="all, delete-orphan")

class AlertAcknowledgement(db.Model):
    __tablename__ = "alert_acknowledgements"
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer,db.ForeignKey("alerts.id"),nullable=False)
    previous_status = db.Column(db.String(20), nullable=False)
    new_status = db.Column(db.String(20), nullable=False)
    acknowledged_by = db.Column(db.String(100), nullable=False)
    acknowledged_at = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc),nullable=False)