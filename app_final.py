import dash
from dash.dependencies import Output, Event, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
import sqlite3
import pandas as pd
import time
from tweets_get import *
import subprocess
from threading import Thread
import dash_table_experiments as dt
import plotly.plotly as py
from datetime import datetime
from datetime import timedelta

conn = sqlite3.connect('twitter.db', check_same_thread=False)

colors = {
    'background':  '#191A1A', #'#ededed', #f7f7f7', #'#e8edf4',
    'font-color': '#CCCCCC',
    'plot': '#191A1A',
    'button-background': '#616163',
    'sentiment-positive': '#00ba3e',
    'sentiment-negative': '#ff5842',
    'sentiment-neutral':  '#050505',
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
sentiment_index = 0.1


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# df = pd.read_sql("SELECT * FROM tweets_base ORDER BY unix_time DESC LIMIT 1000", conn)

# Since we're adding callbacks to elements that don't exist in the app.layout,
# Dash will raise an exception to warn us that we might be
# doing something wrong.
# In this case, we're adding the elements through a callback, so we can ignore
# the exception.
app.config.suppress_callback_exceptions = True


app.layout = html.Div([
        html.H2("Tweets Streamer",
            style={
                'textAlign': 'center',
            }),
        html.Div(id='date-slider-value', style={'display': 'yes', 'color': 'red'}),
        dcc.Tabs(id="tabs-example", value='tab-1-example', children=[
            dcc.Tab(label='Live analysis', value='tab-1-example'),
            dcc.Tab(label='Historical analysis', value='tab-2-example'),
        ], colors={
        "border": "white",
        "primary": "black",
        "background": colors['background'],
        }
        ),
        html.P(),
        html.Div(id='tabs-content')
                         ], style={
        'backgroundColor': colors['background'],
        'color': colors['font-color'],
        'width': '100%',
        'size': '100%',
        'height': '1000px',
        'margin-top': '-20px',
        'margin-bottom': '-20px',
        }
)


loading_component = html.H1(
    style={'textAlign': 'center',
           'verticalAlign': 'center'},
    children='Loading...'
)


@app.callback(Output('tabs-content', 'children'),
              [Input('tabs-example', 'value')])
def render_content(tab):
    if tab == 'tab-1-example':
        return html.Div([
                            html.Div(id='searched-value', style={'display': 'none', 'color': 'red'}),
                            html.Div(id='searched-value-stream', style={'display': 'none', 'color': 'red'}),
                            html.Div(id='stream-clicks', style={'display': 'none', 'color': 'red'}),
                            html.Div([
                                dcc.Input(id='sentiment_term',
                                          value="",
                                          type='text',
                                          disabled=False,
                                          style={'width': '30%',
                                                 'margin-right': 10,
                                                 },
                                          ),
                                html.Button(id='submit-button',
                                            n_clicks=0,
                                            children='Start Streaming',
                                            style={
                                                'cursor': 'pointer',
                                                'background-color': colors['background'],
                                                'color': colors['font-color'],
                                            }),
                                # dcc.RadioItems(
                                #     id='buttons',
                                #     options=[{'label': i, 'value': i} for i in ['Update live', 'Static']],
                                #     value='Static',
                                # ),
                            ], style={'width': '100%',
                                      'margin-left': 30,
                                      'margin-right': 10,
                                      'max-width': 50000,
                                      'display': 'inline-block'}
                            ),
                            # html.Div(id='tweet-info'),
                            html.P(),
                            dcc.Interval(id='graph-update', ),
                            dcc.Interval(id='table-update', ),
                            html.Div
                            (id='live-graph-container', children=[
                              loading_component
                            ], style={
                                'width': '49%',
                                'display': 'inline-block',
                            },
                            ),
                            html.Div(className='row',
                                     children=[html.Div(id="tweets-table", className='col s12 m6 l6')],
                                     style={
                                         "color": colors['font-color'],
                                         "fontSize": "16",
                                         "borderBottom": "1px solid #C8D4E3",
                                         "border": "1px",
                                         "font-size": "1.3rem",
                                         "width": "50%",
                                         'display': 'inline-block'
                                     },
                                     ),
            ])
    elif tab == 'tab-2-example':
        return html.Div([
            html.Div([
                        dcc.Input(id='searched-word-input',
                                  value="",
                                  type='text',
                                  disabled=False,
                                  size=60,
                                  style={
                                      'margin-right': 10,
                                      'width': '30%',
                                  }
                                  ),
                        html.Button(id='searched-button',
                                    n_clicks=0,
                                    children='Search',
                                    style={
                                        'cursor': 'pointer',
                                        'background-color': colors['background'],
                                        'color': colors['font-color'],
                                    }),
                        ], style={'width': '100%',
                                  'margin-left': 30,
                                  'margin-right': 10,
                                  'max-width': 50000,
                                  'display': 'inline-block'
                                  }
                        ),
            html.Div([
                html.Div(id='historical-graph-container', children=[
                    loading_component
                ], style={'verticalAlign': 'center',
                          }
                         ),
                html.P(),
                # html.Div(id='date-slider-container', children=[
                # ], style={'verticalAlign': 'center',
                #           'margin-left': 30,
                #           },
                #          ),
            html.Div([html.H5('Select a start and end date:'),
                      dcc.DatePickerRange(id='my-date-picker',
                                          min_date_allowed=datetime(2018, 10, 1),
                                          max_date_allowed=datetime.today() + timedelta(days=1),
                                          start_date=datetime(2018, 10, 1),
                                          end_date= datetime.today() + timedelta(days=1),
                                          display_format='YYYY-MM-DD',
                                          )], style={'display': 'center', 'margin-left': 50})

            ], style={
                'width': '49%',
                'display': 'inline-block',
            },
                    ),
            html.Div(id='historical-pie-container', children=[
                loading_component
            ], style={'width': '49%',
                      'display': 'inline-block',
                      }
                     ),



            # html.Div(className='row', children=[
            #     html.Div(id="historical-tweets-table", className='col s12 m6 l6')],
            #          style={
            #              "color": colors['font-color'],
            #              "fontSize": "16",
            #              "borderBottom": "1px solid #C8D4E3",
            #              "border": "1px",
            #              "font-size": "1.3rem",
            #              "width": "50%",
            #              "height": "600",
            #              'display': 'inline-block',
            #          },
            #          ),
])


def define_sentiment_color(col):
    if col >= sentiment_index:
        # positive
        return colors['sentiment-positive']
    elif col <= -sentiment_index:
        # negative:
        return colors['sentiment-negative']
    else:
        return colors['background']


def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns.values])] +
        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ], style={'background-color': define_sentiment_color(dataframe.iloc[i][2])}
        )
            for i in range(min(len(dataframe), max_rows))
        ]
    )


