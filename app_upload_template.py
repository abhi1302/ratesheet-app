import pandas as pd
from flask import Blueprint, render_template, request, flash, redirect, url_for
from sqlalchemy import text
from app import db, logger  # import your app’s db & logger

bp = Blueprint('upload_template', __name__, template_folder='templates')


# NEW DDL for your `template` table:
# CREATE TABLE template (
#   id SERIAL PRIMARY KEY,
#   Destination VARCHAR(100),
#   Area_Code VARCHAR(20),
#   Rate DOUBLE PRECISION,
#   TARIFF_NAME VARCHAR(100),
#   Date DATE,
#   Rounding_Rules VARCHAR(20),
#   Destination_Type VARCHAR(50),
#   Setup_Rate DOUBLE PRECISION,
#   Calls_Type VARCHAR(100),
#   Remarks TEXT
# );

@bp.route('/upload-template', methods=['GET','POST'])
def upload_template():
    # same body as above…
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("No file selected", "error")
            logger.error("upload-template: no file provided")
            return redirect(request.url)
        try:
            df = pd.read_excel(file)
            logger.info(f"Template upload: read Excel {df.shape}")
            
            # empty out existing data
            db.session.execute(text("TRUNCATE TABLE template RESTART IDENTITY;"))
            db.session.commit()
            logger.debug("Template table truncated")

            # insert each row
            for i,row in df.iterrows():
                db.session.execute(text("""
                  INSERT INTO template (
                    Destination, Area_Code, Rate, TARIFF_NAME, Date,
                    Rounding_Rules, Destination_Type, Setup_Rate, Calls_Type, Remarks
                  ) VALUES (
                    :Destination, :Area_Code, :Rate, :TARIFF_NAME, :Date,
                    :Rounding_Rules, :Destination_Type, :Setup_Rate, :Calls_Type, :Remarks
                  )
                """), {
                  "Destination":    row.get("Destination"),
                  "Area_Code":      row.get("Area Code"),
                  "Rate":           row.get("Rate"),
                  "TARIFF_NAME":    row.get("TARIFF_NAME"),
                  "Date":           row.get("Date"),
                  "Rounding_Rules": row.get("Rounding Rules"),
                  "Destination_Type": row.get("Destination Type"),
                  "Setup_Rate":     row.get("Setup Rate"),
                  "Calls_Type":     row.get("calls based on number types"),
                  "Remarks":        row.get("remarks"),
                })
                logger.debug(f"Inserted template row {i}")
            db.session.commit()
            flash("Template uploaded successfully", "success")
            logger.info("All template rows committed")
            return redirect(url_for('upload_template'))

        except Exception as e:
            db.session.rollback()
            logger.exception("Error in upload-template")
            flash(f"Error: {e}", "error")
            return redirect(request.url)

    return render_template('upload_template.html')