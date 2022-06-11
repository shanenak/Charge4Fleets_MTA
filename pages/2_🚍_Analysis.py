# from attr import s
import streamlit as st 
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import visualizations as vis
import math
st.set_page_config(page_title='Energy Analysis', page_icon=':oncoming_bus:', layout="wide", initial_sidebar_state="auto", menu_items=None)

convert_from_miles = 1609.34
convert_from_km_to_miles = 0.621371
convert_from_km_to_meters = 1000
convert_from_feet = 0.3048
convert_from_joules = 1/(3.6e6)

ANALYSIS_FEATURE = 'route_id'
st.title('Charge4Fleets &trade;')
st.caption('Digital tool for electrification in collaboration with MTA and NYCERDA')

stops_df = pd.read_csv('trips_3serviceids.csv')

st.write('')
# selected_route = st.selectbox('Select Route', stops_df['route_id'].unique())
with st.expander('Customize parameters for energy analysis', False):
    if st.checkbox('Select a new vehicle type for operational assumptions', False):
        electric_bus_inventory = pd.read_csv('electric_bus_inventory.csv')
        selected_type = st.selectbox('Type of bus', electric_bus_inventory['type'].unique(), index = 1)
        selected_bus = st.selectbox('Model name', electric_bus_inventory.loc[electric_bus_inventory['type']==selected_type, 'model_name'], index = 3)
        vehicle_type_selected = electric_bus_inventory.loc[electric_bus_inventory['model_name'] == selected_bus]
        st.session_state.vehicle_type_selected = vehicle_type_selected
        st.session_state.params['bus_mass'] = vehicle_type_selected['curb_weight'].iloc[0] + vehicle_type_selected['max_passenger_load'].iloc[0]*170
        st.session_state.params['bus_mass_kg'] = st.session_state.params['bus_mass']*0.453592
        st.session_state.params['bus_battery'] = float(vehicle_type_selected['battery_capacity'].iloc[0])
        st.session_state.params['front_area'] = vehicle_type_selected['height'].iloc[0]*vehicle_type_selected['width_no_mirrors'].iloc[0]
    st.caption('The default bus type is highlighted below. ')
    st.write(st.session_state['formatted_bus_inventory'].style.apply(vis.highlight_bus_row, axis=0))
    st.write('')
    st.write('')
    st.markdown('###### Select operational parameters')
    st.session_state.params['battery_efficiency'] = st.number_input('Battery efficiency between 1.5 and 5 (kWh/mi)', min_value=1.5, max_value=5.0, value=st.session_state.params['battery_efficiency'], step=0.1)
    col1, col2 = st.columns([1,4])
    with col1:
        st.write('')
        st.write('')
        st.session_state.params['HVAC_enabled'] = st.checkbox('Include HVAC', st.session_state.params['HVAC_enabled'], key='hvac')
        st.write('')
        st.write('')
    with col2:
        if st.session_state.params['HVAC_enabled']:
            st.session_state.params['HVAC_efficiency'] = st.number_input('HVAC efficiency between 0 and 1 (kWh/mi)', min_value=0.00, max_value=1.00, value=st.session_state.params['HVAC_efficiency'], step=0.05)
    with col1:
        st.write('')
        st.session_state.params['regen_enabled'] = st.checkbox('Include regenerative braking', st.session_state.params['regen_enabled'], key='regen')
    with col2:
        if st.session_state.params['regen_enabled']:
            st.session_state.params['regen_efficiency'] = st.number_input('Regeneration efficiency between 0% and 100%', min_value=0.00, max_value=1.00, value=st.session_state.params['regen_efficiency'], step=0.01)


def energy_analysis(stops_df: pd.DataFrame, params: dict): 
    # TO BE REPLACED - departure times are duplicated. Cannot sort on departure times, sort on distance_traveled. For now, zeroing dist_traveled until can be data input again.
    stops_df.loc[stops_df['dist_traveled']<0, 'dist_traveled'] = 0.0
    
    # 1. Distance_based energy consumption
    stops_df['energy_distance'] = params['battery_efficiency']*stops_df['dist_traveled']*convert_from_km_to_miles
    stops_df['energy_distance'].fillna(0, inplace=True)

    # 2. Distance-based HVAC energy consumption
    stops_df['energy_HVAC'] = params['HVAC_efficiency']*stops_df['dist_traveled']*convert_from_km_to_miles
    
    # 3. Elevation-based energy consumption with or without regeneration. From gradient force to joules to kWh. Taken from physics engine.
    stops_df['gradient_force'] = stops_df.apply(lambda x: params['bus_mass_kg']*9.81*math.sin(math.atan2(x['elevation'],x['dist_traveled']*convert_from_km_to_meters)), axis=1)
    stops_df['energy_elevation'] = stops_df['gradient_force']*stops_df['dist_traveled']*convert_from_joules*convert_from_km_to_meters
    # Consider regeneration
    stops_df['energy_regen'] = stops_df['energy_elevation']
    stops_df.loc[stops_df['elevation']<0, 'energy_regen'] = stops_df['energy_elevation']*params['regen_efficiency']
    stops_df['energy_no_regen'] = stops_df['energy_elevation']
    stops_df.loc[stops_df['elevation']<0, 'energy_no_regen'] = 0.0

    # 4. Total energy demand
    stops_df['energy_used_between_stops'] = stops_df['energy_distance']
    if params['HVAC_enabled']:
        stops_df['energy_used_between_stops']+=stops_df['energy_HVAC']
    if params['regen_enabled']:
        stops_df['energy_used_between_stops']+=stops_df['energy_regen']

    else:
        stops_df['energy_used_between_stops']+=stops_df['energy_no_regen']

    # 5. Calculate remaining battery

    stops_df.sort_values(by=['trip_id', 'start_time'], inplace=True)
    stops_df['energy_used'] = stops_df.groupby('trip_id')['energy_used_between_stops'].transform(pd.Series.cumsum)

    stops_df['battery_energy_remaining'] = params['bus_battery'] - stops_df['energy_used']
    stops_df['SOC'] = stops_df['battery_energy_remaining']/params['bus_battery']
    stops_df['SOC_percent']= pd.to_numeric(stops_df['SOC'], errors='coerce')

    # ENVIRONMENT ANALYSIS OMITTED FOR THIS PHASE
    # if params['environment'] == 'Rural':
    #     stops_df['baseline_energy_Environ'] = stops_df['baseline_energy_HVAC']*1 #1.04 - not been able to find evidence for this being needed
    # elif params['environment'] == 'Semi_Urban':
    #     stops_df['baseline_energy_Environ'] = stops_df['baseline_energy_HVAC']*1 # 1.09 - not been able to find evidence for this being needed
    # else:
    #     stops_df['baseline_energy_Environ'] = stops_df['baseline_energy_HVAC']*1 # 1.2 - not been able to find evidence for this being needed

    return stops_df

