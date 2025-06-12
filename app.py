import os
import logging
import traceback
from datetime import datetime
from flask import Flask, request, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)
# Read secret and DB URI from environment variables
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')

db_uri = os.environ.get('DATABASE_URL')
if not db_uri:
    raise Exception("DATABASE_URL environment variable not found!")
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)

# Helper functions for converting values
def parse_bool(value):
    try:
        val = str(value).strip().lower()
    except Exception:
        return False
    return val in ('yes', 'true', '1', 't')

def parse_date(value):
    try:
        # Adjust the format if needed – here we let pandas parse
        return pd.to_datetime(value).date()
    except Exception:
        return None

def parse_float(value):
    try:
        return float(value)
    except Exception:
        return None

def parse_int(value):
    try:
        return int(float(value))  # Sometimes the value comes as float (e.g., 1.0)
    except Exception:
        return None

# Define the database model based on the 29 columns from the attached sheet.
class Ratesheet(db.Model):
    __tablename__ = 'ratesheet'
    id = db.Column(db.Integer, primary_key=True)
    tap_out = db.Column(db.String(50), nullable=False)  # Required field
    bu_plmn_code = db.Column(db.String(50))
    tax_included = db.Column(db.Boolean)  # "Tax included in the rate Yes/No"
    tadig_plmn_code = db.Column(db.String(50))
    bearer_service_included = db.Column(db.Boolean)  # "Bearer Service included in Special IOT Yes/No"
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    currency = db.Column(db.String(10))
    moc_local_call_rate = db.Column(db.Float)      # "MOC Call Local Call Rate/Value"
    moc_local_call_interval = db.Column(db.Integer)  # "MOC Call Local Call Charging interval"
    moc_call_back_home_rate = db.Column(db.Float)    # "MOC Call Call Back Home Rate/Value"
    moc_call_back_home_interval = db.Column(db.Integer)  # "MOC Call Call Back Home Charging interval"
    moc_rest_world_rate = db.Column(db.Float)        # "MOC Call Rest of the world Rate/Value"
    moc_rest_world_interval = db.Column(db.Integer)    # "MOC Call Rest of the world Charging interval"
    moc_premium_rate = db.Column(db.String(50))      # "MOC Call Premium numbers Rate/Value"
    moc_premium_interval = db.Column(db.String(50))  # "MOC Call Premium numbers Charging interval"
    moc_special_rate = db.Column(db.String(50))        # "MOC Call Special numbers Rate/Value"
    moc_special_interval = db.Column(db.String(50))    # "MOC Call Special numbers Charging interval"
    moc_satellite_rate = db.Column(db.String(50))      # "MOC Call Satellite Rate/Value"
    moc_satellite_interval = db.Column(db.String(50))  # "MOC Call Satellite Charging interval"
    mtc_call_rate = db.Column(db.Float)                # "MTC Call Rate/Value"
    mtc_call_interval = db.Column(db.Integer)          # "MTC Call Charging interval"
    mo_sms_rate = db.Column(db.Float)                  # "MO-SMS Rate/Value"
    gprs_rate_mb_rate = db.Column(db.Float)            # "GPRS Rate MB Rate/Value"
    gprs_rate_mb_interval = db.Column(db.String(50))   # "GPRS Rate MB Charging interval"
    volte_rate_mb_rate = db.Column(db.Float)           # "VoLTE Rate MB Rate/Value"
    volte_rate_mb_interval = db.Column(db.String(50))  # "VoLTE Rate MB Charging interval"
    tax_applicable = db.Column(db.Boolean)             # "Tax applicable Yes/No"
    tax_value = db.Column(db.Float)                    # "Tax applicable Tax Value"

# Create tables so that they're available for Gunicorn and in production
with app.app_context():
    db.create_all()

# Allowed file extensions for Excel uploads
ALLOWED_EXTENSIONS = {'.xls', '.xlsx'}

