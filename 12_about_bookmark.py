from dash import Input, Output, State
import dash
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc  # в этой библиотеке находятся слайдеры и прочее
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as poi
from dash import dash_table  # компонент для создания таблиц

poi.renderers.default = 'browser'  # режим отображения в браузере
# импорт библиотек dash
# импортируем компоненты для того, чтобы график реагировал на изменения

"""" READ DATA """

# с помощью API считываем данные с сайта sterank.com/kepler с пустым параметром запроса и лимитом в 2000
response = requests.get('http://asterank.com/api/kepler?query={}&limit=2000')
df = pd.json_normalize(response.json())  # нормализация json
df = df[df['PER'] > 0]  # отрезаем нежелательную точку с периодом < 0
df['KOI'] = df['KOI'].astype(int, errors='ignore')

# Create Star size category

# разбиваем на категории по метрикам сравнения с метриками солнце
bins = [0, 0.8, 1.2, 100]
names = ['small', 'similar', 'bigger']
df['StarSize'] = pd.cut(df['RSTAR'], bins, labels=names)

# TEMPERATURE BINS (бакеты по температуре планет)
tp_bins = [0, 200, 400, 500, 5000]
tp_labels = ['low', 'optimal', 'high', 'extreme']
# задаем переменную. Разбиваем температуру по бинам + в зависимости от этого лейбл
df['temp'] = pd.cut(df['TPLANET'], tp_bins, labels=tp_labels)

#  SIZE_BINS (бакеты по размерам планеты в зависимости от радиуса Земли)

rp_bins = [0, 0.5, 2, 4, 100]
rp_labels = ['low', 'optimal', 'high', 'extreme']  # лейблы по бакетам
# по аналогии делаем соответствие по радиусам
df['gravity'] = pd.cut(df['RPLANET'], rp_bins, labels=rp_labels)

#  ESTIMATE OBJECT STATUS (разбиваем объекты по статусам)
#  Если temp == optimal и gravity == optimal => promising
df['status'] = np.where((df['temp'] == 'optimal')
                        & (df['gravity'] == 'optimal'),
                        'promising', None)
#  Если и не optimal, и не extreme, то challening для нас
df.loc[:, 'status'] = np.where((df['temp'] == 'optimal') &
                               (df['gravity'].isin(['low', 'high'])),
                               'challening', df['status'])
df.loc[:, 'status'] = np.where((df['gravity'] == 'optimal') &
                               (df['temp'].isin(['low', 'high'])),
                               'challening', df['status'])
#  В остальных случаях значение extreme
df['status'] = df.status.fillna('extreme')

# Relative distnacer (distance to SUN/SUM radius)
df.loc[:, 'relative_dist'] = df['A']/df['RSTAR']

options = []
for k in names:
    options.append({'label': k, 'value': k})

# print(df.head())  # вывод первых пяти строк датафрейма для проверки корректности его загрузки

# fig = px.scatter(df, x = 'TPLANET', y = 'A')  # считываем данные и строим скаттерплот по интересующим нас параметрам. Уже необязательно строить в теле приложеия

star_size_selector = dcc.Dropdown(
    id='star-selector',
    options=options,
    # категорию, выбранные по умолчанию в dropdown слайзере
    value=['small', 'similar', 'bigger'],
    multi=True
)

# создаем слайсер
rplanet_selector = dcc.RangeSlider(
    id='range-slider',
    min=min(df['RPLANET']),  # минимальное значение слайсера
    max=max(df['RPLANET']),  # максимальное значение слайсера
    marks={5: '5', 10: '10', 20: '20'},  # метки данных
    step=1,
    # значения в слайсере "между" по умолчанию
    value=[min(df['RPLANET']), max(df['RPLANET'])]
)

# TABS CONTENT
tab1_content = [dbc.Row([
    dbc.Col(html.Div(id='dist-temp-chart'), md=6),
    dbc.Col(html.Div(id='celestial-chart'), md=6)
], style={'margin-top': 20}),  # задаем верхний отступ (для заголовков графиков)
    dbc.Row([
        dbc.Col(html.Div(id='relative-dist-chart'),
            md=6),  # график по расстоянию
        # график с массой и температурой звезды
        dbc.Col(html.Div(id='mstar-tstar-chart'))
    ])]

tab2_content = [dbc.Row(html.Div(id='data-table'), style={'margin-top': 20})]
app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.FLATLY])  # инициализация приложения

# Tab3 conent
table_header = [html.Thead(
    html.Tr([html.Th('Field Name'), html.Th('Details')]))]

expl = {'KOI': 'Onject of Interest number',
        'A': 'Semi-major axis (AU)'}

tbl_rows = []
for i in expl:
    tbl_rows.append(html.Tr([html.Td(i), html.Td(expl[i])]))
table_body = [html.Tbody(tbl_rows)]
table = dbc.Table(table_header + table_body, bordered=True)

