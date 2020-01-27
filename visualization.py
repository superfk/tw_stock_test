import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import os
import glob

def plotPrice(df, stock_no='', autoshow=True, save2html=True):

    # Create figure
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(x=list(df.Date), y=list(df.Close)))

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
        fig.write_html('html/' + stock_no + '.html')

def visualPrice(stock_no, autoshow=True, save2html=True):
    fileName = '{}.TW'.format(stock_no)
    df = pd.read_csv('finished/{}.csv'.format(fileName))  
    df = df.dropna()
    plotPrice(df, stock_no,  autoshow, save2html)

def visualPriceWithFile(path, stock_no, autoshow=True, save2html=True):
    df = pd.read_csv(path)  
    df = df.dropna()
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
    visualPriceWithFile('2317.TW_wk.csv', '2317', False, True)