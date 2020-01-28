import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import os
import glob
from stock_export import export2dataframe

def plotPrice(df, stock_no='', autoshow=True, save2html=True):

    try:
        df = df.rename(columns = {'index':'date'})
    except:
        pass

    # Create figure
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(x=df['date'], y=df['close']))

    # Set title
    fig.update_layout(
        title_text=stock_no
    )

    # Add range slider
    fig.update_layout(
        xaxis=go.layout.XAxis(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                        label="1m",
                        step="month",
                        stepmode="backward"),
                    dict(count=6,
                        label="6m",
                        step="month",
                        stepmode="backward"),
                    dict(count=1,
                        label="YTD",
                        step="year",
                        stepmode="todate"),
                    dict(count=1,
                        label="1y",
                        step="year",
                        stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

    if autoshow:
        fig.show()
    
    if save2html:
        if not os.path.isdir('html'):
            os.mkdir('html')
        fig.write_html('html/{}.html'.format(stock_no))

def visualPrice(stock_no, autoshow=True, save2html=True):
    fileName = '{}.TW'.format(stock_no)
    df = pd.read_csv('finished/{}.csv'.format(fileName))  
    df = df.dropna()
    plotPrice(df, stock_no,  autoshow, save2html)

def visualPriceWithFile(path, stock_no, autoshow=True, save2html=True):
    df = pd.read_csv(path)  
    df = df.dropna()
    plotPrice(df, stock_no,  autoshow, save2html)

def visualPriceWithDB(dbname, stock_no, autoshow=True, save2html=True):
    df = export2dataframe(dbname)
    df = df.dropna()
    df['index'] = pd.to_datetime(df['index'].astype(str), format='%Y-%m-%d')
    print(df)
    plotPrice(df, stock_no,  autoshow, save2html) 
    
def getAllCSV(folderPath):
    
    allPath = glob.glob(folderPath + r'/*.csv')
    actfilenames = []
    for p in allPath:
        base, child = os.path.split(p)
        child = os.path.splitext(child)[0]
        actfilenames.append(child)
    return actfilenames


if __name__ == '__main__':
    # allf = getAllCSV('finished')
    # for f in allf:
    #     stockN = f.split('.')[0]
    #     visualPrice(stockN, autoshow=True, save2html=True)
    # visualPriceWithFile('2317.TW_wk.csv', '2317', False, True)
    stocks = [2317,2330,2382,2823]
    for s in stocks:
        visualPriceWithDB('database/tw_{}'.format(s),s,False,True)