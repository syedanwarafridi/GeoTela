from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class LocationHistory(db.Model):
    __tablename__ = "location_history"

    id = db.Column(db.Integer, primary_key=True)
    place_name = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)

    def __repr__(self):
        return f"<LocationHistory {self.place_name or 'Unknown'}>"


class HistoricalPlace(db.Model):
    __tablename__ = "historical_places"

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer)  # just store the LocationHistory id manually
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f"<HistoricalPlace {self.name}>"