def allowed_file(filename):
    """Verify that the uploaded file has a permitted extension."""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def load_to_db(df):
    """Transform the DataFrame rows and insert into the database.
       The DataFrame is expected to have columns as per the attached sheet.
    """
    skipped_rows = []
    try:
        for idx, row in df.iterrows():
            # Validate that required field "TAP-OUT" exists and is not empty
            tap_value = row.get("TAP-OUT")
            if pd.isna(tap_value) or str(tap_value).strip() == "":
                logger.error("Skipping row %d: missing TAP-OUT value.", idx)
                skipped_rows.append(idx)
                continue

            record = Ratesheet(
                tap_out = str(tap_value).strip(),
                bu_plmn_code = str(row.get("BU PLMN Code")).strip() if not pd.isna(row.get("BU PLMN Code")) else None,
                tax_included = parse_bool(row.get("Tax included in the rate Yes/No")),
                tadig_plmn_code = str(row.get("TADIG PLMN Code")).strip() if not pd.isna(row.get("TADIG PLMN Code")) else None,
                bearer_service_included = parse_bool(row.get("Bearer Service included in Special IOT Yes/No")),
                start_date = parse_date(row.get("Start date")),
                end_date = parse_date(row.get("End date")),
                currency = str(row.get("Currency")).strip() if not pd.isna(row.get("Currency")) else None,
                moc_local_call_rate = parse_float(row.get("MOC Call Local Call Rate/Value")),
                moc_local_call_interval = parse_int(row.get("MOC Call Local Call Charging interval")),
                moc_call_back_home_rate = parse_float(row.get("MOC Call Call Back Home Rate/Value")),
                moc_call_back_home_interval = parse_int(row.get("MOC Call Call Back Home Charging interval")),
                moc_rest_world_rate = parse_float(row.get("MOC Call Rest of the world Rate/Value")),
                moc_rest_world_interval = parse_int(row.get("MOC Call Rest of the world Charging interval")),
                moc_premium_rate = str(row.get("MOC Call Premium numbers Rate/Value")).strip() if not pd.isna(row.get("MOC Call Premium numbers Rate/Value")) else None,
                moc_premium_interval = str(row.get("MOC Call Premium numbers Charging interval")).strip() if not pd.isna(row.get("MOC Call Premium numbers Charging interval")) else None,
                moc_special_rate = str(row.get("MOC Call Special numbers Rate/Value")).strip() if not pd.isna(row.get("MOC Call Special numbers Rate/Value")) else None,
                moc_special_interval = str(row.get("MOC Call Special numbers Charging interval")).strip() if not pd.isna(row.get("MOC Call Special numbers Charging interval")) else None,
                moc_satellite_rate = str(row.get("MOC Call Satellite Rate/Value")).strip() if not pd.isna(row.get("MOC Call Satellite Rate/Value")) else None,
                moc_satellite_interval = str(row.get("MOC Call Satellite Charging interval")).strip() if not pd.isna(row.get("MOC Call Satellite Charging interval")) else None,
                mtc_call_rate = parse_float(row.get("MTC Call Rate/Value")),
                mtc_call_interval = parse_int(row.get("MTC Call Charging interval")),
                mo_sms_rate = parse_float(row.get("MO-SMS Rate/Value")),
                gprs_rate_mb_rate = parse_float(row.get("GPRS Rate MB Rate/Value")),
                gprs_rate_mb_interval = str(row.get("GPRS Rate MB Charging interval")).strip() if not pd.isna(row.get("GPRS Rate MB Charging interval")) else None,
                volte_rate_mb_rate = parse_float(row.get("VoLTE Rate MB Rate/Value")),
                volte_rate_mb_interval = str(row.get("VoLTE Rate MB Charging interval")).strip() if not pd.isna(row.get("VoLTE Rate MB Charging interval")) else None,
                tax_applicable = parse_bool(row.get("Tax applicable Yes/No")),
                tax_value = parse_float(row.get("Tax applicable Tax Value"))
            )
            db.session.add(record)
        db.session.commit()
        if skipped_rows:
            logger.error("Skipped rows due to missing TAP-OUT: %s", skipped_rows)
        return True
    except Exception as e:
        db.session.rollback()
        logger.error("Error while inserting records into DB: %s", traceback.format_exc())
        return False

@app.route('/upload', methods=['GET', 'POST'])
def upload_ratesheet():
    if request.method == 'POST':
        file = request.files.get('ratesheet')
        if file and allowed_file(file.filename):
            try:
                logger.info("Processing uploaded file: %s", file.filename)
                # Read the file without header and then transpose,
                # because our attached sheet has headers vertically.
                df_raw = pd.read_excel(file, header=None)
                df_transposed = df_raw.transpose()
                # Use the first row of the transposed DataFrame as the header (strip whitespace)
                df_transposed.columns = df_transposed.iloc[0].str.strip()
                df = df_transposed[1:].reset_index(drop=True)
                
                # Validate that required column exists
                if "TAP-OUT" not in df.columns:
                    msg = "Expected column 'TAP-OUT' not found in the uploaded Excel file."
                    logger.error(msg)
                    flash(msg, "danger")
                    return redirect(url_for('upload_ratesheet'))
                
                logger.info("Excel file read successfully. Rows: %d", len(df))
                if load_to_db(df):
                    flash("Ratesheet loaded successfully!", "success")
                    logger.info("Ratesheet data inserted into database successfully.")
                else:
                    flash("Ratesheet load failed. Please check error logs for details.", "danger")
                    logger.error("Ratesheet data insertion failed.")
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error("Failed to process file: %s", error_details)
                flash(f"Failed to process file: {str(e)}", "danger")
        else:
            flash("Invalid file type. Please upload an Excel file (.xls or .xlsx).", "danger")
        return redirect(url_for('upload_ratesheet'))
    return render_template('upload.html')

@app.route('/')
def index():
    return redirect(url_for('upload_ratesheet'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
