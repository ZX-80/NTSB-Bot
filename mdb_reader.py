#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reads the relevant mdb files and creates the formatted reports to submit"""

import pyodbc
import string

from pathlib import Path
from typing import Iterator
from datetime import datetime, date

cursor = None

def sanitize_row(row):
    """Replace any Null strings with None."""
    for attr in row.cursor_description:
        if getattr(row, attr[0]) in ["NONE", "None"]:
            setattr(row, attr[0], None)

def generate_title(event_id: str) -> str:
    """Generate a title of the form: [Injury Severity] [Event Date] Make
    Model, City/ State Country."""

    cursor.execute(f"""
        SELECT
            events.ev_id,
            events.inj_tot_t,
            events.inj_tot_f,
            events.inj_tot_s,
            events.inj_tot_m,
            events.inj_tot_n,
            events.inj_f_grnd,
            events.inj_s_grnd,
            events.inj_m_grnd,
            events.ev_date,
            aircraft.acft_make,
            aircraft.acft_model,
            events.ev_city,
            events.ev_state,
            events.ev_country
        FROM
            events,
            aircraft
        WHERE
            events.ev_id = '{event_id}' and
            aircraft.ev_id = '{event_id}'
        ;
        """)
    
    # Construct a title from the first row, or return None if there's no data
    for row in cursor.fetchall():
        sanitize_row(row)
        title = ''
        # Injuries
        if row.inj_tot_t is not None:
            inj_f = (row.inj_tot_f or 0) + (row.inj_f_grnd or 0)
            inj_s = (row.inj_tot_s or 0) + (row.inj_s_grnd or 0)
            inj_m = (row.inj_tot_m or 0) + (row.inj_m_grnd or 0)
            inj_n = (row.inj_tot_n or 0)
            injury_list = []
            if inj_f > 0: injury_list.append(f'{inj_f} Fatal')
            if inj_s > 0: injury_list.append(f'{inj_s} Serious')
            if inj_m > 0: injury_list.append(f'{inj_m} Minor')
            if inj_n > 0: injury_list.append(f'{inj_n} None')
            title += '[' + ', '.join(injury_list) + '] '
        # Date
        if row.ev_date is not None:
            title += row.ev_date.strftime("[%B %d %Y] ") 
        # Make / Model
        if row.acft_make is not None: title += f"{row.acft_make} "
        if row.acft_model is not None: title += f"{row.acft_model} "
        # Location
        if len(title) > 0 and (row.ev_city is not None or row.ev_state is not None or row.ev_country is not None):
            title = title[:-1] + ', '
        if row.ev_city is not None: title += f"{row.ev_city}/ "
        if row.ev_state is not None: title += f"{row.ev_state} "
        if row.ev_country is not None: title += f"{row.ev_country} "

        return title

def generate_description(event_id: str) -> str:
    """Generate a description of the event that includes the Preliminary,
    Final, Probable Cause, and Incident narrative."""

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

    # Construct a description from the first row, or return None if there's no data
    for row in cursor.fetchall():
        sanitize_row(row)
        description = ''
        if row.narr_accp is not None:
            description += f"# NTSB Preliminary Narrative\n\n{row.narr_accp}\n\n"
        if row.narr_accf is not None:
            description += f"# NTSB Final Narrative\n\n{row.narr_accf}\n\n"
        if row.narr_cause is not None:
            description += f"# NTSB Probable Cause Narrative\n\n{row.narr_cause}\n\n"
        if row.narr_inc is not None:
            description += f"# FAA Incident Narrative\n\n{row.narr_inc}\n\n"

        if len(description) > 0: 
            return description + '---\n\n'
        return None

