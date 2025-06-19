--BU PLMN Code
--TADIG PLMN Code
--Start date	
--End date	
--Currency
--MOC Call Local Call Rate/Value	
--MOC Call Local Call Charging interval	
--MOC Call Call Back Home Rate/Value
--MOC Call Call Back Home Charging interval
--MOC Call Rest of the world Rate/Value	
--MOC Call Rest of the world Charging interval	
--MOC Call Premium numbers Rate/Value	
--MOC Call Premium numbers Charging interval	
--MOC Call Special numbers Rate/Value	
--MOC Call Special numbers Charging interval	
--MOC Call Satellite Rate/Value	
--MOC Call Satellite Charging interval
--MTC Call Rate/Value
--MTC Call Charging interval	
--MO-SMS Rate/Value	
--GPRS Rate MB Rate/Value
--GPRS Rate per KB Rate/Value
--GPRS Rate MB Charging interval
--VoLTE Rate MB Rate/Value	
--VoLTE Rate MB Charging interval	
--Tax applicable Yes/No	
--Tax applicable Tax Value	
--Tax included in the rate Yes/No	
--Bearer Service included in Special IOT Yes/No
CREATE TABLE ratesheet_v2 (
  id SERIAL PRIMARY KEY,
  bu_plmn_code VARCHAR(50),
  tadig_plmn_code VARCHAR(50),
  start_date DATE,
  end_date DATE,
  currency VARCHAR(10),
  moc_call_local_call_rate_value DOUBLE PRECISION,
  moc_call_local_call_charging_interval VARCHAR(50),
  moc_call_call_back_home_rate_value DOUBLE PRECISION,
  moc_call_call_back_home_charging_interval VARCHAR(50),
  moc_call_rest_of_the_world_rate_value DOUBLE PRECISION,
  moc_call_rest_of_the_world_charging_interval VARCHAR(50),
  moc_call_premium_numbers_rate_value DOUBLE PRECISION,
  moc_call_premium_numbers_charging_interval VARCHAR(50),
  moc_call_special_numbers_rate_value DOUBLE PRECISION,
  moc_call_special_numbers_charging_interval VARCHAR(50),
  moc_call_satellite_rate_value DOUBLE PRECISION,
  moc_call_satellite_charging_interval VARCHAR(50),
  mtc_call_rate_value DOUBLE PRECISION,
  mtc_call_charging_interval VARCHAR(50),
  mo_sms_rate_value DOUBLE PRECISION,
  gprs_rate_mb_rate_value DOUBLE PRECISION,
  gprs_rate_per_kb_rate_value DOUBLE PRECISION,
  gprs_rate_mb_charging_interval VARCHAR(50),
  volte_rate_mb_rate_value DOUBLE PRECISION,
  volte_rate_mb_charging_interval VARCHAR(50),
  tax_applicable_yes_no VARCHAR(10),
  tax_applicable_tax_value VARCHAR(50),
  tax_included_in_the_rate_yes_no VARCHAR(10),
  bearer_service_included_in_special_iot_yes_no VARCHAR(10)
);
