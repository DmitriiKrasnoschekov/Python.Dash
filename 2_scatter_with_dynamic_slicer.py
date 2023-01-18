import requests
import pandas as pd
import plotly.express as px
import plotly.io as poi
poi.renderers.default = 'browser'  # режим отображения в браузере 
# импорт библиотек dash
import dash 
from dash import dcc  # в этой библиотеке находятся слайдеры и прочее
from dash import html
# импортируем компоненты для того, чтобы график реагировал на изменения
from dash import Input, Output 

response = requests.get('http://asterank.com/api/kepler?query={}&limit=2000')  # с помощью API считываем данные с сайта sterank.com/kepler с пустым параметром запроса и лимитом в 2000
df = pd.json_normalize(response.json())  # нормализация json 

# print(df.head())  # вывод первых пяти строк датафрейма для проверки корректности его загрузки

fig = px.scatter(df, x = 'TPLANET', y = 'A')  # считываем данные и строим скаттерплот по интересующим нас параметрам

# создаем слайсер
rplanet_selector = dcc.RangeSlider(
    id = 'range-slider',
    min = min(df['RPLANET']), # минимальное значение слайсера 
    max = max(df['RPLANET']),  # максимальное значение слайсера
    marks = {5: '5', 10 : '10', 20 : '20'},  # метки данных
    step = 1,
    value = [5, 50]
)

app = dash.Dash(__name__) # инициализация приложения

app.layout = html.Div([
    html.H1('Hello Dash!'),  # вывод заголовка первого уровня 
    html.Div('Select planet main semi-axis range'),
    html.Div(rplanet_selector, 
            style = {'width' : '400px',
                    'margin-bottom' : '40px'}),  # включаем в график созданный нами слайдер
    html.Div('Planet Temperature ~ Distance from the Star'),  # вывод названия графика
    dcc.Graph(id = 'dist-temp-chart',
        figure = fig)  # вывод графика
],  # app.layout - фронтенд приложения. В нем используются элементы библиотек dcc и html
    style = ({'margine-left' : '80px',
            'margine-right' : '80px'}
))

@app.callback(
    Output(component_id = 'dist-temp-chart', component_property = 'figure'),
    Input(component_id = 'range-slider', component_property = 'value')
)
def update_dist_temp_chart(radius_range):
    chart_data = df[(df['RPLANET'] > radius_range[0]) &
                    (df['RPLANET'] < radius_range[1])]
    fig = px.scatter(chart_data, x = 'TPLANET', y = 'A')

    return fig 


if __name__ == '__main__':
    app.run_server(debug=True)  # debug = True - запуск в тестовом режиме