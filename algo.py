import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
from matplotlib import ticker as mticker
from mpl_finance import candlestick_ohlc
from matplotlib.dates import DateFormatter
import datetime as dt
import numpy as np

#計算MA線
def moving_average(data,period):
    return data['Close'].rolling(period).mean()

#計算KD線
'''
Step1:計算RSV:(今日收盤價-最近9天的最低價)/(最近9天的最高價-最近9天的最低價)
Step2:計算K: K = 2/3 X (昨日K值) + 1/3 X (今日RSV)
Step3:計算D: D = 2/3 X (昨日D值) + 1/3 X (今日K值)
'''
def KD(data):
    data_df = data.copy()
    data_df['min'] = data_df['Low'].rolling(9).min()
    data_df['max'] = data_df['High'].rolling(9).max()
    data_df['RSV'] = (data_df['Close'] - data_df['min'])/(data_df['max'] - data_df['min'])
    data_df = data_df.dropna()
    # 計算K
    # K的初始值定為50
    K_list = [50]
    for num,rsv in enumerate(list(data_df['RSV'])):
        K_yestarday = K_list[num]
        K_today = 2/3 * K_yestarday + 1/3 * rsv
        K_list.append(K_today)
    data_df['K'] = K_list[1:]
    # 計算D
    # D的初始值定為50
    D_list = [50]
    for num,K in enumerate(list(data_df['K'])):
        D_yestarday = D_list[num]
        D_today = 2/3 * D_yestarday + 1/3 * K
        D_list.append(D_today)
    data_df['D'] = D_list[1:]
    use_df = pd.merge(data,data_df[['K','D']],left_index=True,right_index=True,how='left')
    return use_df

def prepare_data(data):
    data_df = data.copy()
    data_df['Date'] = data_df.index
    #data_df = data_df.reset_index()
    data_df = data_df[['Date','Open','High','Low','Close']]
    
    data_df['Date'] = mdates.date2num(data_df['Date'])
    return data_df

# 畫股價圖
# 顏色:https://matplotlib.org/users/colors.html
 
#畫股價線圖與蠟燭圖
def plot_stock_price(data, KD_df, stock_no):
    Ma_1 = moving_average(data,1)
    Ma_50 = moving_average(data,50)
    Length = len(data['Date'].values[50-1:])
    fig = plt.figure(facecolor='white',figsize=(15,10))
    ax1 = plt.subplot2grid((6,4), (0,0),rowspan=4, colspan=4, facecolor='w')
    candlestick_ohlc(ax1, data.values[-Length:],width=0.6,colorup='red',colordown='green')
    Label1 = '1 MA Line'
    # Label2 = '50 MA Line'
    ax1.plot(data.Date.values[-Length:],Ma_1[-Length:],'black',label=Label1, linewidth=1.5)
    # ax1.plot(data.Date.values[-Length:],Ma_50[-Length:],'navy',label=Label2, linewidth=1.5)
    ax1.legend(loc='upper center', ncol=2)
    ax1.grid(True, color='black')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.yaxis.label.set_color("black")
    ax1.tick_params(axis='y', colors='black')
    ax1.tick_params(axis='x', colors='black')
    plt.ylabel('Stock price and Volume')
    plt.suptitle('Stock Code:{}'.format(stock_no),color='black',fontsize=16)
    #畫交易量
    ax1v = ax1.twinx()
    ax1v.fill_between(data.Date.values[-Length:],0, KD_df.Volume.values[-Length:], facecolor='navy', alpha=.4)
    ax1v.axes.yaxis.set_ticklabels([])
    ax1v.grid(False)
    ax1v.set_ylim(0, 3*KD_df.Volume.values.max())
    ax1v.tick_params(axis='x', colors='black')
    ax1v.tick_params(axis='y', colors='black')
    #加入KD線在下方
    ax2 = plt.subplot2grid((6,4), (4,0), sharex=ax1, rowspan=1, colspan=4, facecolor='white')
    ax2.plot(data.Date.values[-Length:], KD_df.K[-Length:],color='black')
    ax2.plot(data.Date.values[-Length:], KD_df.D[-Length:],color='navy')
    plt.ylabel('KD Value', color='black')
    # 買進訊號
    x = data.Date.values[-Length:]
    y = Ma_1[-Length:]
    x_filt = x[KD_df.event1[-Length:]]
    y_filt = y[KD_df.event1[-Length:]]
    ax1.plot(x_filt, y_filt,'go',markersize=5)
    # 賣出訊號
    x = data.Date.values[-Length:]
    y = Ma_1[-Length:]
    x_filt = x[KD_df.event2[-Length:]]
    y_filt = y[KD_df.event2[-Length:]]
    ax1.plot(x_filt, y_filt,'ro',markersize=5)

def strategy1(KD_df):
    '''是KD均小於20 且 K突破D (K開始大於D)時買進'''
    shape = len(KD_df['K'].values[:])
    zeroy = np.zeros((shape))
    truey = np.ones((shape))
    condition = np.logical_and(KD_df['K']<0.2, KD_df['D']<0.2)
    condition = np.logical_and(condition, KD_df['K']>KD_df['D'])
    print(condition)
    print(condition.shape)
    KD_df['event1']= np.where(condition, truey, zeroy).astype('bool')
    return KD_df

def strategy2(KD_df):
    '''是KD均大於20 且 D突破K (D開始大於K)時賣出'''
    shape = len(KD_df['K'].values[:])
    zeroy = np.zeros((shape))
    truey = np.ones((shape))
    condition = np.logical_and(KD_df['K']>0.8, KD_df['D']>0.8)
    condition = np.logical_and(condition, KD_df['K']<KD_df['D'])
    print(condition)
    print(condition.shape)
    KD_df['event2']= np.where(condition, truey, zeroy).astype('bool')
    return KD_df


if __name__=='__main__':
    # 匯入資料，把csv檔(連結下方)放到與程式檔同一資料夾
    stock_no = 2353
    df = pd.read_csv('finished\\{}.TW.csv'.format(stock_no), parse_dates=['Date'], index_col=0).dropna()
    df = df[(df.index > '2000-01-01')]
    df_plot = df[['Open','High','Low','Close']]
    daysreshape = prepare_data(df_plot)
    kd_df = KD(df)
    print(kd_df)
    stre1_df = strategy1(kd_df)
    print(stre1_df)
    stre1_df = strategy2(stre1_df)
    print(stre1_df)

    
    plot_stock_price(daysreshape, stre1_df, stock_no)
    plt.show()