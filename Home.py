# from attr import s
import streamlit as st 
import pandas as pd
# import geopandas as gpd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import visualizations as vis

### SET-UP PAGE
st.set_page_config(page_title='Charge4Fleets', page_icon=':oncoming_bus:', layout="wide", initial_sidebar_state="auto", menu_items=None)
st.title('Charge4Fleets &trade;')
st.caption('Digital tool for electrification in collaboration with MTA and NYCERDA')
# st.sidebar.write('''
#            Assumptions for preliminary analysis:
#            - Routes serviced by Jackie Gleason Depot are limited to the following B4, B8, B9, B11, B16, B35, B37, B43, B61, B63, B67,B68, B69, B70
#            - Trips to and from Jackie Gleason have been indicated with "JG" in the trip id
#            - Weekday service is sufficient for conservative estimates
#            ''')

### CONSTANTS
PRIMARY_FEATURE = 'trip_name'
ANALYSIS_FEATURE = 'route_id'
TOKEN = "pk.eyJ1Ijoic2hhbm5vbm5ha2FtdXJhIiwiYSI6ImNrbG9zbG44OTB2d2Eyd20yc3FkYXVib3oifQ.Mck3r247wz8bgWvROUi_ww"
convert_from_lbs_to_kg = 0.453592
average_weight_of_person = 170 #lbs

### LOAD DATA
unique_trips = pd.read_csv('unique_stop_sequences.csv')
unique_trips['trip_name'] = unique_trips['trip_id'].str.split(pat='_', expand=True)[2]


def on_launch():
    st.session_state['filter_bus'] = []
    st.session_state['filter_route'] = ['1237']
    
    electric_bus_inventory = pd.read_csv('electric_bus_inventory.csv')
    st.session_state['formatted_bus_inventory'] = electric_bus_inventory.rename(columns={'type': 'Type', 'model_name':'Model Name', 'manufacturer':'Manufacturer', 'battery_capacity':'Battery Capacity (kWh)', 'length':'Length (ft)', 'max_passenger_load':'Max. Passenger Load'})
    st.session_state['formatted_bus_inventory'] = st.session_state['formatted_bus_inventory'][['Type', 'Model Name', 'Manufacturer', 'Battery Capacity (kWh)', 'Length (ft)', 'Max. Passenger Load']].set_index('Model Name')
    st.session_state['formatted_bus_inventory'].sort_values(by=['Type'], ascending=False, inplace=True)
    st.session_state['formatted_bus_inventory']['Length (ft)'] = st.session_state['formatted_bus_inventory']['Length (ft)'].round(1).map('{:,.1f}'.format)
    selected_type = electric_bus_inventory['type'].unique()[1]
    selected_bus = electric_bus_inventory.loc[electric_bus_inventory['type']==selected_type, 'model_name'].iloc[0]
    vehicle_type_selected = electric_bus_inventory.loc[electric_bus_inventory['model_name'] == selected_bus]
    st.session_state.vehicle_type_selected = vehicle_type_selected
    st.session_state.params = {}
    st.session_state.params['bus_mass'] = vehicle_type_selected['curb_weight'].iloc[0] + vehicle_type_selected['max_passenger_load'].iloc[0]*average_weight_of_person
    st.session_state.params['bus_mass_kg'] = st.session_state.params['bus_mass']*convert_from_lbs_to_kg
    st.session_state.params['bus_battery'] = float(vehicle_type_selected['battery_capacity'].iloc[0])
        
    st.session_state.params['front_area'] = vehicle_type_selected['height'].iloc[0]*vehicle_type_selected['width_no_mirrors'].iloc[0]

    st.session_state.params['battery_efficiency'] = 2.2 #kw-hr/mile
    st.session_state.params['regen_enabled'] = True
    st.session_state.params['regen_efficiency'] = 0.5
    st.session_state.params['HVAC_enabled'] = True
    st.session_state.params['HVAC_efficiency'] = 0.25
    
    st.session_state.SOC_min = 80

### VISUALIZATIONS
def make_map(unique_trips:pd.DataFrame):
    fig = make_subplots(rows=2, cols=2,
                        column_widths = [0.5, 0.5],
                        row_heights = [0.6, 0.4],
                        horizontal_spacing = 0.05,
                        vertical_spacing = 0.05,
                        subplot_titles=("Map of Stops", 
                                        "Elevation of Stops",
                                        "Max. elevation of each trip (m)"
                                        ),
                        specs=[[{"type": "mapbox", "colspan": 2}, None], 
                               [{"type": "scene"}, {"type": "xy"}]]
                        )

    for count, value in enumerate(sorted(unique_trips[PRIMARY_FEATURE].unique())):
        fig.add_trace(
            vis.make_scattermapbox(unique_trips, value),
            row = 1, col = 1
        )
        fig.add_trace(
            vis.make_scatter3d(unique_trips, value, False),
            row = 2, col = 1
        )
        fig.add_trace(
            vis.make_histogram(unique_trips, 'elevation', PRIMARY_FEATURE, value),
            row = 2, col = 2
        )
    fig.add_trace(
            vis.make_JG_location(unique_trips, value),
            row = 1, col = 1
        )

    updatemenu= []    
    layout = dict(
        height = 600,
        margin = dict(t = 1, b = 0, l = 0, r = 0),
        # legend_title_text = '<b> Block IDs </b>',
        xaxis = dict(title = "Max. elevation (in meters)"),
        yaxis = dict(title = "Trip ID"),
        mapbox = dict(
            accesstoken = TOKEN,
            center = dict(lon = np.mean(unique_trips['stop_lon']), lat = np.mean(unique_trips['stop_lat'])),
            pitch = 60,
            zoom = 11,
            style = 'dark'
            )
        )

    fig.update_layout(
        layout

    )
    return fig

def make_scatters(unique_trips:pd.DataFrame):
    fig = make_subplots(rows=1, cols=2,
                        # column_widths = [0.5, 0.5],
                        # row_heights = [0.5, 0.5],
                        # horizontal_spacing = 0.05,
                        # vertical_spacing = 0.05,
                        subplot_titles=("Number of trips starting by hour throughout the day", 
                                        "Total length of trips (in miles) by hour",
                                        ),
                        specs=[[{"type": "xy"},{"type": "xy"}]]
                        )

    for count, value in enumerate(sorted(unique_trips[ANALYSIS_FEATURE].unique())):
        fig.add_trace(
            vis.make_scatter_routes(unique_trips, value, True),
            row = 1, col = 1
        )        
        fig.add_trace(
            vis.make_scatter_length(unique_trips, value, False),
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
        yaxis = dict(title = "Trips starting by route"),
        yaxis2 = dict(title = "Length of trips (miles)"),
        legend_title_text = 'Route IDs'
        )

    fig.update_layout(
        layout
    )
    return fig


on_launch()
st.write('')
st.markdown('##### Which buses are served by Jackie Gleason Depot?')
st.caption('Trips are shown here that stop at Jackie Gleason Depot. Trip data comes from GTFS [here](https://transitfeeds.com/p/mta/80')
summary_fig = make_map(unique_trips)
st.plotly_chart(summary_fig, use_container_width=True)

stops_df = pd.read_csv('trips_3serviceids.csv')
st.write('')
st.markdown('##### How do trips vary throughout the day?')
st.caption('Trips to be assigned to vehicles in next round of analysis. Trips have been filtered by route and service to isolate those serviced by Jackie Gleason Depot.')
summary_fig = make_scatters(stops_df.sort_values(by='route_id'))
st.plotly_chart(summary_fig, use_container_width=True)