def aircraft_operator_info(event_id: str) -> str:
    """Generate the aircraft and owner/operator information table."""

    cursor.execute(f"""
        SELECT
            acft_make,
            regis_no,
            acft_model,
            acft_series,
            acft_category,
            homebuilt
        FROM
            aircraft
        WHERE
            ev_id = '{event_id}'
        ;
        """)

    # Construct the Aircraft and Owner/Operator Information from the first row, or return None if there's no data
    for row in cursor.fetchall():
        sanitize_row(row)
        
        model_series = []
        if row.acft_model is not None: model_series.append(str(row.acft_model))
        if row.acft_series is not None: model_series.append(str(row.acft_series))
        model_series = ' / '.join(model_series) if len(model_series) > 0 else None

        return f"""## **Aircraft and Owner/Operator Information**
Category|Data|Category|Data
:--|:--|:--|:--
Aircraft Make: | {row.acft_make or ''} | Registration: | {row.regis_no or ''} 
Model/Series: | {model_series or ''} | Aircraft Category: | {row.acft_category or ''} 
Amateur Built: | {row.homebuilt or ''} |\n\n"""

def meteorological_info(event_id: str) -> str:
    """Generate the meteorological information and flight plan table."""

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

    # Construct the Meteorological Information and Flight Plan from the first row, or return None if there's no data
    for row in cursor.fetchall():
        sanitize_row(row)

        if row.altimeter is not None: row.altimeter = round(row.altimeter, 2)

        # wx_obs_fac_id, wx_obs_elev ft MSL
        obs_facility = []
        if row.wx_obs_fac_id is not None: obs_facility.append(str(row.wx_obs_fac_id))
        if row.wx_obs_elev is not None: obs_facility.append(f"{row.wx_obs_elev} ft MSL")
        obs_facility = ', '.join(obs_facility) if len(obs_facility) > 0 else None

        # wx_obs_dist nautical miles
        obs_dist = f"{row.wx_obs_dist} nautical miles" if row.wx_obs_dist is not None else None

        # wx_temp°F / wx_dew_pt°F
        temp = []
        if row.wx_temp is not None: temp.append(f"{row.wx_temp}°F")
        if row.wx_dew_pt is not None: temp.append(f"{row.wx_dew_pt}°F")
        temp = ' / '.join(temp) if len(temp) > 0 else None

        # sky_cond_nonceil, sky_nonceil_ht ft AGL
        lowest_cloud = []
        if row.sky_cond_nonceil is not None: lowest_cloud.append(str(row.sky_cond_nonceil))
        if row.sky_nonceil_ht is not None: lowest_cloud.append(f"{row.sky_nonceil_ht} ft AGL")
        lowest_cloud = ', '.join(lowest_cloud) if len(lowest_cloud) > 0 else None

        # wind_vel_kts / gust_kts knots, wind_dir_deg°
        wind = []
        if row.wind_vel_kts is not None: wind.append(str(row.wind_vel_kts))
        if row.gust_kts is not None: wind.append(str(row.gust_kts))
        wind = ' / '.join(wind) + ' knots' if len(wind) > 0 else None
        if row.wind_dir_deg is not None:
            if wind is not None: wind += ', '
            wind += f"{row.wind_dir_deg}°"

        # sky_cond_ceil / sky_ceil_ht ft AGL
        lowest_ceil = []
        if row.sky_cond_ceil is not None: lowest_ceil.append(str(row.sky_cond_ceil))
        if row.sky_ceil_ht is not None: lowest_ceil.append(f"{row.sky_ceil_ht} ft AGL")
        lowest_ceil = ' / '.join(lowest_ceil) if len(lowest_ceil) > 0 else None

        # vis_sm Statute Miles
        vis = f"{row.vis_sm:.0f} statute miles" if row.vis_sm is not None else None

        # altimeter inches Hg
        alt = f"{row.altimeter} inches Hg" if row.altimeter is not None else None

        # dprt_city, dprt_state, dprt_country
        departure = []
        if row.dprt_city is not None: departure.append(str(row.dprt_city))
        if row.dprt_state is not None: departure.append(str(row.dprt_state))
        if row.dprt_country is not None: departure.append(str(row.dprt_country))
        departure = ', '.join(departure) if len(departure) > 0 else None

        # dest_city, dest_state, dest_country
        destination = []
        if row.dest_city is not None: destination.append(str(row.dest_city))
        if row.dest_state is not None: destination.append(str(row.dest_state))
        if row.dest_country is not None: destination.append(str(row.dest_country))
        destination = ', '.join(destination) if len(destination) > 0 else None
        
        return f"""## **Meteorological Information and Flight Plan**
Category|Data|Category|Data
:--|:--|:--|:--
Conditions at Accident Site: | {row.wx_cond_basic or ''} | Condition of Light: | {row.light_cond or ''}
Observation Facility, Elevation: | {obs_facility or ''} | Observation Time: | {row.wx_obs_time or ''} {row.wx_obs_tmzn or ''}
Distance from Accident Site: | {obs_dist or ''} | Temperature/Dew Point: | {temp or ''}
Lowest Cloud Condition: | {lowest_cloud or ''} | Wind Speed/Gusts, Direction: | {wind or ''}
Lowest Ceiling: | {lowest_ceil or ''} | Visibility: | {vis or ''}
Altimeter Setting: | {alt or ''} | Type of Flight Plan Filed: | {row.flt_plan_filed or ''}  
Departure Point: | {departure or ''} | Destination: | {destination or ''}
METAR: | {row.metar or ''} | |\n\n"""

