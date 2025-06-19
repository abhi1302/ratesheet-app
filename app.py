import os
import logging
import pandas as pd
import numpy as np
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # Replace with your strong secret key

# Use the DATABASE_URL environment variable if available, otherwise update the connection string below.
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define the model to store each Excel row as a JSON object.
class RateSheet(db.Model):
    __tablename__ = 'ratesheet'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.JSON)

@app.before_first_request
def create_tables():
    logger.info("Creating database tables if not already created.")
    db.create_all()

def make_json_serializable(row_dict):
    """Converts Pandas Timestamps to isoformat strings and NaNs to None."""
    serializable_dict = {}
    for key, value in row_dict.items():
        if isinstance(value, pd.Timestamp):
            logger.debug(f"Converting Timestamp for key '{key}': {value}")
            serializable_dict[key] = value.isoformat()
        elif isinstance(value, float) and np.isnan(value):
            logger.debug(f"Converting NaN for key '{key}' to None")
            serializable_dict[key] = None
        else:
            serializable_dict[key] = value
    return serializable_dict

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get("file")
        if not file:
            logger.error("File upload attempted with no file provided.")
            flash("No file provided", "error")
            return redirect(request.url)
        try:
            # Read the Excel file into a pandas DataFrame.
            logger.info("Reading Excel file uploaded.")
            df = pd.read_excel(file)
            logger.debug(f"Excel file read successfully with shape {df.shape}")
            # Insert each row into the database after making it JSON serializable.
            for index, row in df.iterrows():
                row_dict = row.to_dict()
                row_serializable = make_json_serializable(row_dict)
                new_row = RateSheet(data=row_serializable)
                db.session.add(new_row)
                logger.debug(f"Added row {index} to session.")
            db.session.commit()
            logger.info("All rows committed to the database successfully.")
            flash("Excel file successfully loaded into DB", "success")
            return redirect(url_for("data_view"))
        except Exception as e:
            logger.exception("Error processing Excel file.")
            flash(f"Error processing file: {str(e)}", "error")
            return redirect(request.url)
    return render_template("index.html")

@app.route('/data', methods=["GET", "POST"])
def data_view():
    if request.method == "POST":
        try:
            record_id = request.form.get("record_id")
            record = RateSheet.query.filter_by(id=record_id).first()
            if record:
                updated_data = {}
                for key, value in request.form.items():
                    if key != "record_id":
                        updated_data[key] = value
                record.data = updated_data
                db.session.commit()
                logger.info(f"Record {record_id} updated successfully.")
                flash("Record updated", "success")
            else:
                logger.error(f"Record {record_id} not found for update.")
                flash("Record not found", "error")
        except Exception as e:
            logger.exception("Error updating record.")
            flash(f"Error updating record: {str(e)}", "error")
        return redirect(url_for("data_view"))
    
    records = RateSheet.query.all()
    logger.debug(f"Fetched {len(records)} records from the database.")
    return render_template("data.html", records=records)

if __name__ == '__main__':
    logger.info("Starting Flask application on host 0.0.0.0, port 5000 with debug=True")
    app.run(host='0.0.0.0', port=5000, debug=True)
