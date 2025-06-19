import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime

from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Configure logging.
# In development, logs are output to the console.
# On Render, logs written to stdout/stderr will be visible in Render's dashboard logs.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # Replace with a strong secret key

# Use DATABASE_URL if provided, otherwise update the connection string accordingly.
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define the model based on your DDL.
class RateSheetV2(db.Model):
    __tablename__ = 'ratesheet_v2'
    id = db.Column(db.Integer, primary_key=True)
    bu_plmn_code = db.Column(db.String(50))
    tadig_plmn_code = db.Column(db.String(50))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    currency = db.Column(db.String(10))
    moc_call_local_call_rate_value = db.Column(db.Float)
    moc_call_local_call_charging_interval = db.Column(db.String(50))
    moc_call_call_back_home_rate_value = db.Column(db.Float)
    moc_call_call_back_home_charging_interval = db.Column(db.String(50))
    moc_call_rest_of_the_world_rate_value = db.Column(db.Float)
    moc_call_rest_of_the_world_charging_interval = db.Column(db.String(50))
    moc_call_premium_numbers_rate_value = db.Column(db.Float)
    moc_call_premium_numbers_charging_interval = db.Column(db.String(50))
    moc_call_special_numbers_rate_value = db.Column(db.Float)
    moc_call_special_numbers_charging_interval = db.Column(db.String(50))
    moc_call_satellite_rate_value = db.Column(db.Float)
    moc_call_satellite_charging_interval = db.Column(db.String(50))
    mtc_call_rate_value = db.Column(db.Float)
    mtc_call_charging_interval = db.Column(db.String(50))
    mo_sms_rate_value = db.Column(db.Float)
    gprs_rate_mb_rate_value = db.Column(db.Float)
    gprs_rate_per_kb_rate_value = db.Column(db.Float)
    gprs_rate_mb_charging_interval = db.Column(db.String(50))
    volte_rate_mb_rate_value = db.Column(db.Float)
    volte_rate_mb_charging_interval = db.Column(db.String(50))
    tax_applicable_yes_no = db.Column(db.String(10))
    tax_applicable_tax_value = db.Column(db.String(50))
    tax_included_in_the_rate_yes_no = db.Column(db.String(10))
    bearer_service_included_in_special_iot_yes_no = db.Column(db.String(10))

# Mapping dictionary between Excel headers and DB model field names.
COLUMN_MAPPING = {
    "BU PLMN Code": "bu_plmn_code",
    "TADIG PLMN Code": "tadig_plmn_code",
    "Start date": "start_date",
    "End date": "end_date",
    "Currency": "currency",
    "MOC Call Local Call Rate/Value": "moc_call_local_call_rate_value",
    "MOC Call Local Call Charging interval": "moc_call_local_call_charging_interval",
    "MOC Call Call Back Home Rate/Value": "moc_call_call_back_home_rate_value",
    "MOC Call Call Back Home Charging interval": "moc_call_call_back_home_charging_interval",
    "MOC Call Rest of the world Rate/Value": "moc_call_rest_of_the_world_rate_value",
    "MOC Call Rest of the world Charging interval": "moc_call_rest_of_the_world_charging_interval",
    "MOC Call Premium numbers Rate/Value": "moc_call_premium_numbers_rate_value",
    "MOC Call Premium numbers Charging interval": "moc_call_premium_numbers_charging_interval",
    "MOC Call Special numbers Rate/Value": "moc_call_special_numbers_rate_value",
    "MOC Call Special numbers Charging interval": "moc_call_special_numbers_charging_interval",
    "MOC Call Satellite Rate/Value": "moc_call_satellite_rate_value",
    "MOC Call Satellite Charging interval": "moc_call_satellite_charging_interval",
    "MTC Call Rate/Value": "mtc_call_rate_value",
    "MTC Call Charging interval": "mtc_call_charging_interval",
    "MO-SMS Rate/Value": "mo_sms_rate_value",
    "GPRS Rate MB Rate/Value": "gprs_rate_mb_rate_value",
    "GPRS Rate per KB Rate/Value": "gprs_rate_per_kb_rate_value",
    "GPRS Rate MB Charging interval": "gprs_rate_mb_charging_interval",
    "VoLTE Rate MB Rate/Value": "volte_rate_mb_rate_value",
    "VoLTE Rate MB Charging interval": "volte_rate_mb_charging_interval",
    "Tax applicable Yes/No": "tax_applicable_yes_no",
    "Tax applicable Tax Value": "tax_applicable_tax_value",
    "Tax included in the rate Yes/No": "tax_included_in_the_rate_yes_no",
    "Bearer Service included in Special IOT Yes/No": "bearer_service_included_in_special_iot_yes_no"
}

