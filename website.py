from nicegui import ui
from fastapi import FastAPI
from db_connection import DBConnection
import plotly.graph_objects as go


DB = DBConnection()
select = ""


def create_station_graph(station_id_number: int):
    fig = go.Figure()
    # Retrieve data for the graph from the database
    station_name, date_list, motorina_standard_list, motorina_premium_list, benzina_standard_list, benzina_premium_list, \
        gpl_list = DB.retrieve_data_for_graph(station_id=station_id_number)
    # Add traces for each fuel type if there is data available
    if len(motorina_standard_list) > 0:
        fig.add_trace(go.Scatter(x=date_list,
                                 y=motorina_standard_list,
                                 name="Motorina Standard",
                                 line=dict(color='#808080', width=3)))
    if len(motorina_premium_list) > 0:
        fig.add_trace(go.Scatter(x=date_list,
                                 y=motorina_premium_list,
                                 name="Motorina Premium",
                                 line=dict(color='#0d0d0d', width=3)))
    if len(benzina_standard_list) > 0:
        fig.add_trace(go.Scatter(x=date_list,
                                 y=benzina_standard_list,
                                 name="Benzina Standard",
                                 line=dict(color='#ff0000', width=3)))
    if len(benzina_premium_list) > 0:
        fig.add_trace(go.Scatter(x=date_list,
                                 y=benzina_premium_list,
                                 name="Benzina Premium",
                                 line=dict(color='#00cc00', width=3)))
    if len(gpl_list) > 0:
        fig.add_trace(go.Scatter(x=date_list,
                                 y=gpl_list,
                                 name="GPL",
                                 line=dict(color='#e6e600', width=3)))
    # Update the layout to include range selector, rangeslider, and date type for x-axis
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label='7 zile', step='day', stepmode='backward'),
                    dict(count=30, label='30 zile', step='day', stepmode='backward'),
                    dict(step='all')
                ])),
            rangeslider=dict(visible=True),
            type='date'
        )
    )
    # Update the layout to adjust legend position and margins
    fig.update_layout(legend=dict(orientation="v", x=0, y=-1.3),    margin=dict(
        l=5,    # Adjust the left margin
        r=5,    # Adjust the right margin
        b=100,  # Increase the bottom margin
        t=50    # Adjust the top margin
    ),
                      autosize=True)

    return fig


# Store user input file selection
def update_selection(e):
    global select
    select = e.value


# Show the graph
def show_graph(selection):
    if selection == "":
        # Create blank graph and show it until station is selected
        fig = go.Figure()
        return fig
    else:
        # Show graph from the selected station
        return create_station_graph(station_id_number=DB.retrieve_station_id(name=select))


# with ui.column().classes("items-center w-full mb-10 my-2"):
#     ui.label("Pretul Combustibililor").classes("text-2xl font-medium tracking-wide text-fuchsia-700")
#
# with ui.row().classes('w-full justify-around my-0'):
#     with ui.column().classes("w-fit"):
#         ui.label("Selecteaza benzinaria din lista dropdown, apoi apasa butonul de sub grafic").\
#             classes("text-lg font-medium tracking-wide text-purple-600")
#         ui.label("Poti scrie in casuta pentru a micsora lista dropdown").\
#             classes("text-lg font-medium tracking-wide text-purple-600")
#         select_station = ui.select(options=DB.retrieve_all_stations_names_list(), with_input=True, on_change=update_selection).\
#             classes('w-screen bg-slate-900 text-left')
#         ui.button("Refresh", on_click=refresh).classes()
#
# with ui.row().classes('w-full justify-around'):
#     plot = ui.plotly(show_graph(select)).classes('w-screen')
# with ui.row().classes('w-full justify-around my-0'):
#     button = ui.button('Arata graficul', on_click=lambda: plot.update_figure(show_graph(select))).\
#         bind_visibility_from(select_station, "value").classes("w-fit mt-2 animate-bounce")
#
# ui.run(title="Fuel Price Analysis", dark=True, host="0.0.0.0", port=60)

@ui.page("/")
def page1():
    with ui.column().classes("items-center w-full mb-10 my-2"):
        ui.label("Pretul Combustibililor").classes("text-2xl font-medium tracking-wide text-fuchsia-700")

    with ui.row().classes('w-full justify-around my-0'):
        with ui.column().classes("w-fit"):
            ui.label("Selecteaza benzinaria din lista dropdown, apoi apasa butonul de sub grafic").\
                classes("text-lg font-medium tracking-wide text-purple-600")
            ui.label("Poti scrie in casuta pentru a micsora lista dropdown").\
                classes("text-lg font-medium tracking-wide text-purple-600")
            select_station = ui.select(options=DB.retrieve_all_stations_names_list(), with_input=True, on_change=update_selection).\
                classes('w-screen bg-slate-900 text-left')

    with ui.row().classes('w-full justify-around'):
        plot = ui.plotly(show_graph(select)).classes('w-screen')
    with ui.row().classes('w-full justify-around my-0'):
        ui.button('Arata graficul', on_click=lambda: plot.update_figure(show_graph(select))).\
            bind_visibility_from(select_station, "value").classes("w-fit mt-2 animate-bounce")


def init(fastapi_app: FastAPI) -> None:
    ui.run_with(fastapi_app)
