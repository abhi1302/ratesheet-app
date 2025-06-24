import io
import pandas as pd
from flask import Blueprint, render_template, current_app, url_for, redirect, flash, send_file
from sqlalchemy import text
from app import db  # your SQLAlchemy instance

ratecard_bp = Blueprint(
    'ratecard',             # blueprint name
    __name__,
    template_folder='templates'
)

SQL = """
SELECT 
    t.destination,
    t.area_code,
    a.moc_call_local_call_rate_value AS rate,
    'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250701' AS tariff_name,
    '2025-07-01' AS "date",
    CASE 
        WHEN a.moc_call_call_back_home_charging_interval = '1 second' THEN '1/1'
        WHEN a.moc_call_call_back_home_charging_interval = '60 seconds' THEN '60/60'
        ELSE a.moc_call_call_back_home_charging_interval
    END AS rounding_rules,
    t.destination_type,
    t.setup_rate,
    t.calls_type,
    CASE 
        WHEN t.remarks = 'NaN' THEN NULL
        ELSE t.remarks
    END AS remarks
FROM ratesheet_v2 a
CROSS JOIN "template" t
JOIN country_v2 b
  ON LEFT(a.tadig_plmn_code, 3) = b.alpha_3
WHERE t.destination = 'National'
ORDER BY tariff_name;
"""

@ratecard_bp.route('/download-ratecard', methods=['GET'])
def download_ratecard_page():
    """Render a simple page with a Download button."""
    return render_template('download_ratecard.html')


@ratecard_bp.route('/download-ratecard/file', methods=['GET'])
def download_ratecard_file():
    logger = current_app.logger
    try:
        logger.info("Running ratecard SQL…")
        # <-- use db.engine instead of db.session.bind -->
        df = pd.read_sql_query(SQL, con=db.engine)
        logger.debug(f"Fetched {len(df)} rows for ratecard")

        # Build Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Ratecard')
        output.seek(0)
        logger.info("Excel workbook generated, sending to client")

        return send_file(
            output,
            as_attachment=True,
            download_name='ratecard_national.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.exception("Failed to generate ratecard Excel")
        flash(f"Error generating ratecard: {e}", "error")
        return redirect(url_for('ratecard.download_ratecard_page'))
