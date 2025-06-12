from flask import Flask, request, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a strong secret in production

# Configure database - using SQLite here for simplicity
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ratesheet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database model to hold ratesheet data
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
    # You can add additional columns as required

# Allow file extensions for Excel
ALLOWED_EXTENSIONS = {'.xls', '.xlsx'}

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

# Function to load DataFrame rows to DB
def load_to_db(df):
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
                # Map additional fields as needed…
            )
            db.session.add(record)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print("Error while inserting records:", e)
        return False

@app.route('/upload', methods=['GET', 'POST'])
def upload_ratesheet():
    if request.method == 'POST':
        file = request.files.get('ratesheet')
        if file and allowed_file(file.filename):
            try:
                # Read Excel into a DataFrame using pandas
                df = pd.read_excel(file)
                # Insert into database
                if load_to_db(df):
                    flash("Ratesheet loaded successfully!", "success")
                else:
                    flash("Ratesheet load failed. Please check error logs for details.", "danger")
            except Exception as e:
                flash(f"Failed to process file: {str(e)}", "danger")
        else:
            flash("Invalid file type. Please upload an Excel file (.xls or .xlsx).", "danger")
        return redirect(url_for('upload_ratesheet'))
    return render_template('upload.html')

# Default route to redirect to upload
@app.route('/')
def index():
    return redirect(url_for('upload_ratesheet'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(host='0.0.0.0', port=5000, debug=True)