def make_scatters(capacity_df:pd.DataFrame):
    fig = make_subplots(rows=1, cols=2,
                        # column_widths = [0.5, 0.5],
                        # row_heights = [0.5, 0.5],
                        # horizontal_spacing = 0.05,
                        # vertical_spacing = 0.05,
                        subplot_titles=("Buses able to charge by hour for TPSS & Third Rail Options", 
                                        "Energy demand against TPSS & Third Rail Capacity",
                                        ),
                        specs=[[{"type": "xy"},{"type": "xy"}]]
                        )

    fig.add_trace(
        vis.make_scatter_capacity(capacity_df, 'third_rail_capacityBuses', 'Third Rail capacity', 'Purple', False),
        row = 1, col = 1
    )        
    fig.add_trace(
        vis.make_scatter_capacity(capacity_df, 'TPSS_capacityBuses', 'TPSS capacity', 'ForestGreen', False),
        row = 1, col = 1
    )
    fig.add_trace(
        vis.make_bar_capacity(capacity_df, 'buses_charging', 'Buses Charging', 'Navy', False),
        row = 1, col = 1
    )
    fig.add_trace(
        vis.make_scatter_capacity(capacity_df, 'third_rail_capacityMW', 'Third Rail capacity', 'Purple', True),
        row = 1, col = 2
    )        
    fig.add_trace(
        vis.make_scatter_capacity(capacity_df, 'TPSS_capacityMW', 'TPSS capacity','ForestGreen', True),
        row = 1, col = 2
    )
    fig.add_trace(
        vis.make_bar_capacity(capacity_df, 'energy_demandMW', 'Demand', 'Navy',True),
        row = 1, col = 2
    )
    fig.add_trace(
        vis.make_scatter_capacity(capacity_df, 'max_energy_demand', 'Max Energy Demand', 'Red', True),
        row = 1, col = 2
    )        
    fig.add_trace(
        vis.make_scatter_capacity(capacity_df, 'average_energy_demand', 'Average Energy Demand','Orange', True),
        row = 1, col = 2
    )
        
    updatemenu= []    
    layout = dict(
        height = 600,
        # margin = dict(t = 1, b = 0, l = 0, r = 0),
        xaxis_tickformat = "%H:%M",
        xaxis2_tickformat = "%H:%M",
        xaxis = dict(title = "Time of Day"),
        xaxis2 = dict(title = "Time of Day"),
        yaxis = dict(title = "Capacity in number of buses"),
        yaxis2 = dict(title = "Energy Demand (MW)"),
        legend_title_text = 'Legend'
        )

    fig.update_layout(
        layout
    )
    return fig





st.write('')
energy_stops_df = energy_analysis(stops_df, st.session_state.params)

st.warning('Note: Analysis shown here is for demonstration purposes only. Calculations will be refined as more data is collected.')
st.write('')
st.markdown('##### Where are there areas of low State of Charge?')
st.caption('This heatmap shows where there are concentrations of stops with low State of Charge. Highlighted areas may be strategic locations to place on-route charging.')
st.write('')
st.markdown('###### Select range for charging analysis')
# st.dataframe(energy_stops_df)
heatmap_limits = st.slider('View concentration of stops within State of Charge (%)', 
                            min_value=0, 
                            max_value=round(energy_stops_df['SOC_percent'].max()*100), 
                            value= [0, st.session_state['SOC_min']],
                            format="%d%%"
                            )
heatmap_stops_df = energy_stops_df.loc[(energy_stops_df['SOC_percent']>(heatmap_limits[0]/100))&(energy_stops_df['SOC_percent']<(heatmap_limits[1]/100))]
heat_fig = vis.make_heatmapbox(heatmap_stops_df, 'SOC_percent')
st.plotly_chart(heat_fig, use_container_width=True)

capacity_df = pd.read_csv('Final_BEB Battery Calculations.csv')
st.write('')
st.markdown('##### How can buses charge?')
st.caption('These graphs show for TPSS and Third Rail how buses could charge throughout the day. The number of buses charging has been approximated with the number of headways provided [here](https://new.mta.info/document/14111).')
summary_fig = make_scatters(capacity_df)
st.plotly_chart(summary_fig, use_container_width=True)