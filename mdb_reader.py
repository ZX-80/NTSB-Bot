#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads the relevent mdb files and creates the formatted reports to submit"""

import pyodbc
import string
from datetime import datetime, date

# Globals
NO_DATA = ["NONE", None, 0]
conn = None
cursor = None

def generate_title(event_id):
    cursor.execute(f"""
        SELECT
            events.ntsb_no,
            events.ev_date,
            events.ev_id,
            events.inj_f_grnd,
            events.inj_m_grnd,
            events.inj_s_grnd,
            events.inj_tot_f,
            events.inj_tot_m,
            events.inj_tot_n,
            events.inj_tot_s,
            events.inj_tot_t,
            events.ev_city,
            events.ev_state,
            events.ev_country,
            aircraft.acft_make,
            aircraft.acft_model
        FROM
            events,
            aircraft
        WHERE
            events.ev_id = '{event_id}' and
            aircraft.ev_id = '{event_id}'
        ;
        """)
    

    for row in cursor.fetchall():
        title = ''
        if row.inj_tot_t not in NO_DATA:
            inj_f = (row.inj_tot_f or 0) + (row.inj_f_grnd or 0)
            inj_s = (row.inj_tot_s or 0) + (row.inj_s_grnd or 0)
            inj_m = (row.inj_tot_m or 0) + (row.inj_m_grnd or 0)
            inj_n = (row.inj_tot_n or 0)
            title += '['
            title += ', '.join(filter(None, [
                f'{inj_f} Fatal' * (inj_f > 0), 
                f'{inj_s} Serious' * (inj_s > 0),
                f'{inj_m} Minor' * (inj_m > 0),
                f'{inj_n} None' * (inj_n > 0)]))+ ']'
        title += row.ev_date.strftime(" [%B %d %Y] ")
        title += f"{row.acft_make} {row.acft_model}, {row.ev_city}/ {row.ev_state} {row.ev_country}"

        return title

def generate_description(event_id):
    cursor.execute(f"""
        SELECT
            narr_accp,
            narr_accf,
            narr_cause,
            narr_inc
        FROM
            narratives
        WHERE
            ev_id = '{event_id}'
        ;
        """)
    for row in cursor.fetchall():
        description = ''
        description += f"# NTSB Preliminary Narrative\n{row.narr_accp}\n" * (row.narr_accp != None)
        description += f"# NTSB Final Narrative\n{row.narr_accf}\n" * (row.narr_accf != None)
        description += f"# NTSB Probable Cause Narrative\n{row.narr_cause}\n" * (row.narr_cause != None)
        description += f"# FAA Incident Narrative\n{row.narr_inc}\n" * (row.narr_inc != None)

        return description + ('\n\n---' if len(description) > 0 else '')

def aircraft_operator_info(event_id):
    cursor.execute(f"""
        SELECT
            acft_make,
            acft_model,
            acft_series,
            regis_no,
            acft_category,
            homebuilt
        FROM
            aircraft
        WHERE
            ev_id = '{event_id}'
        ;
        """)
    for row in cursor.fetchall():
        return f"""## **Aircraft and Owner/Operator Information**
Category|Data|Category|Data
:--|:--|:--|:--
Aircraft Make: | {row.acft_make} | Registration: | {row.regis_no} 
Model/Series: | {row.acft_model} / {row.acft_series}   | Aircraft Category: | {row.acft_category} 
Amateur Built: | {row.homebuilt} |\n\n"""

