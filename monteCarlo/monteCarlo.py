from urllib.parse import _NetlocResultMixinStr
import psycopg2
import plotly.express as px
import plotly.figure_factory as ff
import pandas as pd
import numpy as np
import streamlit as st

SECONDSPERDAY = 24 * 60 * 60
nPath = 1000

def monteCarloFigures(secretDict, timestampLower, timestampUpper):

    dfETH = ethPriceGet(secretDict, timestampLower, timestampUpper)
    ethPriceFig = px.line(dfETH, x='datetime', y='price', title='ETH price')

    prices = dfETH['price'].values
    paths, currentPrice = pathsGet(prices, nPath)
    samplesFig = samplesFigGet(paths)

    return ethPriceFig, samplesFig, currentPrice, paths, dfETH

def barrierProbGet(paths, barrierValue):
    currentPrice = paths[0,0]
    nPaths = paths.shape[1]
    if barrierValue >= currentPrice:
        allMax = np.max(paths, axis=0)
        barrierProb = sum(barrierValue <= allMax)/nPaths
    else:
        allMin = np.min(paths, axis=0)
        barrierProb = sum(barrierValue >= allMin)/nPaths
    return barrierProb

def samplesFigGet(paths):
    samplesFig = px.line(data_frame=paths[:,0:10])
    samplesFig.update_layout(showlegend=False, 
                             title='Sample Paths Based on Recent Data - One Day Ahead', 
                             xaxis_title='seconds into future',
                             yaxis_title='simulated price of ETH')
    return samplesFig

def pathsGet(prices, nPath):
    
    currentPrice = prices[-1]
    logReturns = np.diff(np.log(prices))
    st.write('here 1')
    paths = currentPrice * np.exp(np.cumsum(np.random.choice(logReturns, size=(SECONDSPERDAY, nPath)), axis = 0))
    st.write('here 2')
    return paths, currentPrice

def dfNormalize(df):
    
    df1 = df.copy()
    df1.set_index('datetime', inplace=True)
    df1 = df1.asfreq(freq='S', method='pad')
    df1.reset_index(inplace=True)
    df1['datetime'] = df1['datetime'].apply(lambda x: x.replace(microsecond=0))
    
    return df1

def ethPriceGet(secretDict, timestampLower, timestampUpper):
    dbUsername = secretDict['dbUsername']
    dbPassword = secretDict['dbPassword']
    dbHostname = secretDict['dbHostname']
    database = secretDict['database']
    df = dfNormalize(dbQuery(dbUsername, dbPassword, dbHostname, database, timestampLower, timestampUpper))
    return df

def dbQuery(dbUsername, dbPassword, dbHostname, database, timestampLower, timestampUpper):

    try:
        conn = psycopg2.connect (dbname = database,
                                 user = dbUsername,
                                 password = dbPassword,
                                 host = dbHostname,
                                 connect_timeout = 10)
        
        query = """SELECT timestamp, exchange, symbol, price from trade_pairs where exchange::text like 'coinbase%%' 
                   and symbol::text like 'ETH-USD'
                   and timestamp >= '%s' and timestamp < '%s' order by timestamp asc""" % (timestampLower, timestampUpper) 

        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        df = pd.DataFrame(rows)
        df.columns = ['datetime', 'exchange', 'pair', 'price']
        df['price'] = df['price'].astype('float')
        return df

    except:
        st.write("This problem")
        print("Some problem")
