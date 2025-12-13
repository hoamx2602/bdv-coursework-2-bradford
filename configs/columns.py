# configs/columns.py
CSV_TO_CURATED = {
    # Temperature & indices
    "Temp_Out": "temp_out",
    "Hi_Temp": "hi_temp",
    "Low_Temp": "low_temp",
    "Dew_Pt": "dew_pt",
    "Wind_Chill": "wind_chill",
    "Heat_Index": "heat_index",
    "THW_Index": "thw_index",
    "THSW_Index": "thsw_index",

    # Humidity
    "Out_Hum": "out_hum",

    # Wind
    "Wind_Speed": "wind_speed",
    "Wind_Dir": "wind_dir",
    "Wind_Run": "wind_run",
    "Hi_Speed": "hi_speed",
    "Hi_Dir": "hi_dir",
    "Wind_Samp": "wind_samp",
    "Wind_Tx": "wind_tx",

    # Pressure (note: two trailing spaces in CSV header)
    "Bar  ": "bar",

    # Rain
    "Rain": "rain",
    "Rain_Rate": "rain_rate",

    # Solar / UV
    "Solar_Rad": "solar_rad",
    "Solar_Energy": "solar_energy",
    "Hi Solar_Rad": "hi_solar_rad",
    "UV_Index": "uv_index",
    "UV_Dose": "uv_dose",
    "Hi_UV": "hi_uv",

    # Degree days
    "Heat_D-D": "heat_dd",
    "Cool_D-D": "cool_dd",

    # Indoor
    "In_Temp": "in_temp",
    "In_Hum": "in_hum",
    "In_Dew": "in_dew",
    "In_Heat": "in_heat",
    "In_EMC": "in_emc",
    "InAir_Density": "inair_density",

    # ET (note: one trailing space in CSV header)
    "ET ": "et",

    # Station metadata
    "ISS_Recept": "iss_recept",
    "Arc_Int": "arc_int",
}
