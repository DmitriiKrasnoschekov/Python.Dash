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
from dash import Input, Output, State 

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

# Relative distnacer (distance to SUN/SUM radius)
df.loc[:, 'relative_dist'] = df['A']/df['RSTAR']

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
    # header
    dbc.Row(html.H1('Planets Dashboard'),
            style = {'margin-bottom' : 40}),
    # filters
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
            width = {'size' : 3, 'offset' : 1}),
        dbc.Col(dbc.Button('Apply', id = 'submit-val', n_clicks = 0, 
                            className = 'mr-2'))  # кнопка + результат для кнопки и оформление
    ],
            style = {'margin-bottom' : 40}),
    # charts 
    dbc.Row([
        dbc.Col(html.Div(id = 'dist-temp-chart'), md = 6),
        dbc.Col(html.Div(id = 'celestial-chart'), md = 6)
        ]),
    dbc.Row([
        dbc.Col(html.Div(id = 'relative-dist-chart'), md = 6),  # график по расстоянию 
        dbc.Col(html.Div(id = 'mstar-tstar-chart'))  # график с массой и температурой звезды 
    ])
    ],
    style = {'margin-left' : '80px',
            'margin-right': '80px'})

"""" CALLBACK """

@app.callback(
    [Output(component_id = 'dist-temp-chart', component_property = 'children'),
    Output(component_id = 'celestial-chart', component_property = 'children'),
    Output(component_id = 'relative-dist-chart', component_property = 'children'),
    Output(component_id = 'mstar-tstar-chart', component_property = 'children')],
    [Input(component_id = 'submit-val', component_property = 'n_clicks')],
    [State(component_id = 'range-slider', component_property = 'value'),
    State(component_id = 'star-selector', component_property = 'value')]
)
def update_dist_temp_chart(n, radius_range, star_size):

    # print(n)  # смотрим сколько раз кликнули на кнопку "apply"
    chart_data = df[(df['RPLANET'] > radius_range[0]) &
                    (df['RPLANET'] < radius_range[1]) &
                    (df['StarSize'].isin(star_size))]

    # WARINNG MESSAGE
    
    if len(chart_data) == 0:
        return html.Div('Please select more data'), html.Div(), html.Div(), html.Div()  # Если выбор пустой, то возвращаем предупреждение
    

    fig1 = px.scatter(chart_data, x = 'TPLANET', y = 'A', color = 'StarSize')  # по x - Tplanet, по y - A, разбивка по цветам в зависимости от категории StarSize

    html1 = [html.Div('Planet Temperature ~ Distance from the Star'),  # название графика
            dcc.Graph(figure = fig1)]  # второй элемент - списка график

    fig2 = px.scatter(chart_data, x = 'RA', y = 'DEC', size = 'RPLANET', 
                                                        color = 'status')

    html2 = [html.Div('Position on the Celestial Sphere'),
            dcc.Graph(figure = fig2)]

    # RELATIVE DISTANCE CHART

    fig3 = px.histogram(chart_data, x = 'relative_dist', 
                        color = 'status', barmode = 'overlay', marginal = 'violin') 
    fig3.add_vline(x = 1, y0 = 0, y1 = 155, annotation_text = 'Earth', line_dash = 'dot') #  вертикальная линия (уровень Земли) 
    html3 = [html.Div('Relative Distance (AU/SOL radii'), 
            dcc.Graph(figure = fig3)]

    fig4 = px.scatter(chart_data, x = 'MSTAR', y = 'TSTAR', size = 'RPLANET', color = 'status')
    html4 = [html.Div('Star Mass ~ Star Temperature'), 
            dcc.Graph(figure = fig4)]

    return html1, html2, html3, html4

if __name__ == '__main__':
    app.run_server(debug=True)  # debug = True - запуск в тестовом режиме