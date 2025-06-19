from flask import Flask, request, render_template, redirect, url_for, flash
import os
import pandas as pd
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # Replace with your strong secret key

# Use the DATABASE_URL environment variable if available, otherwise update the connection string below.
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define a model that stores each Excel row as a JSON object.
class RateSheet(db.Model):
    __tablename__ = 'ratesheet'
    id = db.Column(db.Integer, primary_key=True)
    # Using a JSON column makes it easier to handle arbitrary Excel columns.
    data = db.Column(db.JSON)

# Create tables on the first request if they don't exist.
@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get("file")
        if not file:
            flash("No file provided", "error")
            return redirect(request.url)
        try:
            # Read the Excel file into a pandas DataFrame.
            df = pd.read_excel(file)
            # Insert each row into the database.
            for _, row in df.iterrows():
                new_row = RateSheet(data=row.to_dict())
                db.session.add(new_row)
            db.session.commit()
            flash("Excel file successfully loaded into DB", "success")
            return redirect(url_for("data_view"))
        except Exception as e:
            flash(f"Error processing file: {str(e)}", "error")
            return redirect(request.url)
    return render_template("index.html")

@app.route('/data', methods=["GET", "POST"])
def data_view():
    if request.method == "POST":
        # Save updated data from the form.
        try:
            record_id = request.form.get("record_id")
            record = RateSheet.query.filter_by(id=record_id).first()
            if record:
                updated_data = {}
                # Process every form key except record_id.
                for key, value in request.form.items():
                    if key != "record_id":
                        updated_data[key] = value
                record.data = updated_data
                db.session.commit()
                flash("Record updated", "success")
            else:
                flash("Record not found", "error")
        except Exception as e:
            flash(f"Error updating record: {str(e)}", "error")
        return redirect(url_for("data_view"))
    
    # Display all records
    records = RateSheet.query.all()
    return render_template("data.html", records=records)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