def wreckage_and_impact_info(event_id: str) -> str:
    """Generate the wreckage and impact information table."""

    crew_inj_f = 0
    crew_inj_s = 0
    crew_inj_m = 0
    crew_inj_n = 0
    pass_inj_f = 0
    pass_inj_s = 0
    pass_inj_m = 0
    pass_inj_n = 0
    cursor.execute(f"""
        SELECT
            injury_level,
            inj_person_count,
            inj_person_category
        FROM
            injury
        WHERE
            ev_id = '{event_id}'
        ;
        """)
    for row in cursor.fetchall():
        if row.inj_person_category == 'Crew':
            if row.injury_level == "FATL":
                crew_inj_f = row.inj_person_count
            elif row.injury_level == "SERS":
                crew_inj_s = row.inj_person_count
            elif row.injury_level == "MINR":
                crew_inj_m = row.inj_person_count
            elif row.injury_level == "NONE":
                crew_inj_n = row.inj_person_count
        elif row.inj_person_category == 'Pass':
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
            inj_f_grnd,
            inj_m_grnd,
            inj_s_grnd,
            inj_tot_f,
            inj_tot_m,
            inj_tot_n,
            inj_tot_s,
            inj_tot_t,
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

    # Construct the Wreckage and Impact Information from the first row, or return None if there's no data
    for row in cursor.fetchall():
        sanitize_row(row)

        crew_inj = []
        if crew_inj_f > 0: crew_inj.append(f'{crew_inj_f} Fatal')
        if crew_inj_s > 0: crew_inj.append(f'{crew_inj_s} Serious')
        if crew_inj_m > 0: crew_inj.append(f'{crew_inj_m} Minor')
        if crew_inj_n > 0: crew_inj.append(f'{crew_inj_n} None')
        crew_inj = ', '.join(crew_inj)

        pass_inj = []
        if pass_inj_f > 0: pass_inj.append(f'{pass_inj_f} Fatal')
        if pass_inj_s > 0: pass_inj.append(f'{pass_inj_s} Serious')
        if pass_inj_m > 0: pass_inj.append(f'{pass_inj_m} Minor')
        if pass_inj_n > 0: pass_inj.append(f'{pass_inj_n} None')
        pass_inj = ', '.join(pass_inj)

        gnd_inj = []
        if row.inj_f_grnd or 0 > 0: gnd_inj.append(f'{row.inj_f_grnd} Fatal')
        if row.inj_s_grnd or 0 > 0: gnd_inj.append(f'{row.inj_s_grnd} Serious')
        if row.inj_m_grnd or 0 > 0: gnd_inj.append(f'{row.inj_m_grnd} Minor')
        gnd_inj = ', '.join(gnd_inj)

        tot_inj = []
        if row.inj_tot_f or 0 > 0: tot_inj.append(f'{row.inj_tot_f} Fatal')
        if row.inj_tot_s or 0 > 0: tot_inj.append(f'{row.inj_tot_s} Serious')
        if row.inj_tot_m or 0 > 0: tot_inj.append(f'{row.inj_tot_m} Minor')
        if row.inj_tot_n or 0 > 0: tot_inj.append(f'{row.inj_tot_n} None')
        tot_inj = ', '.join(tot_inj)

        location = []
        if row.latitude is not None: location.append(str(row.latitude))
        if row.longitude is not None: location.append(str(row.longitude))
        location = ', '.join(location)

        return f"""## **Wreckage and Impact Information**
Category|Data|Category|Data
:--|:--|:--|:--
Crew Injuries: | {crew_inj} | Aircraft Damage: | {row.damage or ''} 
Passenger Injuries: | {pass_inj} | Aircraft Fire: | {row.acft_fire or ''}  
Ground Injuries: | {gnd_inj} | Aircraft Explosion: | {row.acft_expl or ''}  
Total Injuries: | {tot_inj} | Latitude, Longitude: | {location}\n\n"""

