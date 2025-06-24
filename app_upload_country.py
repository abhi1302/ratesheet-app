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

# in app_upload_country.py, near the top:
def clean_cell(val, max_len=None, upper=False):
    """
    - nan → None
    - floats with .0 → int
    - everything → str()
    - optionally truncate to max_len, uppercase
    """
    if pd.isna(val):
        return None
    # convert floats like 2.0 → int(2)
    if isinstance(val, float) and val.is_integer():
        val = int(val)
    s = str(val).strip()
    if upper:
        s = s.upper()
    if max_len is not None and len(s) > max_len:
        s = s[:max_len]
    return s

@country_bp.route('/upload-country', methods=['GET','POST'])
def upload_country():
    logger = current_app.logger

    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("No file provided", "error")
            logger.error("upload-country: no file received")
            return redirect(request.url)

        try:
            df = pd.read_excel(file)
            logger.info(f"Country sheet shape: {df.shape}")

            # Truncate
            db.session.execute(text("TRUNCATE TABLE country_v2 RESTART IDENTITY;"))
            db.session.commit()
            logger.debug("country_v2 truncated")

            for i, row in df.iterrows():
                params = {
                    # max_len=100 for name, custom_name
                    "name":                    clean_cell(row["name"], max_len=100),
                    "alpha_2":                 clean_cell(row["alpha-2"], max_len=2, upper=True),
                    "alpha_3":                 clean_cell(row["alpha-3"], max_len=3, upper=True),
                    "country_code":            clean_cell(row["country-code"], max_len=10),
                    "iso_3166_2":              clean_cell(row["iso_3166-2"], max_len=20),
                    "region":                  clean_cell(row["region"], max_len=50),
                    "sub_region":              clean_cell(row["sub-region"], max_len=50),
                    "intermediate_region":     clean_cell(row["intermediate-region"], max_len=50),
                    "region_code":             clean_cell(row["region-code"], max_len=10),
                    "sub_region_code":         clean_cell(row["sub-region-code"], max_len=10),
                    "intermediate_region_code":clean_cell(row["intermediate-region-code"], max_len=10),
                    "custom_name":             clean_cell(row["custom-name"], max_len=100),
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

    return render_template('upload_country.html')