def convert_value(value, target_field):
    """
    Convert the value type based on the target DB column.
    For date fields, convert to a date; for numeric fields, attempt a float conversion.
    """
    # For date fields.
    if target_field in ["start_date", "end_date"]:
        if pd.isnull(value):
            return None
        if isinstance(value, pd.Timestamp):
            return value.date()
        try:
            return pd.to_datetime(value).date()
        except Exception as e:
            logger.error(f"Error converting date for field {target_field}: {value} -- {e}")
            return None

    # For numeric (float) fields.
    numeric_fields = [
        "moc_call_local_call_rate_value", "moc_call_call_back_home_rate_value",
        "moc_call_rest_of_the_world_rate_value", "moc_call_premium_numbers_rate_value",
        "moc_call_special_numbers_rate_value", "moc_call_satellite_rate_value",
        "mtc_call_rate_value", "mo_sms_rate_value", "gprs_rate_mb_rate_value",
        "gprs_rate_per_kb_rate_value", "volte_rate_mb_rate_value"
    ]
    if target_field in numeric_fields:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    return value

def process_excel_row(row):
    """
    Given a Pandas series (row) read from the Excel file,
    map it to a dictionary with keys matching the RateSheetV2 model.
    """
    processed = {}
    for excel_header, model_field in COLUMN_MAPPING.items():
        value = row.get(excel_header, None)
        # Convert numpy NaN to None if applicable.
        if isinstance(value, float) and np.isnan(value):
            value = None
        processed[model_field] = convert_value(value, model_field)
    return processed

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get("file")
        if not file:
            logger.error("No file provided during upload request.")
            flash("No file provided", "error")
            return redirect(request.url)
        try:
            logger.info("Reading uploaded Excel file...")
            df = pd.read_excel(file)
            logger.debug(f"Excel file read with columns: {list(df.columns)} and shape: {df.shape}")

            # Truncate the ratesheet_v2 table for a fresh upload.
            logger.info("Truncating ratesheet_v2 table for fresh upload.")
            db.session.execute(text("TRUNCATE TABLE ratesheet_v2 RESTART IDENTITY;"))
            db.session.commit()

            # Process every row (first row is headers).
            for idx, row in df.iterrows():
                row_data = process_excel_row(row)
                new_row = RateSheetV2(**row_data)
                db.session.add(new_row)
                logger.debug(f"Prepared row {idx} for insertion: {row_data}")
            db.session.commit()
            logger.info("All rows inserted successfully into ratesheet_v2.")
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
            record = RateSheetV2.query.filter_by(id=record_id).first()
            if record:
                # Loop through the known fields (ignoring record_id).
                for field in COLUMN_MAPPING.values():
                    if field in request.form:
                        new_val = request.form.get(field)
                        # For date fields, convert string back to a date.
                        if field in ["start_date", "end_date"]:
                            try:
                                new_val = pd.to_datetime(new_val).date()
                            except Exception:
                                new_val = None
                        # For numeric fields, try to convert.
                        elif field in [
                            "moc_call_local_call_rate_value", "moc_call_call_back_home_rate_value",
                            "moc_call_rest_of_the_world_rate_value", "moc_call_premium_numbers_rate_value",
                            "moc_call_special_numbers_rate_value", "moc_call_satellite_rate_value",
                            "mtc_call_rate_value", "mo_sms_rate_value", "gprs_rate_mb_rate_value",
                            "gprs_rate_per_kb_rate_value", "volte_rate_mb_rate_value"
                        ]:
                            try:
                                new_val = float(new_val)
                            except Exception:
                                new_val = None
                        setattr(record, field, new_val)
                db.session.commit()
                logger.info(f"Record {record_id} updated successfully.")
                flash("Record updated", "success")
            else:
                logger.error(f"Record not found for id {record_id}.")
                flash("Record not found", "error")
        except Exception as e:
            logger.exception("Error updating record.")
            flash(f"Error updating record: {str(e)}", "error")
        return redirect(url_for("data_view"))
    
    records = RateSheetV2.query.all()
    logger.debug(f"Fetched {len(records)} records from the database for display.")
    return render_template("data.html", records=records)

# Global error handler to capture any unhandled exceptions.
@app.errorhandler(Exception)
def handle_exception(e):
    logger.exception("Unhandled Exception: %s", e)
    return render_template("error.html", error=str(e)), 500


# Inject Python's built-in getattr into templates.
@app.context_processor
def inject_utilities():
    return dict(getattr=getattr)
    
@app.context_processor
def inject_globals():
    return dict(COLUMN_MAPPING=COLUMN_MAPPING, getattr=getattr)

@app.template_filter('float_format')
def float_format(value, precision=6):
    try:
        return f"{value:.{precision}f}"
    except Exception as e:
        logger.error("Error formatting float: %s", e)
        return value
    

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting app_v2 on host 0.0.0.0, port {port} with debug=True")
    app.run(host='0.0.0.0', port=port, debug=True)

