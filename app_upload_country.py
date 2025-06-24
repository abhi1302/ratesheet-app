import pandas as pd
from flask import Blueprint, request, render_template, flash, redirect, url_for, current_app
from sqlalchemy import text
from app import db  # import your SQLAlchemy db instance

# Create a Blueprint
country_bp = Blueprint(
    'country',                # blueprint name
    __name__,
    template_folder='templates'
)

@country_bp.route('/upload-country', methods=['GET', 'POST'])
def upload_country():
    logger = current_app.logger

    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("No file provided", "error")
            logger.error("upload-country: no file received")
            return redirect(request.url)

        try:
            logger.info("Reading country Excel file...")
            df = pd.read_excel(file)
            logger.debug(f"Country sheet shape: {df.shape}")

            # Truncate table
            db.session.execute(text("TRUNCATE TABLE country_v2 RESTART IDENTITY;"))
            db.session.commit()
            logger.debug("Truncated country_v2 table")

            # Insert rows
            for i, row in df.iterrows():
                params = {
                    "name":                    row.get("name"),
                    "alpha_2":                 row.get("alpha-2"),
                    "alpha_3":                 row.get("alpha-3"),
                    "country_code":            row.get("country-code"),
                    "iso_3166_2":              row.get("iso_3166-2"),
                    "region":                  row.get("region"),
                    "sub_region":              row.get("sub-region"),
                    "intermediate_region":     row.get("intermediate-region"),
                    "region_code":             row.get("region-code"),
                    "sub_region_code":         row.get("sub-region-code"),
                    "intermediate_region_code":row.get("intermediate-region-code"),
                    "custom_name":             row.get("custom-name")
                }
                db.session.execute(text("""
                    INSERT INTO country_v2 (
                      name, alpha_2, alpha_3, country_code, iso_3166_2,
                      region, sub_region, intermediate_region,
                      region_code, sub_region_code, intermediate_region_code,
                      custom_name
                    ) VALUES (
                      :name, :alpha_2, :alpha_3, :country_code, :iso_3166_2,
                      :region, :sub_region, :intermediate_region,
                      :region_code, :sub_region_code, :intermediate_region_code,
                      :custom_name
                    )
                """), params)
                logger.debug(f"Inserted row {i}: {params['name']}")

            db.session.commit()
            flash("Country data loaded successfully", "success")
            logger.info("All country rows committed")
            return redirect(url_for('country.upload_country'))

        except Exception as e:
            db.session.rollback()
            logger.exception("Error in upload-country")
            flash(f"Error processing file: {e}", "error")
            return redirect(request.url)

    # GET
    return render_template('upload_country.html')
