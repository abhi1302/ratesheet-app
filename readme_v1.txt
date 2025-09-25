readme file:

https://ratesheet-app.onrender.com/upload-template

CREATE TABLE IF NOT EXISTS template (
    id SERIAL PRIMARY KEY,
    destination VARCHAR(100),
    area_code VARCHAR(20),
    rate DOUBLE PRECISION,
    tariff_name VARCHAR(100),
    date DATE,
    rounding_rules VARCHAR(20),
    destination_type VARCHAR(50),
    setup_rate DOUBLE PRECISION,
    calls_type VARCHAR(100),
    remarks TEXT
);



https://ratesheet-app.onrender.com/upload-country

CREATE TABLE country_v2 (
  id SERIAL PRIMARY KEY,
  name                   VARCHAR(100),
  alpha_2                CHAR(2),
  alpha_3                CHAR(3),
  country_code           VARCHAR(10),
  iso_3166_2             VARCHAR(20),
  region                 VARCHAR(50),
  sub_region             VARCHAR(50),
  intermediate_region    VARCHAR(50),
  region_code            VARCHAR(10),
  sub_region_code        VARCHAR(10),
  intermediate_region_code VARCHAR(10),
  custom_name            VARCHAR(100)
);


-----------------------------------------

https://ratesheet-app.onrender.com/download-ratecard

-----------------------------------

SELECT *
FROM (
    -- 1. Local Calls
    SELECT 
        t.destination,
        t.area_code,
        a.moc_call_local_call_rate_value AS rate,
        'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250801' AS tariff_name,
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
        'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250801' AS tariff_name,
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
        'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250801' AS tariff_name,
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
        'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250801' AS tariff_name,
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
        'CELC_IR_VOICE_TARIFF_' || a.tadig_plmn_code || '_20250801' AS tariff_name,
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
