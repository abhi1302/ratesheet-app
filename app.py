import os
import logging
import traceback
from flask import Flask, request, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this for production

# Configure database - using SQLite for simplicity
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ratesheet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Set up logging (this will log to console, which Render shows in the logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database model for ratesheet data
class Ratesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tap_out = db.Column(db.String(50), nullable=False)
    bu_plmn_code = db.Column(db.String(50))
    tax_included = db.Column(db.Boolean)
    tadig_plmn_code = db.Column(db.String(50))
    bearer_service_included = db.Column(db.Boolean)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    currency = db.Column(db.String(10))
    moc_local_call_rate = db.Column(db.Float)
    moc_local_call_interval = db.Column(db.Integer)
    # Add additional columns as required

# Allowed Excel file extensions
ALLOWED_EXTENSIONS = {'.xls', '.xlsx'}

def allowed_file(filename):
    """Verify that the uploaded file has a permitted extension."""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def load_to_db(df):
    """Load rows from the pandas DataFrame into the database."""
    try:
        for index, row in df.iterrows():
            record = Ratesheet(
                tap_out=row.get("TAP-OUT"),
                bu_plmn_code=row.get("BU PLMN Code"),
                tax_included=True if str(row.get("Tax included in the rate Yes/No")).strip().lower() == "yes" else False,
                tadig_plmn_code=row.get("TADIG PLMN Code"),
                bearer_service_included=True if str(row.get("Bearer Service included in Special IOT Yes/No")).strip().lower() == "yes" else False,
                start_date=pd.to_datetime(row.get("Start date")).date() if row.get("Start date") else None,
                end_date=pd.to_datetime(row.get("End date")).date() if row.get("End date") else None,
                currency=row.get("Currency"),
                moc_local_call_rate=row.get("MOC Call Local Call Rate/Value"),
                moc_local_call_interval=row.get("MOC Call Local Call Charging interval")
                # Add additional field mappings here…
            )
            db.session.add(record)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        # Log full stack trace for debugging purposes
        logger.error("Error while inserting records into DB: %s", traceback.format_exc())
        return False

@app.route('/upload', methods=['GET', 'POST'])
def upload_ratesheet():
    if request.method == 'POST':
        file = request.files.get('ratesheet')
        if file and allowed_file(file.filename):
            try:
                # Log the file upload attempt
                logger.info("Processing uploaded file: %s", file.filename)
                # Read the Excel file using pandas
                df = pd.read_excel(file)
                logger.info("Excel file read successfully. Rows: %d", len(df))
                # Insert DataFrame rows into the database
                if load_to_db(df):
                    flash("Ratesheet loaded successfully!", "success")
                    logger.info("Ratesheet data inserted into database successfully.")
                else:
                    flash("Ratesheet load failed. Please check error logs for details.", "danger")
                    logger.error("Ratesheet data insertion failed.")
            except Exception as e:
                error_details = traceback.format_exc()
                # Log the exception details
                logger.error("Failed to process file: %s", error_details)
                flash(f"Failed to process file: {str(e)}", "danger")
        else:
            flash("Invalid file type. Please upload an Excel file (.xls or .xlsx).", "danger")
        return redirect(url_for('upload_ratesheet'))
    return render_template('upload.html')

# Default route redirects to the upload page
@app.route('/')
def index():
    return redirect(url_for('upload_ratesheet'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
