# Import the dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station



#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"<h1>Welcome to the Hawaii Climate API!</h1>"
        f"<b>Available Routes:</b><br/>"
        f"/api/v1.0/precipitation - Last 12 months of precipitation data<br/>"
        f"/api/v1.0/stations - List of weather stations<br/>"
        f"/api/v1.0/tobs - Temperature observations for the most active station<br/>"
        f"/api/v1.0/&lt;start&gt; - Min, Avg, Max temps from start date<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt; - Min, Avg, Max temps for date range<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return a list of precipitation data with date and precipitation values"""

    # Create session (link) from Python to the DB
    session = Session(engine)

    # Find the most recent date
    most_recent_date = session.query(func.max(Measurement.date)).scalar()

    # Convert to datetime & calculate 1 year ago
    query_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query precipitation data for the last 12 months
    precip_data = session.query(Measurement.date, Measurement.prcp).\
        filter(func.strftime(Measurement.date) >= query_date).all()
    
    # Close session after query
    session.close()  

    # Convert query results to a list of dictionaries and append list
    all_precipitations = []
    for date, prcp in results:
        precip_dict = {}
        precip_dict["date"] = date
        precip_dict["precipitation"] = prcp
        all_precipitations.append(precip_dict)

    return jsonify(all_precipitations)  


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all station names"""
    
    # Create session (link) from Python to the DB
    session = Session(engine)

    # Query all station names
    results = session.query(Station.station).all()

    # Close the session after query
    session.close()

    # Convert list of tuples into a normal list
    all_stations = list(np.ravel(results))

    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    """Return JSON of temperature observations (tobs) for the most active station."""
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Find the most active station
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]

    # Find the most recent date & calculate last 12 months
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    query_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query temperature observations for the most active station
    tobs_data = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.station == most_active_station).\
    filter(func.strftime(Measurement.date) >= query_date).all()

    session.close()

    # Convert to a list of dictionaries and append
    all_tobs = []
    for date, temp in tobs_data:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["temperature"] = temp
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)