text = 'Data are sourced from Kepler API via asterank.com'
tab3_content = [
    dbc.Row(html.A(text, href='https://www.asterank.com/kepler'),
            style={'margin-top': 20}),
    dbc.Row(html.Div(children=table),
            style={'margin-top': 20})]

"""" LAYOUT """

app.layout = html.Div([
    # header
    dbc.Row(html.H1('Planets Dashboard'),
            style={'margin-bottom': 40}),
    # filters
    dbc.Row([
        dbc.Col([
            html.Div('Select planet main semi-axis range'),
            html.Div(rplanet_selector)
        ],
            width={'size': 2}),
        dbc.Col([
            html.Div('Star Size '),
            html.Div(star_size_selector)
        ],
            width={'size': 3, 'offset': 1}),
        dbc.Col(dbc.Button('Apply', id='submit-val', n_clicks=0,
                           className='mr-2'))  # кнопка + результат для кнопки и оформление
    ],
        style={'margin-bottom': 40}),
    # charts
    dbc.Tabs([
        dbc.Tab(tab1_content, label='Charts'),
        dbc.Tab(tab2_content, label='Data'),
        dbc.Tab(tab3_content, label='About')
    ])
    #    dbc.Row([
    #        dbc.Col(html.Div(id='dist-temp-chart'), md=6),
    #        dbc.Col(html.Div(id='celestial-chart'), md=6)
    #    ]),
    #    dbc.Row([
    #        dbc.Col(html.Div(id='relative-dist-chart'),
    #                md=6),  # график по расстоянию
    #        # график с массой и температурой звезды
    #        dbc.Col(html.Div(id='mstar-tstar-chart'))
    #    ])
],
    style={'margin-left': '80px',
           'margin-right': '80px'})

"""" CALLBACK """


@app.callback(
    [Output(component_id='dist-temp-chart', component_property='children'),
     Output(component_id='celestial-chart', component_property='children'),
     Output(component_id='relative-dist-chart', component_property='children'),
     Output(component_id='mstar-tstar-chart', component_property='children'),
     Output(component_id='data-table', component_property='children')],
    [Input(component_id='submit-val', component_property='n_clicks')],
    [State(component_id='range-slider', component_property='value'),
     State(component_id='star-selector', component_property='value')]
)
def update_dist_temp_chart(n, radius_range, star_size):

    # print(n)  # смотрим сколько раз кликнули на кнопку "apply"
    chart_data = df[(df['RPLANET'] > radius_range[0]) &
                    (df['RPLANET'] < radius_range[1]) &
                    (df['StarSize'].isin(star_size))]

    # WARINNG MESSAGE

    if len(chart_data) == 0:
        # Если выбор пустой, то возвращаем предупреждение
        return html.Div('Please select more data'), html.Div(), html.Div(), html.Div()

    # по x - Tplanet, по y - A, разбивка по цветам в зависимости от категории StarSize
    fig1 = px.scatter(chart_data, x='TPLANET', y='A', color='StarSize')

    html1 = [html.Div('Planet Temperature ~ Distance from the Star'),  # название графика
             dcc.Graph(figure=fig1)]  # второй элемент - списка график

    fig2 = px.scatter(chart_data, x='RA', y='DEC', size='RPLANET',
                      color='status')

    html2 = [html.Div('Position on the Celestial Sphere'),
             dcc.Graph(figure=fig2)]

    # RELATIVE DISTANCE CHART

    fig3 = px.histogram(chart_data, x='relative_dist',
                        color='status', barmode='overlay', marginal='violin')
    fig3.add_vline(x=1, y0=0, y1=155, annotation_text='Earth',
                   line_dash='dot')  # вертикальная линия (уровень Земли)
    html3 = [html.Div('Relative Distance (AU/SOL radii'),
             dcc.Graph(figure=fig3)]

    fig4 = px.scatter(chart_data, x='MSTAR', y='TSTAR',
                      size='RPLANET', color='status')
    html4 = [html.Div('Star Mass ~ Star Temperature'),
             dcc.Graph(figure=fig4)]

    # RAW DATA TABLE
    # вывоидм наш датафрейм без указанных колонок
    raw_data = chart_data.drop(
        ['relative_dist', 'StarSize', 'ROW', 'temp', 'gravity'], axis=1)
    tbl = dash_table.DataTable(data=raw_data.to_dict('records'),  # конвертируем в словарь
                               columns=[{'name': i, 'id': i}
                                        for i in raw_data.columns],
                               style_data={'width': '100px',
                                           'maxWidth': '100px',
                                           'minWidth': '100px'},
                               # Количество элементов (в нашем случае строк) на странице
                               page_size=30,
                               # Задаем стиль заголовка (выравниваем по центру)
                               style_header={'textAlign': 'center'})

    html5 = [html.P('Raw Data'), tbl]

    return html1, html2, html3, html4, html5


if __name__ == '__main__':
    app.run_server(debug=True)  # debug = True - запуск в тестовом режиме