@app.callback(Output('stream-clicks', 'children'),
             [Input('submit-button', 'n_clicks')])
def store_clicks(clicks):
    return clicks


@app.callback(Output('searched-value', 'children'),
             [Input('sentiment_term', 'value')])
def store_searched_value(value):
    return value


@app.callback(Output('searched-value-stream', 'children'),
              [Input('submit-button', 'n_clicks')],
              [State('searched-value', 'children')])
def start_streaming(n_clicks, value):
    hash_tag_list = []
    errors = 0
    if n_clicks % 2 == 1:
        if value == "":
            hash_tag_list.extend(("a", "e", "o", "i"))
        else:
            hash_tag_list.append(value)
        with open('hash_tag_list.txt', 'a') as f:
            f.write(hash_tag_list[0])
            f.write('\n')
        try:
            twitter_streamer = TwitterStreamer()
            key_search = ''.join(hash_tag_list)
            twitter_streamer.start_stream(hash_tag_list, key_search)
            with open('key_search.txt', 'a') as f:
                f.write(key_search)
                f.write('\n')
        except Exception:
            time.sleep(5)
            errors += 1
            return "Error nr {}".format(errors)
    if n_clicks % 2 == 0 & n_clicks != 0:
        try:
            twitter_streamer.stop_stream()
            del twitter_streamer
            del hash_tag_list
        except:
            return "End"
        # twitter_streamer.stop_stream()
        # twitter_streamer.start_stream(hash_tag_list)


