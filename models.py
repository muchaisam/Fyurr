from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False, unique=True)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=True)
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String, nullable=True)
    website_link = db.Column(db.String(), nullable=True)
    genres = db.Column(db.String(120))
    shows = db.relationship("Show", backref="venue", lazy=True)

    def __repr__(self) -> str:
       return f"<Venue: {self.name}>"


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False, unique=True)
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=True)
    website_link = db.Column(db.String(), nullable=True)
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String, nullable=True)
    shows = db.relationship("Show", backref="artist", lazy=True)

    def __repr__(self) -> str:
        return f"<Artist: {self.name}>"


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<Show: {self.artist_id} - {self.venue_id}>"