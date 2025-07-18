import io
import pandas as pd
from flask import Blueprint, render_template, current_app, url_for, redirect, flash, send_file
from sqlalchemy import text
from app import db

ratecard_bp = Blueprint('ratecard', __name__, template_folder='templates')

SQL = """ 
SELECT *
FROM (
    -- 1. Local Calls
    SELECT 
        t.destination,
        t.area_code,
        a.moc_call_local_call_rate_value AS rate,
        'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250701' AS tariff_name,
        t."date"::DATE AS date,
        CASE 
            WHEN a.moc_call_local_call_charging_interval = '1 second' THEN '1/1'
            WHEN a.moc_call_local_call_charging_interval = '60 seconds' THEN '60/60'
            ELSE a.moc_call_local_call_charging_interval
        END AS rounding_rules,
        t.destination_type,
        t.setup_rate,
        t.calls_type,
        CASE WHEN t.remarks = 'NaN' THEN NULL ELSE t.remarks END AS remarks,
        1 AS source_order
    FROM ratesheet_v2 a
    CROSS JOIN "template" t
    JOIN country_v2 b ON LEFT(a.tadig_plmn_code, 3) = b.alpha_3
    WHERE t.destination = 'National'

    UNION ALL

    -- 2. Call Back Home
    SELECT 
        t.destination,
        t.area_code,
        a.moc_call_call_back_home_rate_value AS rate,
        'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250701' AS tariff_name,
        t."date"::DATE AS date,
        CASE 
            WHEN a.moc_call_call_back_home_charging_interval = '1 second' THEN '1/1'
            WHEN a.moc_call_call_back_home_charging_interval = '60 seconds' THEN '60/60'
            ELSE a.moc_call_call_back_home_charging_interval
        END AS rounding_rules,
        t.destination_type,
        t.setup_rate,
        t.calls_type,
        CASE WHEN t.remarks = 'NaN' THEN NULL ELSE t.remarks END AS remarks,
        2 AS source_order
    FROM ratesheet_v2 a
    CROSS JOIN "template" t
    JOIN country_v2 b ON LEFT(a.tadig_plmn_code, 3) = b.alpha_3
    WHERE t.destination = b.custom_name

    UNION ALL

    -- 3. ROW
    SELECT 
        t.destination,
        t.area_code,
        a.moc_call_rest_of_the_world_rate_value AS rate,
        'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250701' AS tariff_name,
        t."date"::DATE AS date,
        CASE 
            WHEN a.moc_call_rest_of_the_world_charging_interval = '1 second' THEN '1/1'
            WHEN a.moc_call_rest_of_the_world_charging_interval = '60 seconds' THEN '60/60'
            ELSE a.moc_call_rest_of_the_world_charging_interval
        END AS rounding_rules,
        t.destination_type,
        t.setup_rate,
        t.calls_type,
        CASE WHEN t.remarks = 'NaN' THEN NULL ELSE t.remarks END AS remarks,
        3 AS source_order
    FROM ratesheet_v2 a
    CROSS JOIN "template" t
    JOIN country_v2 b ON LEFT(a.tadig_plmn_code, 3) = b.alpha_3
    WHERE t.destination <> b.custom_name
      AND t.calls_type = 'ROW'

    UNION ALL

    -- 4. MTC CALLS
    SELECT 
        t.destination,
        t.area_code,
        a.mtc_call_rate_value AS rate,
        'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250701' AS tariff_name,
        t."date"::DATE AS date,
        CASE 
            WHEN a.mtc_call_charging_interval = '1 second' THEN '1/1'
            WHEN a.mtc_call_charging_interval = '60 seconds' THEN '60/60'
            ELSE a.mtc_call_charging_interval
        END AS rounding_rules,
        t.destination_type,
        t.setup_rate,
        t.calls_type,
        CASE WHEN t.remarks = 'NaN' THEN NULL ELSE t.remarks END AS remarks,
        4 AS source_order
    FROM ratesheet_v2 a
    CROSS JOIN "template" t
    JOIN country_v2 b ON LEFT(a.tadig_plmn_code, 3) = b.alpha_3
    WHERE t.calls_type = 'MTC CALLS'

    UNION ALL

    -- 5. Special/Miscellaneous Calls from Template Table
    SELECT 
        t.destination,
        t.area_code,
        t.rate AS rate,
        'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250701' AS tariff_name,
        t."date"::DATE AS date,
        CASE 
            WHEN t.rounding_rules = '1 second' THEN '1/1'
            WHEN t.rounding_rules = '60 seconds' THEN '60/60'
            ELSE t.rounding_rules
        END AS rounding_rules,
        t.destination_type,
        t.setup_rate,
        t.calls_type,
        CASE WHEN t.remarks = 'NaN' THEN NULL ELSE t.remarks END AS remarks,
        5 AS source_order
    FROM ratesheet_v2 a
    CROSS JOIN "template" t
    JOIN country_v2 b ON LEFT(a.tadig_plmn_code, 3) = b.alpha_3
    WHERE t.calls_type IN (
        'Customer Care',
        'directory calls',
        'emergency calls',
        'Satellite',
        'Local Short Code',
        'Premium',
        'Toll Free'
    )
) final_output

ORDER BY 
    tariff_name,
    source_order,
    -- For ROW block (source_order 3)
    CASE WHEN source_order = 3 THEN destination ELSE NULL END,
    -- For Local/Call-Back-Home (1 and 2)
    CASE WHEN source_order IN (1, 2) THEN calls_type ELSE NULL END,
    -- For MTC CALLS (4)
    CASE WHEN source_order = 4 THEN destination ELSE NULL END,
    -- For Misc block (5)
    CASE WHEN source_order = 5 THEN calls_type ELSE NULL END,
    CASE WHEN source_order = 5 THEN destination ELSE NULL END;
"""

@ratecard_bp.route('/download-ratecard', methods=['GET'])
def download_ratecard_page():
    return render_template('download_ratecard.html')

@ratecard_bp.route('/download-ratecard/file', methods=['GET'])
def download_ratecard_file():
    logger = current_app.logger
    try:
        logger.info("Running ratecard SQL…")
        # execute via session, not engine
        result = db.session.execute(text(SQL))
        rows = result.fetchall()
        cols = result.keys()
        df = pd.DataFrame(rows, columns=cols)
        logger.debug(f"Fetched {len(df)} rows for ratecard")

        # Write Excel to memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Ratecard')
        output.seek(0)
        logger.info("Excel generated, sending to client")

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
