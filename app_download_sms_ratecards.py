import io
import pandas as pd
from flask import Blueprint, render_template, current_app, url_for, redirect, flash, send_file
from sqlalchemy import text
from app import db

sms_ratecard_bp = Blueprint('sms_ratecard', __name__, template_folder='templates')

SQL_SMS = """
select tadig_plmn_code as "Destination", 
       tadig_plmn_code as "Area Code", 
       mo_sms_rate_value as "Setup Rate",
       start_date as "Valid From (dd-mmm-yyyy)",
       0.0 AS "Rate"
from ratesheet_v2;
"""

@sms_ratecard_bp.route('/download-sms-ratecard', methods=['GET'])
def download_sms_ratecard_page():
    return render_template('download_ratecard.html')


@sms_ratecard_bp.route('/download-sms-ratecard/file', methods=['GET'])
def download_sms_ratecard_file():
    logger = current_app.logger
    try:
        logger.info("Running SMS ratecard SQL…")
        result = db.session.execute(text(SQL_SMS))
        rows = result.fetchall()
        cols = result.keys()
        df = pd.DataFrame(rows, columns=cols)
        logger.debug(f"Fetched {len(df)} rows for sms ratecard")

        # If the start_date column is a date object, you may want to format it as dd-MMM-YYYY
        # Uncomment the following lines if needed:
        # if 'Valid From (dd-mmm-yyyy)' in df.columns:
        #     df['Valid From (dd-mmm-yyyy)'] = pd.to_datetime(df['Valid From (dd-mmm-yyyy)']).dt.strftime('%d-%b-%Y')

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='SMS_Ratecard')
        output.seek(0)
        logger.info("SMS Excel generated, sending to client")

        return send_file(
            output,
            as_attachment=True,
            download_name='sms_ratecard.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.exception("Failed to generate sms ratecard Excel")
        flash(f"Error generating sms ratecard: {e}", "error")
        return redirect(url_for('sms_ratecard.download_sms_ratecard_page'))