def generate_signature(event_id: str) -> str:
    """Add a signature, and list the NTSB number for searching with CAROL."""

    cursor.execute(f"""
        SELECT
            ntsb_no
        FROM
            events
        WHERE
            events.ev_id = '{event_id}'
        ;
        """)
    
    ntsb_no = cursor.fetchone().ntsb_no
    if ntsb_no in ["NONE", "None", None]:
        ntsb_no = "No data"

    return f"""\n\n---\n\n
Generated by NTSB Bot Mk. 5\n
The docket, full report, and other information for this event can be found by searching the NTSB's Query Tool, [CAROL](https://data.ntsb.gov/carol-main-public/basic-search) (Case Analysis and Reporting Online), with the NTSB Number **{ntsb_no}**
"""

class Report:
    """
    Represents a formatted accident report in markdown

    Attributes
    ----------
    date : str
        the date encoded in the event ID
    event_id : str
        the event ID with the date stripped
    ntsb_no : str
        the NTSB number for this event
    title : str
        the submission title
    text : str
        the submission body
    """
    def __init__(self, event_id: str, ntsb_no: str) -> None:
        self.date = event_id[:8]
        self.event_id = event_id[8:]
        self.ntsb_no = ntsb_no
        self.title = ''
        self.text = ''

def parse_events(epoch: date, mdb_filepath: Path) -> Iterator[int | Report]:
    """Generate the aircraft and owner/operator information table.
    The first element returned is the amount of reports available.
    The remaining elements returned are the reports."""
    global cursor

    # connect to db
    DRV = '{Microsoft Access Driver (*.mdb, *.accdb)}' # Microsoft Access Driver (*.mdb)
    cursor = pyodbc.connect(f'DRIVER={DRV};DBQ={mdb_filepath};').cursor()

    cursor.execute(f"""
        SELECT
            ev_id,
            ntsb_no,
            lchg_date
        FROM
            events
        WHERE
            lchg_date >= #{epoch.strftime("%m/%d/%Y")}#
        ;
        """)
    relevant_events = cursor.fetchall()
    yield len(relevant_events)
    for row in relevant_events:
        if row.ev_id not in ["NONE", "None", None]:
            report = Report(row.ev_id, row.ntsb_no)

            report.title = generate_title(row.ev_id)
            report.title = ''.join(filter(lambda x: x in set(string.printable), report.title))

            description = generate_description(row.ev_id) or ''

            tables = aircraft_operator_info(row.ev_id) or ''
            tables += meteorological_info(row.ev_id) or ''
            tables += wreckage_and_impact_info(row.ev_id) or ''
            tables += generate_signature(row.ev_id) or ''

            # Sanitize text, replacing utf-8 quotes with ascii quotes and limiting text size to <40000
            size_limit = 40000 - len(tables) - 1
            report.text = description[:size_limit - 3] + '...' * (len(description) > size_limit) + tables
            report.text = report.text.replace('\xEF\xAC\x81','"').replace('\xEF\xAC\x82','"').replace('\xE2\x84\xA2','\'').replace('\xEF\xBF\xBD','\N{degree sign}')

            yield report

if __name__ == "__main__":
    EPOCH = date.fromisoformat('2022-04-01') # YYYY-MM-DD
    events = parse_events(EPOCH, Path('Aviation_Data/avall.mdb'))
    for count, report_or_len in enumerate(events):
        if count == 0:
            print(f"{report_or_len} event(s)")
        else:
            print(report_or_len.title)
            print(report_or_len.text)
            print('='*80)
        if count == 9: break # Output 9 events
