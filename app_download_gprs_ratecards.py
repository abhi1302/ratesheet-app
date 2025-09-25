import io
import pandas as pd
from flask import Blueprint, render_template, current_app, url_for, redirect, flash, send_file
from sqlalchemy import text
from app import db

gprs_ratecard_bp = Blueprint('gprs_ratecard', __name__, template_folder='templates')

SQL_GPRS = """
select tadig_plmn_code as "Destination", 
       tadig_plmn_code as "Area Code", 
       gprs_rate_mb_rate_value as "Rate",
       start_date AS "Valid From",   -- keep as DATE, no to_char
       CASE 
           WHEN gprs_rate_mb_charging_interval = '1 KB' THEN '1024/1024'
           WHEN gprs_rate_mb_charging_interval = '10 KB' THEN '10240/10240'
           WHEN gprs_rate_mb_charging_interval = '1 MB' THEN '1048576/1048576'
           ELSE gprs_rate_mb_charging_interval
       END AS rounding_rules
from ratesheet_v2;
"""

@gprs_ratecard_bp.route('/download-gprs-ratecard', methods=['GET'])
def download_gprs_ratecard_page():
    return render_template('download_gprs_ratecard.html')


@gprs_ratecard_bp.route('/download-gprs-ratecard/file', methods=['GET'])
def download_gprs_ratecard_file():
    logger = current_app.logger
    try:
        logger.info("Running GPRS ratecard SQL…")
        result = db.session.execute(text(SQL_GPRS))
        rows = result.fetchall()
        cols = result.keys()
        df = pd.DataFrame(rows, columns=cols)
        logger.debug(f"Fetched {len(df)} rows for gprs ratecard")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='GPRS_Ratecard')
        output.seek(0)
        logger.info("GPRS Excel generated, sending to client")

        return send_file(
            output,
            as_attachment=True,
            download_name='gprs_ratecard.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.exception("Failed to generate gprs ratecard Excel")
        flash(f"Error generating gprs ratecard: {e}", "error")
        return redirect(url_for('gprs_ratecard.download_gprs_ratecard_page'))


# ------------------------------------------------------------------
# Add the following to your app.py to register this blueprint:
#
# from app_download_gprs_ratecards import gprs_ratecard_bp
# app.register_blueprint(gprs_ratecard_bp)
#
# ------------------------------------------------------------------
# Template: download_gprs_ratecard.html (place in templates/)
#
# <!DOCTYPE html>
# <html lang="en">
# <head>
#   <meta charset="UTF-8">
#   <title>Download GPRS Ratecard</title>
# </head>
# <body>
#   <h1>Download GPRS Ratecard</h1>
#   <form method="GET" action="{{ url_for('gprs_ratecard.download_gprs_ratecard_file') }}">
#     <button type="submit">Download GPRS ratecard</button>
#   </form>
#
#   {% with msgs = get_flashed_messages(with_categories=true) %}
#     {% if msgs %}
#       <ul>
#         {% for cat, msg in msgs %}
#           <li style="color: {{ 'red' if cat=='error' else 'green' }}">{{ msg }}</li>
#         {% endfor %}
#       </ul>
#     {% endif %}
#   {% endwith %}
# </body>
# </html>
#
# ------------------------------------------------------------------
# Notes:
# - The SQL above formats the date using to_char. If you'd like the Excel to contain
#   a real date value (better for sorting/filtering), remove to_char in SQL and
#   format the date in pandas/xlsxwriter when writing the file.
# - If you want column formatting (e.g. numeric precision, date format) I can add
#   the xlsxwriter formatting into this file.
# ------------------------------------------------------------------
