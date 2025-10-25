from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class LocationHistory(db.Model):
    __tablename__ = "location_history"

    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    place_name = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)

    # One-to-many relationship: One location history can have multiple nearby places
    historical_places = db.relationship(
        "HistoricalPlace",
        backref="location",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<LocationHistory {self.place_name or 'Unknown'} ({self.latitude}, {self.longitude})>"


class HistoricalPlace(db.Model):
    __tablename__ = "historical_places"

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("location_history.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    distance_km = db.Column(db.Float)  # distance from the main location
    established_year = db.Column(db.String(10))
    country = db.Column(db.String(100))

    def __repr__(self):
        return f"<HistoricalPlace {self.name}>"