def meteorological_info(event_id):
    cursor.execute(f"""
        SELECT
            wx_cond_basic,
            light_cond,
            wx_obs_fac_id, wx_obs_elev,
            wx_obs_time, wx_obs_tmzn,
            wx_obs_dist,
            wx_temp, wx_dew_pt,
            sky_cond_nonceil, sky_nonceil_ht,
            wind_vel_kts, gust_kts, wind_dir_deg,
            sky_cond_ceil, sky_ceil_ht,
            vis_sm,
            altimeter,
            flt_plan_filed,
            dprt_city, dprt_state, dprt_country,
            dest_city, dest_state, dest_country,
            metar
        FROM
            aircraft,
            events
        WHERE
            aircraft.ev_id = '{event_id}' and events.ev_id = '{event_id}'
        ;
        """)
    for row in cursor.fetchall():
        if type(row.altimeter) == float:
            row.altimeter = round(row.altimeter, 2)
        return f"""## **Meteorological Information and Flight Plan**
Category|Data|Category|Data
:--|:--|:--|:--
Conditions at Accident Site: | {row.wx_cond_basic}  | Condition of Light: | {row.light_cond} 
Observation Facility, Elevation: | {row.wx_obs_fac_id} , {row.wx_obs_elev} ft MSL  | Observation Time: | {row.wx_obs_time} {row.wx_obs_tmzn} 
Distance from Accident Site: | {row.wx_obs_dist} Nautical Miles  | Temperature/Dew Point: | {row.wx_temp}\N{degree sign}F / {row.wx_dew_pt}°F 
Lowest Cloud Condition: | {row.sky_cond_nonceil} / {row.sky_nonceil_ht} ft AGL  | Wind Speed/Gusts, Direction: | {row.wind_vel_kts} / {row.gust_kts} knots, {row.wind_dir_deg}° 
Lowest Ceiling: | {row.sky_cond_ceil} / {row.sky_ceil_ht} ft AGL | Visibility: | {row.vis_sm} Statute Miles 
Altimeter Setting: | {row.altimeter} inches Hg  | Type of Flight Plan Filed: | {row.flt_plan_filed}  
Departure Point: | {row.dprt_city}, {row.dprt_state}, {row.dprt_country} | Destination: | {row.dest_city}, {row.dest_state}, {row.dest_country}
METAR: | {row.metar} | |\n\n"""

def wreckage_and_impact_info(event_id):
    crew_inj_f = 0
    crew_inj_s = 0
    crew_inj_m = 0
    crew_inj_n = 0
    cursor.execute(f"SELECT injury_level, inj_person_count FROM injury WHERE inj_person_category = 'Crew' and ev_id = '{event_id}'")
    for row in cursor.fetchall():
        if row.injury_level == "FATL":
            crew_inj_f = row.inj_person_count
        elif row.injury_level == "SERS":
            crew_inj_s = row.inj_person_count
        elif row.injury_level == "MINR":
            crew_inj_m = row.inj_person_count
        elif row.injury_level == "NONE":
            crew_inj_n = row.inj_person_count

    pass_inj_f = 0
    pass_inj_s = 0
    pass_inj_m = 0
    pass_inj_n = 0
    cursor.execute(f"SELECT injury_level, inj_person_count FROM injury WHERE inj_person_category = 'Pass' and ev_id = '{event_id}'")
    for row in cursor.fetchall():
        if row.injury_level == "FATL":
            pass_inj_f = row.inj_person_count
        elif row.injury_level == "SERS":
            pass_inj_s = row.inj_person_count
        elif row.injury_level == "MINR":
            pass_inj_m = row.inj_person_count
        elif row.injury_level == "NONE":
            pass_inj_n = row.inj_person_count

    cursor.execute(f"""
        SELECT
            inj_f_grnd, inj_m_grnd, inj_s_grnd, inj_tot_f, inj_tot_m, inj_tot_n, inj_tot_s, inj_tot_t,
            damage,
            acft_fire,
            acft_expl,
            latitude,
            longitude
        FROM
            aircraft,
            events
        WHERE
            aircraft.ev_id = '{event_id}' and events.ev_id = '{event_id}'
        ;
        """)

    for row in cursor.fetchall():
        crew_inj = ', '.join(filter(None, [
            f'{crew_inj_f} Fatal' * (crew_inj_f > 0), 
            f'{crew_inj_s} Serious' * (crew_inj_s > 0),
            f'{crew_inj_m} Minor' * (crew_inj_m > 0),
            f'{crew_inj_n} None' * (crew_inj_n > 0)]))
        pass_inj = ', '.join(filter(None, [
            f'{pass_inj_f} Fatal' * (pass_inj_f > 0), 
            f'{pass_inj_s} Serious' * (pass_inj_s > 0),
            f'{pass_inj_m} Minor' * (pass_inj_m > 0),
            f'{pass_inj_n} None' * (pass_inj_n > 0)]))
        gnd_inj = ', '.join(filter(None, [
            f'{row.inj_f_grnd} Fatal' * (type(row.inj_f_grnd) == int and row.inj_f_grnd > 0), 
            f'{row.inj_s_grnd} Serious' * (type(row.inj_s_grnd) == int and row.inj_s_grnd > 0),
            f'{row.inj_m_grnd} Minor' * (type(row.inj_m_grnd) == int and row.inj_m_grnd > 0)]))
        tot_inj = ', '.join(filter(None, [
            f'{row.inj_tot_f} Fatal' * (type(row.inj_tot_f) == int and row.inj_tot_f > 0), 
            f'{row.inj_tot_s} Serious' * (type(row.inj_tot_s) == int and row.inj_tot_s > 0),
            f'{row.inj_tot_m} Minor' * (type(row.inj_tot_m) == int and row.inj_tot_m > 0),
            f'{row.inj_tot_n} None' * (type(row.inj_tot_n) == int and row.inj_tot_n > 0)]))

        if crew_inj == '': crew_inj = "None"
        if pass_inj == '': pass_inj = "None"
        if gnd_inj == '': gnd_inj = "None"
        if tot_inj == '': tot_inj = "None"

        return f"""## **Wreckage and Impact Information**
Category|Data|Category|Data
:--|:--|:--|:--
Crew Injuries: | {crew_inj} | Aircraft Damage: | {row.damage} 
Passenger Injuries: | {pass_inj} | Aircraft Fire: | {row.acft_fire}  
Ground Injuries: | {gnd_inj} | Aircraft Explosion: | {row.acft_expl}  
Total Injuries: | {tot_inj} | Latitude, Longitude: | {row.latitude}, {row.longitude}\n\n"""

