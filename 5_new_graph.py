import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as poi
poi.renderers.default = 'browser'  # режим отображения в браузере 
# импорт библиотек dash
import dash 
from dash import dcc  # в этой библиотеке находятся слайдеры и прочее
from dash import html
import dash_bootstrap_components as dbc
# импортируем компоненты для того, чтобы график реагировал на изменения
from dash import Input, Output 

"""" READ DATA """

response = requests.get('http://asterank.com/api/kepler?query={}&limit=2000')  # с помощью API считываем данные с сайта sterank.com/kepler с пустым параметром запроса и лимитом в 2000
df = pd.json_normalize(response.json())  # нормализация json 
df = df[df['PER'] > 0]  # отрезаем нежелательную точку с периодом < 0

# Create Star size category 

bins = [0, 0.8, 1.2, 100]  # разбиваем на категории по метрикам сравнения с метриками солнце
names = ['small', 'similar', 'bigger']
df['StarSize'] = pd.cut(df['RSTAR'], bins, labels=names)

# TEMPERATURE BINS (бакеты по температуре планет)
tp_bins = [0, 200, 400, 500, 5000]
tp_labels = ['low', 'optimal', 'high', 'extreme']
df['temp'] = pd.cut(df['TPLANET'], tp_bins, labels = tp_labels) # задаем переменную. Разбиваем температуру по бинам + в зависимости от этого лейбл

#  SIZE_BINS (бакеты по размерам планеты в зависимости от радиуса Земли)

rp_bins = [0, 0.5, 2, 4, 100]
rp_labels = ['low', 'optimal', 'high', 'extreme']  # лейблы по бакетам
df['gravity'] = pd.cut(df['RPLANET'], rp_bins, labels = rp_labels)  # по аналогии делаем соответствие по радиусам 

#  ESTIMATE OBJECT STATUS (разбиваем объекты по статусам)
#  Если temp == optimal и gravity == optimal => promising
df['status'] = np.where((df['temp'] == 'optimal')
                        &(df['gravity'] == 'optimal'),
                        'promising', None) 
#  Если и не optimal, и не extreme, то challening для нас
df.loc[:, 'status'] = np.where((df['temp'] == 'optimal')&
                               (df['gravity'].isin(['low', 'high'])),
                                'challening', df['status']) 
df.loc[:, 'status'] = np.where((df['gravity'] == 'optimal')&
                               (df['temp'].isin(['low', 'high'])),
                                'challening', df['status']) 
#  В остальных случаях значение extreme
df['status'] = df.status.fillna('extreme')


options = []
for k in names:
    options.append({'label' : k, 'value' : k})

# print(df.head())  # вывод первых пяти строк датафрейма для проверки корректности его загрузки

# fig = px.scatter(df, x = 'TPLANET', y = 'A')  # считываем данные и строим скаттерплот по интересующим нас параметрам. Уже необязательно строить в теле приложеия

star_size_selector = dcc.Dropdown(
    id = 'star-selector',
    options = options,
    value = ['small', 'similar', 'bigger'], # категорию, выбранные по умолчанию в dropdown слайзере
    multi = True
)

# создаем слайсер
rplanet_selector = dcc.RangeSlider(
    id = 'range-slider',
    min = min(df['RPLANET']), # минимальное значение слайсера 
    max = max(df['RPLANET']),  # максимальное значение слайсера
    marks = {5: '5', 10 : '10', 20 : '20'},  # метки данных
    step = 1,
    value = [min(df['RPLANET']), max(df['RPLANET'])] # значения в слайсере "между" по умолчанию
)

app = dash.Dash(__name__,
                external_stylesheets = [dbc.themes.FLATLY]) # инициализация приложения

"""" LAYOUT """

app.layout = html.Div([
    dbc.Row(html.H1('Planets Dashboard'),
            style = {'margin-bottom' : 40}),
    dbc.Row([
        dbc.Col([
            html.Div('Select planet main semi-axis range'),
            html.Div(rplanet_selector)
        ],
            width = {'size' : 2}),
        dbc.Col([
            html.Div('Star Size '),
            html.Div(star_size_selector)
        ], 
            width = {'size' : 3, 'offset' : 1})
    ],
            style = {'margin-bottom' : 40}), 
    dbc.Row([
        dbc.Col([
            html.Div('Planet Temperature ~ Distance from the Star'),
            dcc.Graph(id = 'dist-temp-chart')
        ], 
            width = {'size' : 6}),
        dbc.Col([
            html.Div('Position on the Celestial Sphere'), # название для нового графика
            dcc.Graph(id = 'celestial-chart') # новый график
        ])
    ],
            style = {'margin-bottom' : 40}),
    ],
    style = {'margin-left' : '80px',
            'margin-right': '80px'})


# app.layout = html.Div([
#     html.H1('Hello Dash!'),  # вывод заголовка первого уровня 
#     html.Div('Select planet main semi-axis range'),
#     html.Div(rplanet_selector, 
#             style = {'width' : '400px',
#                     'margin-bottom' : '40px'}),  # включаем в график созданный нами слайдер
#     html.Div('Select star size'),
#     html.Div(star_size_selector, 
#             style = {'width' : '400px',
#                     'margin-bottom' : '40px'}), 
#     html.Div('Planet Temperature ~ Distance from the Star'),  # вывод названия графика
#     dcc.Graph(id = 'dist-temp-chart')  # вывод графика
# ],  # app.layout - фронтенд приложения. В нем используются элементы библиотек dcc и html
#     style = ({'margine-left' : '80px',
#             'margine-right' : '80px'}
# ))

"""" CALLBACK """

@app.callback(
    Output(component_id = 'dist-temp-chart', component_property = 'figure'),
    [Input(component_id = 'range-slider', component_property = 'value'),
    Input(component_id = 'star-selector', component_property = 'value')]
)
def update_dist_temp_chart(radius_range, star_size):
    chart_data = df[(df['RPLANET'] > radius_range[0]) &
                    (df['RPLANET'] < radius_range[1]) &
                    (df['StarSize'].isin(star_size))]
    fig = px.scatter(chart_data, x = 'TPLANET', y = 'A', color = 'StarSize')  # по x - Tplanet, по y - A, разбивка по цветам в зависимости от категории StarSize

    return fig 

# callback для нового графика

@app.callback(
    Output(component_id = 'celestial-chart', component_property = 'figure'),
    [Input(component_id = 'range-slider', component_property = 'value'),
    Input(component_id = 'star-selector', component_property = 'value')]
)
def update_dist_celestial_chart(radius_range, star_size):
    chart_data = df[(df['RPLANET'] > radius_range[0]) &
                    (df['RPLANET'] < radius_range[1]) &
                    (df['StarSize'].isin(star_size))]
    fig = px.scatter(chart_data, x = 'RA', y = 'DEC', size = 'RPLANET', 
                                                        color = 'status')  # по x - RA, по y - DEC, размер в зависимости от RPLANET, цвета в зависимости от Status

    return fig 

if __name__ == '__main__':
    app.run_server(debug=True)  # debug = True - запуск в тестовом режиме