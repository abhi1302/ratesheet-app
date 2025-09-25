import io
import pandas as pd
from flask import Blueprint, render_template, current_app, url_for, redirect, flash, send_file
from sqlalchemy import text
from app import db

volte_ratecard_bp = Blueprint('volte_ratecard', __name__, template_folder='templates')

SQL_VOLTE = """
select
    tadig_plmn_code as "Destination",
    tadig_plmn_code as "Area Code",
    volte_rate_mb_rate_value::numeric(12,8) as "Rate",
    start_date as "Valid From",  -- keep as DATE
    CASE
        WHEN volte_rate_mb_charging_interval = '1 KB' THEN '1024/1024'
        WHEN volte_rate_mb_charging_interval = '10 KB' THEN '10240/10240'
        WHEN volte_rate_mb_charging_interval = '1 MB' THEN '1048576/1048576'
        ELSE volte_rate_mb_charging_interval
    END as rounding_rules
from ratesheet_v2;
"""

@volte_ratecard_bp.route('/download-volte-ratecard', methods=['GET'])
def download_volte_ratecard_page():
    return render_template('download_volte_ratecard.html')


@volte_ratecard_bp.route('/download-volte-ratecard/file', methods=['GET'])
def download_volte_ratecard_file():
    logger = current_app.logger
    try:
        logger.info("Running VoLTE ratecard SQL…")
        result = db.session.execute(text(SQL_VOLTE))
        rows = result.fetchall()
        cols = result.keys()
        df = pd.DataFrame(rows, columns=cols)
        logger.debug(f"Fetched {len(df)} rows for volte ratecard")

        # Write to Excel (default sheet name = "Sheet1")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)  # default sheet name -> "Sheet1"

            # Optional: apply date format so Excel displays dd-mmm-yy while keeping real date
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            date_format = workbook.add_format({'num_format': 'dd-mmm-yy'})
            # find column index for "Valid From" and set format (0-based index)
            # assume "Valid From" is one of the columns; find its index dynamically:
            try:
                col_idx = df.columns.get_loc('Valid From')
                # set_column expects Excel col letters/range; compute start-end as A:A style
                # simpler: set_column by index range using zero-based col numbers converted to Excel syntax
                # xlsxwriter set_column accepts numeric indices as string range 'A:A' so compute:
                col_letter = chr(ord('A') + col_idx)  # works for first 26 columns
                worksheet.set_column(f'{col_letter}:{col_letter}', 15, date_format)
            except Exception:
                # If anything goes wrong (e.g., column not present or index > 25), skip formatting.
                logger.debug("Could not apply date format to 'Valid From' column; skipping.")

        output.seek(0)
        logger.info("VoLTE Excel generated, sending to client")

        return send_file(
            output,
            as_attachment=True,
            download_name='volte_ratecard.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.exception("Failed to generate volte ratecard Excel")
        flash(f"Error generating volte ratecard: {e}", "error")
        return redirect(url_for('volte_ratecard.download_volte_ratecard_page'))