# @app.callback(Output('tweets-update', 'interval'),
#               [Input('submit-button', 'n_clicks')])
# def update_interval_tweets(n_clicks):
#     if n_clicks % 2 == 1:
#         return 15000
#     if n_clicks % 2 == 0:
#         return 1000000

# @app.callback(Output('graph-update', 'interval'),
#             [Input('buttons', 'value')])
# def update_interval(value):
#     if value == 'Live':
#         return 1000
#     if value == 'Static':
#         return 100000
@app.callback(Output('graph-update', 'interval'),
             [Input('stream-clicks', 'children')])  # jak dam submit button to odświeży live
def update_interval(value):
    if value % 2 == 1:
        return 1000
    if value % 2 == 0:
        return 100000


@app.callback(Output('table-update', 'interval'),
             [Input('stream-clicks', 'children')])
def update_interval_table(value):
    if value % 2 == 1:
        return 1000
    if value % 2 == 0:
        return 100000


@app.callback(Output('submit-button', 'children'),
             [Input('submit-button', 'n_clicks')])
def update_interval(value):
    if value % 2 == 1:
        return "Stop Streaming"
    if value % 2 == 0:
        return "Start Streaming"


@app.callback(Output('sentiment_term', 'disabled'),
              [Input('submit-button', 'n_clicks')])
def text_disabled(value):
    if value % 2 == 1:
        return True
    if value % 2 == 0:
        return False


@app.callback(Output('live-graph-container', 'children'),
              [Input('graph-update', 'n_intervals')],
              [State('sentiment_term', 'value')])
def update_graph_scatter(n_intervals, sentiment_term):
    try:
        # df = pd.read_sql("SELECT * FROM tweets_base ORDER BY unix_time DESC LIMIT 1000", conn)
        # df = pd.read_sql("SELECT unix_time,sentiment FROM tweets_base WHERE text LIKE ? ORDER BY unix_time DESC LIMIT 1000",
        #                  conn, params=('%' + sentiment_term + '%',))

        df = pd.read_sql("SELECT unix_time, sentiment"
                         " FROM tweets_base  ORDER BY unix_time DESC LIMIT 1000", conn)

        # df.sort_values('created_at', inplace=True)twitter
        df.sort_values('unix_time', inplace=True)
        df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df) / 2)).mean()

        df['date'] = pd.to_datetime(df['unix_time'], unit='ms')
        df.set_index('date', inplace=True)

        df = df.resample('1s').mean()
        df.dropna(inplace=True)
        X = df.index[-100:]
        Y = df['sentiment_smoothed'][-100:]
        # X = df['unix_time'].values[-100:]

        return dcc.Graph(id='live-graph',
                        animate=True,
                        figure= {'data': [go.Scatter(
                                x=X,
                                y=Y,
                                name='Scatter',
                                mode='markers+lines',
                            )
                        ], 'layout': go.Layout(xaxis=dict(title='Time', range=[min(X), max(X)]),
                                               yaxis=dict(title='Sentiment', range=[min(Y) - 0.01, max(Y) + 0.01]),
                                               title='{}'.format(sentiment_term),
                                               plot_bgcolor=colors['background'],
                                               paper_bgcolor=colors['background'],
                                               font=dict(color=colors['font-color']),
                                               hovermode='closest',
                                               ),
                        })
    except Exception as e:
        with open('errors_update_scatter.txt', 'a') as f:
            f.write(str(e))
            f.write('\n')


tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}


@app.callback(Output('tweets-table', 'children'),
              [Input('table-update', 'n_intervals')],
              [State('sentiment_term', 'value')])
