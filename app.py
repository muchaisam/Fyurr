import logging
from datetime import datetime
from logging import FileHandler, Formatter
import string
import babel
import dateutil.parser
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_moment import Moment

from forms import *
from models import db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

# connect to a local postgresql database
migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  # Show Recent Listed Artists and Venues 
  MAX_ITEMS = 10
  artists = Artist.query.order_by(db.desc(Artist.id)).limit(MAX_ITEMS).all()
  venues = Venue.query.order_by(db.desc(Venue.id)).limit(MAX_ITEMS).all()
  return render_template('pages/home.html', artists=artists, venues=venues)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  cities = []
  venues = Venue.query.all()
  for venue in venues:
    if venue.city not in cities:
      cities.append(venue.city)
      data.append({
        'city': venue.city,
        'state': venue.state,
        'venues': [
          {
            'id': item.id,
            'name': item.name,
            'num_upcoming_shows': len(item.shows)
          }
          for item in venues 
          if item.city == venue.city
        ]
      })
  
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={"count": 0, "data": []}
  search_term=request.form.get('search_term', '')
  # Implement searching by city and state
  terms = search_term.strip().split(',')
  if len(terms) == 2:
    city , state = terms
    city = city.strip()
    state = state.strip()
    venues = Venue.query.filter(Venue.city.ilike(f'%{city}%'), Venue.state.ilike(f'%{state}%'))
    response['city'] = city
    response['state'] = state
  else:
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))
  response["count"] = venues.count()
  for venue in venues:
    response["data"].append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': len(venue.shows)
    })
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # replace with real venue data from the venues table, using venue_id
  
  venue = Venue.query.get(venue_id)

  past_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()   
  past_shows = []
  for show in past_shows_query:
    past_shows.append(
      {
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
      }
    )
  
  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()   
  upcoming_shows = []
  for show in upcoming_shows_query:
    upcoming_shows.append(
      {
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
      } 
    )
  
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  } 
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # insert form data as a new Venue record in the db, instead
  # modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  try:
    form = VenueForm(request.form)
      
    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data.strip()
    address = form.address.data.strip()
    phone = form.phone.data.strip()
    image_link = form.image_link.data.strip()
    facebook_link = form.facebook_link.data.strip()
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data.strip()
    website = form.website_link.data.strip()
    genres = ",".join(form.genres.data) # need to transform genres to a string before insertion
  
    for char in string.ascii_letters:
      if char in phone:
        raise Exception("Invalid phone Number!!") # we don't want letters in phone numbers
    
    if phone ==  '':
      raise Exception("Invalid phone Number!!") # we don't need an empty phone number
    
    venue = Venue(
      name=name, 
      state=state,
      city=city, 
      address=address,
      phone=phone,
      image_link=image_link,
      facebook_link=facebook_link,
      seeking_talent=seeking_talent,
      seeking_description=seeking_description,
      website_link=website,
      genres=genres
    )
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    for show in venue.shows:
      db.session.delete(show)
    
    db.session.delete(venue)
    db.session.commit()
    flash(venue.name + ' is successfully deleted.')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' is not deleted!!!')
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={"count": 0, "data": []}
  search_term=request.form.get('search_term', '')
  # Implement searching by city and state
  terms = search_term.strip().split(',')
  if len(terms) == 2:
    city , state = terms
    city = city.strip()
    state = state.strip()
    artists = Artist.query.filter(Artist.city.ilike(f'%{city}%'), Artist.state.ilike(f'%{state}%'))
    response['city'] = city
    response['state'] = state
  else:
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
  response["count"] = artists.count()
  for artist in artists:
    response["data"].append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': len(artist.shows)
    })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get(artist_id)

  past_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()   
  past_shows = []
  for show in past_shows_query:
    past_shows.append(
      {
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
      }
    )
  
  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()   
  upcoming_shows = []
  for show in upcoming_shows_query:
    upcoming_shows.append(
      {
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
      }
    )
  
  data ={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # populate form with fields from artist with ID <artist_id>
  artist = Artist.query.get(artist_id)
  form = ArtistForm()
  # form.genres.populate_obj(artist.genres.split(","))
  form.genres.default = artist.genres.split(",")
  form.name.default = artist.name
  form.city.default = artist.city
  form.state.default = artist.state
  form.phone.default = artist.phone
  form.facebook_link.default = artist.facebook_link
  form.website_link.default = artist.website_link
  form.image_link.default = artist.image_link
  form.seeking_venue.default = artist.seeking_venue
  form.seeking_description.default = artist.seeking_description
  form.process()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist = Artist.query.get(artist_id)
    form = ArtistForm(request.form)

    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.facebook_link = form.facebook_link.data
    artist.website_link = form.website_link.data
    artist.image_link = form.image_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    artist.genres = ",".join(form.genres.data)

    db.session.commit()
    flash('ARTIST ' + request.form['name'] + ' WAS SUCCESSFULLY UPDATED!')
  except:
    db.session.rollback()
    flash('FAILED TO UPDATE' + request.form['name'] + ' DATA !!')
  
  return redirect(url_for('show_artist', artist_id=artist.id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  # populate form with values from venue with ID <venue_id>
  form.genres.default = venue.genres.split(",")
  form.name.default = venue.name
  form.city.default = venue.city
  form.state.default = venue.state
  form.address.default = venue.address
  form.phone.default = venue.phone
  form.facebook_link.default = venue.facebook_link
  form.website_link.default = venue.website_link
  form.image_link.default = venue.image_link
  form.seeking_talent.default = venue.seeking_talent
  form.seeking_description.default = venue.seeking_description
  form.process()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    venue = Venue.query.get(venue_id)
    form = VenueForm(request.form)

    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.address = form.address.data
    venue.facebook_link = form.facebook_link.data
    venue.website_link = form.website_link.data
    venue.image_link = form.image_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
    venue.genres = ",".join(form.genres.data)

    db.session.commit()
    flash('VENUE ' + request.form['name'] + ' WAS SUCCESSFULLY UPDATED!')
  except:
    db.session.rollback()
    flash('FAILED TO UPDATE' + request.form['name'] + ' DATA !!')

  return redirect(url_for('show_venue', venue_id=venue.id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # insert form data as a new Venue record in the db, instead
  # modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  try:
    form = ArtistForm(request.form)
  
    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data.strip()
    phone = form.phone.data.strip()
    image_link = form.image_link.data.strip()
    facebook_link = form.facebook_link.data.strip()
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data.strip()
    website = form.website_link.data.strip()
    genres = ",".join(form.genres.data) 
    
    # a phone number must not contain aphabetic characters but 
    for char in string.ascii_letters:
      if char in phone:
        raise Exception("Invalid phone Number!!")
    
    if phone ==  '':
      raise Exception("Invalid phone Number!!") # we don't need an empty phone number
      
    artist = Artist(
      name=name,
      city=city,
      state=state,
      phone=phone,
      image_link=image_link,
      facebook_link=facebook_link,
      seeking_venue=seeking_venue,
      seeking_description=seeking_description,
      website_link=website,
      genres=genres
    )
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # replace with real venues data.
  data = []
  shows = Show.query.all()
  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  # flash('Show was successfully listed!')
  # on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  try:
    form = ShowForm(request.form)

    artist_id = int(form.artist_id.data)
    venue_id = int(form.venue_id.data)
    start_time = form.start_time.data
    show = Show(
      start_time=start_time,
      artist_id=artist_id,
      venue_id=venue_id
    )
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''