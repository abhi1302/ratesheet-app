import os
import logging
import traceback
from datetime import datetime
from flask import Flask, request, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)

# Read SECRET_KEY and DATABASE_URL from environment variables.
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-for-dev')
db_uri = os.environ.get('DATABASE_URL')
if not db_uri:
    raise Exception("DATABASE_URL environment variable not found!")
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)

# Helper conversion functions
def parse_bool(value):
    try:
        val = str(value).strip().lower()
    except Exception:
        return False
    return val in ('yes', 'true', '1', 't')

def parse_date(value):
    try:
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
        return int(float(value))
    except Exception:
        return None

# Database model – using column names exactly as in the Excel headers.
class Ratesheet(db.Model):
    __tablename__ = 'ratesheet'
    id = db.Column(db.Integer, primary_key=True)
    tap_out = db.Column(db.String(50), nullable=False)  # from header: TAP-OUT
    bu_plmn_code = db.Column(db.String(50))             # BU PLMN Code
    tax_included = db.Column(db.Boolean)                # Tax included in the rate Yes/No
    tadig_plmn_code = db.Column(db.String(50))          # TADIG PLMN Code
    bearer_service_included = db.Column(db.Boolean)     # Bearer Service included in Special IOT Yes/No
    start_date = db.Column(db.Date)                     # Start date
    end_date = db.Column(db.Date)                       # End date
    currency = db.Column(db.String(10))                 # Currency
    moc_local_call_rate = db.Column(db.Float)           # MOC Call Local Call Rate/Value
    moc_local_call_interval = db.Column(db.Integer)     # MOC Call Local Call Charging interval
    moc_call_back_home_rate = db.Column(db.Float)       # MOC Call Call Back Home Rate/Value
    moc_call_back_home_interval = db.Column(db.Integer) # MOC Call Call Back Home Charging interval
    moc_rest_world_rate = db.Column(db.Float)           # MOC Call Rest of the world Rate/Value
    moc_rest_world_interval = db.Column(db.Integer)     # MOC Call Rest of the world Charging interval
    moc_premium_rate = db.Column(db.String(50))         # MOC Call Premium numbers Rate/Value
    moc_premium_interval = db.Column(db.String(50))     # MOC Call Premium numbers Charging interval
    moc_special_rate = db.Column(db.String(50))           # MOC Call Special numbers Rate/Value
    moc_special_interval = db.Column(db.String(50))       # MOC Call Special numbers Charging interval
    moc_satellite_rate = db.Column(db.String(50))         # MOC Call Satellite Rate/Value
    moc_satellite_interval = db.Column(db.String(50))     # MOC Call Satellite Charging interval
    mtc_call_rate = db.Column(db.Float)                   # MTC Call Rate/Value
    mtc_call_interval = db.Column(db.Integer)             # MTC Call Charging interval
    mo_sms_rate = db.Column(db.Float)                     # MO-SMS Rate/Value
    gprs_rate_mb_rate = db.Column(db.Float)               # GPRS Rate MB Rate/Value
    gprs_rate_mb_interval = db.Column(db.String(50))      # GPRS Rate MB Charging interval
    volte_rate_mb_rate = db.Column(db.Float)              # VoLTE Rate MB Rate/Value
    volte_rate_mb_interval = db.Column(db.String(50))     # VoLTE Rate MB Charging interval
    tax_applicable = db.Column(db.Boolean)                # Tax applicable Yes/No
    tax_value = db.Column(db.Float)                       # Tax applicable Tax Value

# Create tables
with app.app_context():
    db.create_all()

# Allowed Excel file extensions
ALLOWED_EXTENSIONS = {'.xls', '.xlsx'}

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def load_to_db(df):
    """Process each row from the DataFrame and insert into the database.
       If a required field (TAP-OUT) is missing, use a default value "DEFAULT".
    """
    skipped_rows = []
    try:
        for idx, row in df.iterrows():
            # Check required field value for "TAP-OUT"
            tap_value = row.get("TAP-OUT")
            # If missing or empty, you may choose to skip or assign a default.
            if pd.isna(tap_value) or str(tap_value).strip() == "":
                # For this example, we'll assign a default value.
                logger.warning("Row %d missing TAP-OUT. Using default value.", idx)
                tap_value = "DEFAULT"
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
            logger.error("Skipped rows (if any) due to missing TAP-OUT: %s", skipped_rows)
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
                
                # First, try reading the file normally.
                df = pd.read_excel(file)
                logger.info("File headers as read: %s", df.columns.tolist())
                
                # If "TAP-OUT" is not found, assume headers are vertical.
                if "TAP-OUT" not in df.columns:
                    logger.info("'TAP-OUT' not found in headers. Attempting transposition using first 29 rows as header.")
                    file.seek(0)  # Reset the file pointer
                    # Read without header; assume first 29 rows are headers
                    df_raw = pd.read_excel(file, header=None)
                    headers = df_raw.iloc[:29, 0].tolist()
                    headers = [str(h).strip() for h in headers]
                    logger.info("Detected headers: %s", headers)
                    # The remaining rows constitute the data; transpose so that headers become column names.
                    df_data = df_raw.iloc[29:]
                    df_t = df_data.transpose()
                    df_t.columns = headers
                    df = df_t.reset_index(drop=True)
                    logger.info("After transposition, columns: %s", df.columns.tolist())
                    
                # Validate mandatory header exists.
                if "TAP-OUT" not in df.columns:
                    msg = "Expected column 'TAP-OUT' not found in the uploaded Excel file."
                    logger.error(msg)
                    flash(msg, "danger")
                    return redirect(url_for('upload_ratesheet'))
                    
                logger.info("Excel file read successfully. Data rows: %d", len(df))
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