def update_recent_tweets(n_inervals, value):
    # df = pd.read_sql("SELECT "
    #                  "unix_time,"
    #                  "user_screenname,"
    #                  "text  FROM tweets_base WHERE text LIKE ? ORDER BY
    # unix_time DESC LIMIT 500", conn, params=('%' + sentiment_term + '%',))
    df = pd.read_sql("SELECT user_screenname, text, sentiment, unix_time "
                     "FROM tweets_base  ORDER BY unix_time DESC LIMIT 1000", conn)
    df.sort_values('unix_time', inplace=True)
    # df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df) / 2)).mean()
    df = df[['user_screenname', 'text', 'sentiment']]
    df.columns = ['User', 'Tweet', 'Sentiment']
    return generate_table(df, max_rows=5)

#
# @app.callback(Output('historical-tweets-table', 'children'),
#               [Input('searched-button', 'n_clicks')],
#               [State('searched-word-input', 'value')])
# def update_datatable(n_clicks, searched_word):
#     """
#     For user selections, return the relevant table
#     """
#     df = pd.read_sql(
#         "SELECT  username,text, sentiment FROM tweets_base WHERE text LIKE ? ORDER BY unix_time DESC LIMIT 1000",
#         conn, params=('%' + searched_word + '%',))
#     df.columns = ['User', 'Tweet', 'Sentiment']
#     return generate_table(df, max_rows=5)

@app.callback(Output('historical-graph-container', 'children'),
              [Input('searched-button', 'n_clicks'),
               Input('my-date-picker', 'start_date'),
               Input('my-date-picker', 'end_date')],
              [State('searched-word-input', 'value')])
def update_historical_graph_scatter(n_clicks, start_date, end_date, searched_word):
        df = pd.read_sql("SELECT user_screenname, text, sentiment, unix_time "
                         "FROM tweets_base WHERE text LIKE ? ORDER BY unix_time DESC LIMIT 25000", conn, params=('%' + searched_word + '%',))

        # df.sort_values('unix_time', inplace=True)
        # df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df) / 2)).mean()
        # df['date'] = pd.to_datetime(df['unix_time'], unit='ms')
        # start = datetime.strptime(start_date[:10], '%Y-%m-%d')
        # end = datetime.strptime(end_date[:10], '%Y-%m-%d')
        # df = df[df['date'] <= end]
        # df.dropna(inplace=True)
        # X = df['date'][-100:]
        # Y = df['sentiment_smoothed'][-100:]
        # # X = df['unix_time'].values[-100:]

        df.sort_values('unix_time', inplace=True)

        df['date'] = pd.to_datetime(df['unix_time'], unit='ms')
        start = datetime.strptime(start_date[:10], '%Y-%m-%d')
        end = datetime.strptime(end_date[:10], '%Y-%m-%d')
        df = df[(df['date'] < end)]
        df.dropna(inplace=True)
        X = df['date'][:1000]
        Y = df['sentiment'][:1000]

        return dcc.Graph(
          id='historical-graph',
          animate=True,
          figure = {'data': [go.Scatter(
                    x=X,
                    y=Y,
                    name='Scatter',
                    mode='markers+lines',
                    )
        ],  'layout': go.Layout(xaxis=dict(title='Time', range=[datetime(2018, 10, 1), datetime.today()]),
                                yaxis=dict(title='Sentiment', range=[-1, 1]),
                                title='{}'.format(searched_word),
                                plot_bgcolor=colors['background'],
                                paper_bgcolor=colors['background'],
                                font=dict(color=colors['font-color']),
                                hovermode='closest',
                               ),
          })


@app.callback(Output('historical-pie-container', 'children'),
              [Input('searched-button', 'n_clicks'),
               Input('my-date-picker', 'start_date'),
               Input('my-date-picker', 'end_date')],
              [State('searched-word-input', 'value')])