def generate_signature(event_id):
    cursor.execute(f"SELECT ntsb_no FROM events WHERE events.ev_id = '{event_id}'")
    ntsb_no = "None"
    for row in cursor.fetchall():
        ntsb_no = row.ntsb_no
        break

    return f"""\n---\n
Generated by NTSB Bot Mk. 5\n
The docket, full report, and other information for this event can be found by searching the NTSB's Query Tool, [CAROL](https://data.ntsb.gov/carol-main-public/basic-search) (Case Analysis and Reporting Online), with the NTSB Number **{ntsb_no}**
"""

class Report:
    def __init__(self, event_id, ntsb_no) -> None:
        self.date = event_id[:4+2+2]
        self.event_id = event_id[4+2+2:]
        self.ntsb_no = ntsb_no
        self.title = ''
        self.text = ''

def parse_events(epoch, mdb_filepath):
    global conn, cursor

    # connect to db
    DRV = '{Microsoft Access Driver (*.mdb, *.accdb)}' # Microsoft Access Driver (*.mdb)
    conn = pyodbc.connect(f'DRIVER={DRV};DBQ={str(mdb_filepath)};')
    cursor = conn.cursor()

    cursor.execute(f'SELECT ev_id, ntsb_no, lchg_date FROM events WHERE (lchg_date >= #{epoch.strftime("%m/%d/%Y")}#);')  # MDY
    for row in cursor.fetchall():
        if len(row) == 0 or row.ev_id == None: continue
        report = Report(row.ev_id, row.ntsb_no)

        report.title = generate_title(row.ev_id)
        report.title = ''.join(filter(lambda x: x in set(string.printable), report.title))
        report.title = report.title.encode("ascii","ignore").decode('utf-8')

        description = '\n' + (generate_description(row.ev_id) or '')

        table = '\n\n' + aircraft_operator_info(row.ev_id) or ''
        table += '\n\n' + meteorological_info(row.ev_id) or ''
        table += '\n\n' + wreckage_and_impact_info(row.ev_id) or ''
        table += '\n\n' + generate_signature(row.ev_id) or ''

        # Sanitize text, replacing utf-8 quotes with ascii quotes and limiting text size to <40000
        report.text = description[:40000-len(table)-5] + '...' * (len(description) > (40000-len(table)-1)) + table
        report.text = report.text.replace('\xEF\xAC\x81','"').replace('\xEF\xAC\x82','"').replace('\xE2\x84\xA2','\'').replace('\xEF\xBF\xBD','\N{degree sign}')

        report.lchg_date = datetime.date(row.lchg_date)

        yield report

if __name__ == "__main__":
    count = 9 # Output 9 events
    EPOCH = date.fromisoformat('2022-04-01') # YYYY-MM-DD
    for document in parse_events(EPOCH):
        print(document.event_id)
        print(document.title)
        print(document.text)
        print('='*80)
        if (count := count - 1) == 0: break
