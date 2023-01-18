import requests
import pandas as pd
import plotly.express as px
import plotly.io as poi
poi.renderers.default = 'browser'  # режим отображения в браузере 
# импорт библиотек dash
import dash 
from dash import dcc
from dash import html

response = requests.get('http://asterank.com/api/kepler?query={}&limit=2000')  # с помощью API считываем данные с сайта sterank.com/kepler с пустым параметром запроса и лимитом в 2000
df = pd.json_normalize(response.json())  # нормализация json 

# print(df.head())  # вывод первых пяти строк датафрейма для проверки корректности его загрузки

fig = px.scatter(df, x = 'TPLANET', y = 'A')  # считываем данные и строим скаттерплот по интересующим нас параметрам

app = dash.Dash(__name__) # инициализация приложения

app.layout = html.Div([
    html.H1('Hello Dash!'),  # вывод заголовка первого уровня 
    html.Div('Exoplanets chart'),  # вывод названия графика
    dcc.Graph(figure = fig)  # вывод графика
])  # app.layout - фронтенд приложения. В нем используются элементы библиотек dcc и html

if __name__ == '__main__':
    app.run_server(debug=True)  # debug = True - запуск в тестовом режиме