def update_historical_pie(n_clicks, start_date, end_date, searched_word):

        df = pd.read_sql("SELECT user_screenname, text, unix_time, sentiment "
                         "FROM tweets_base WHERE text LIKE ? ORDER BY unix_time DESC LIMIT 2000", conn, params=('%' + searched_word + '%',))

        df.sort_values('unix_time', inplace=True)
        df['date'] = pd.to_datetime(df['unix_time'], format='%Y-%m-%d')
        start = datetime.strptime(start_date[:10], '%Y-%m-%d')
        end = datetime.strptime(end_date[:10], '%Y-%m-%d')
        df = df[(df['date'] <= end)]
        sentiment_positive = df['sentiment'][df['sentiment'] > 0.1].count()
        sentiment_negative = df['sentiment'][df['sentiment'] < -0.1].count()
        sentiment_neutral = df['sentiment'][df['sentiment'].between(-0.1, 0.1, inclusive=True)].count()
        # sentiment_neutral
        # # , sentiment_positive
        # sentiments= []
        # # sentiments.extend((sentiment_positive, sentiment_negative))
        # sentiments.append(sentiment_positive)
        # sentiments.append(sentiment_negative)
        return  dcc.Graph(
          id='historical-pie',
          animate=True,
          figure={'data': [go.Pie(
                    values=[sentiment_positive, sentiment_negative, sentiment_neutral],
                    labels=['Positive', 'Negative', 'Neutral'],
                    marker={'colors': [colors['sentiment-positive'], colors['sentiment-negative'],
                                       colors['sentiment-neutral']]},
                    )],
                    'layout': go.Layout(plot_bgcolor=colors['background'],
                                        paper_bgcolor=colors['background'],
                                        font=dict(color=colors['font-color'])),
                    }
        )




# @app.callback(Output('date-slider-container', 'children'),
#               [Input('searched-button', 'n_clicks')],
#               [State('searched-word-input', 'value')])
# def update_data_slider_container(n_clicks, searched_word):
#     df = pd.read_sql("SELECT user_screenname, text, sentiment, unix_time "
#                      "FROM tweets_base WHERE text LIKE ? ORDER BY unix_time DESC LIMIT 25000", conn,
#                      params=('%' + searched_word + '%',))
#     # date_min = df['created_at'].min()
#     # date_max = df['created_at'].max()
#     df['date'] = pd.to_datetime(df['unix_time'], unit='ms')
#     df.set_index('date', inplace=True)
#     date_min = min(df['date'])
#     date_max = max(['date'].max())
#     return dcc.RangeSlider(
#                     marks={i: 'Label {}'.format(i) for i in range(date_min, date_max)},
#                     min=date_min,
#                     max=date_max,
#                     value=[date_min, date_max],
#     )
#
#
# @app.callback(Output('date-slider-value', 'children'),
#               [Input('searched-button', 'n_clicks')],
#               [State('searched-word-input', 'value')])
# def update_data_slider_container(n_clicks, searched_word):
#     df = pd.read_sql("SELECT user_screenname, text, sentiment, unix_time "
#                      "FROM tweets_base WHERE text LIKE ? ORDER BY unix_time DESC LIMIT 25000", conn,
#                      params=('%' + searched_word + '%',))
#
#     df['date'] = pd.to_datetime(df['unix_time'], unit='ms')
#     df.set_index('date', inplace=True)
#     date_min = df['date'].min()
#     # date = datetime.strptime(date_min, "%Y-%m-%d  %H:%M:%s")
#     # df['date'] = datetime.strptime(df['created_at'], '%b %d %Y %I:%M%p')
#     return str(type(date_min))



# @app.callback(Output('historical-pie', 'children'),
#               [Input('searched-button', 'n_clicks')],
#               [State('searched-word-input', 'value')])
# def update_historical_graph_scatter(n_clicks, searched_word):
#         df = pd.read_sql("SELECT user_screenname, text, sentiment, created_at "
#                          "FROM tweets_base WHERE text LIKE ? ORDER BY unix_time DESC LIMIT 200", conn2, params=('%' + searched_word + '%',))
#         sentiment_positive = df['sentiment'][df['sentiment'] > 0.1].count()
#         sentiment_negative = df['sentiment'][df['sentiment'] < -0.1].count()
#         sentiment_neutral = df['sentiment'][df['sentiment'].between(-0.1, 0.1, inclusive=True)].count()
#
#         sentiments= []
#         # # sentiments.extend((sentiment_positive, sentiment_negative))
#         sentiments.append(sentiment_pos)
#         # sentiments.append(sentiment_negative)


if __name__ == '__main__':
    app.run_server(debug=True)








