# Import the dependencies
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
# Create engine to connect to the SQLite database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the database schema into ORM classes
Base = automap_base()

# Reflect tables from the database
Base.prepare(autoload_with=engine)
print(Base.classes.keys())

# Save references to the Measurement and Station tables
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################

# Initialize the Flask app
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

    # Get the most recent date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()

    # Calculate the date one year prior to the most recent date
    query_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query precipitation data for the last 12 months
    precip_data = session.query(Measurement.date, Measurement.prcp).\
        filter(func.strftime(Measurement.date) >= query_date).all()
    
    # Close session after query
    session.close()  

    # Convert query results to a list of dictionaries and append list
    all_precipitations = []
    for date, prcp in precip_data:
        precip_dict = {}
        precip_dict["date"] = date
        precip_dict["precipitation"] = prcp
        all_precipitations.append(precip_dict)

    return jsonify(all_precipitations)  


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all station names"""
    
    # Create session (link) from Python to connect to the database
    session = Session(engine)

    # Query all station names
    results = session.query(Station.name).all()

    # Close the session after query
    session.close()

    # Flatten list of tuples into a simple list
    all_stations = list(np.ravel(results))

    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():

    """Return JSON of temperature observations (tobs) for the most active station."""
    # Create our session (link) from Python to the database
    session = Session(engine)

    # Identify the most active station by count of observations
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]

    # Get the most recent date in the dataset
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]

    # Calculate the date one year prior
    query_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query temperature observations for the most active station
    tobs_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(func.strftime(Measurement.date) >= query_date).all()

    # Close the session after query
    session.close()

    # Format results into a list of dictionaries
    all_tobs = []
    for date, temp in tobs_data:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["temperature"] = temp
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)
   

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start, end=None):
    
    """Return min, avg, and max temperature for given date range."""
    # Create our session (link) from Python to the database
    session = Session(engine)

    # Retrieve earliest and latest dates in the dataset
    earliest_date = session.query(func.min(Measurement.date)).scalar()
    latest_date = session.query(func.max(Measurement.date)).scalar()

    # Validate the start date
    if start < earliest_date or start > latest_date:
        session.close()
        return jsonify({"error": f"Invalid start date. Date must be between {earliest_date} and {latest_date}"}), 400

    # Validate the end date if provided
    if end:
        if end < earliest_date or end > latest_date:
            session.close()
            return jsonify({"error": f"Invalid end date. Date must be between {earliest_date} and {latest_date}"}), 400
        if start > end:
            session.close()
            return jsonify({"error": "Invalid date range. Start date must be before end date."}), 400

    # Query min, avg, max temperatures from start date (if no end date)
    if not end:
        results = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start).all()
    
    # Query min, avg, max temperatures for start to end date
    else:
        results = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    
    # Close the session
    session.close()

    # Format the results into a dictionary
    temp_stats = {
        "Minimum Temperature": f"{results[0][0]:.2f} F",
        "Average Temperature": f"{results[0][1]:.2f} F",
        "Maximun Temperature": f"{results[0][2]:.2f} F"
    }

    return jsonify(temp_stats)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
    