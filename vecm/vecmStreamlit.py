import pandas as pd
import datetime
from sklearn.linear_model import LinearRegression
import numpy as np
import psycopg2
import plotly.express as px
import streamlit as st

SECONDSPERYEAR = 365 * 24 * 3600

exponentialSmoothingFactor = 1.0
k_ar_diff = 5
rvWindowSeconds = 20
rvSmoothingExponent = -.1 # negative value for decay in time

def latentPriceFigures(secretDict, timestampLower, timestampUpper):
    dExchanges = dataForVECMGet(secretDict, timestampLower, timestampUpper)
    pStar = vecmPriceGet(k_ar_diff, dExchanges, exponentialSmoothingFactor)

    datetimes = dExchanges[0]['datetime'].values[k_ar_diff + 1:]
    dTemp = {'datetime': datetimes, 'price': pStar, 'code': np.array(['latent price' for i in range(len(datetimes))])}
    dTemp = pd.DataFrame(dTemp)
    dTemp_2 = pd.concat(dExchanges)
    dTemp_2['code'] = dTemp_2['exchange'] + '-' + dTemp_2['pair']
    dTemp_2 = pd.concat([dTemp_2, dTemp])

    fig0 = px.line(dTemp_2, x='datetime', y='price', color='code')
    fig0.update_layout(title='Latent Price of ETH', 
                       xaxis_title="Datetime", 
                       yaxis_title="Price of ETH in US Dollars", 
                       legend=dict(yanchor="top", y=0.99, xanchor="right", x=1.3), )
    
    
    rvs = [realizedVolatility(pStar[i - rvWindowSeconds: i], rvSmoothingExponent) for i in range(rvWindowSeconds, len(pStar))]
    dTemp_1 = {'datetime': datetimes[rvWindowSeconds:], 'rv': rvs}
    dTemp_1 = pd.DataFrame(dTemp_1)
    fig1 = px.line(dTemp_1, x='datetime', y='rv')
    fig1.update_layout(title='Realized Volatility Based on Latent ETH Price Timeseries', 
                       xaxis_title="Datetime", 
                       yaxis_title="Realized Volatility")

    #fig = px.line(x=range(10), y=range(10), title='Coming Soon!')
    return fig0, fig1, pStar


def dataForVECMGet(secretDict, timestampLower, timestampUpper):
    
    # get all the data from the database
    dbUsername = secretDict['dbUsername']
    dbPassword = secretDict['dbPassword']
    dbHostname = secretDict['dbHostname']
    database = secretDict['database']
    df = dbQuery(dbUsername, dbPassword, dbHostname, database, timestampLower, timestampUpper)

    # find all the exchanges and pairs
    allExchangePairs = list(set([tuple(i) for i in df[['exchange', 'pair']].values]))
    
    # split up the data by exchange and pair
    dExchanges = [dfNormalize(df[(df['exchange'] == i[0]) & (df['pair'] == i[1])]) for i in allExchangePairs]
    
    # ensure all dataframes begin and end at the same time
    beginTimestamp = max([i.iloc[0]['datetime'] for i in dExchanges])
    endTimestamp = min([i.iloc[-1]['datetime'] for i in dExchanges])
    
    dExchanges = [i[(i['datetime'] >= beginTimestamp) & (i['datetime'] <= endTimestamp)] for i in dExchanges]
    return dExchanges

def dbQuery(dbUsername, dbPassword, dbHostname, database, timestampLower, timestampUpper):

    try:
        conn = psycopg2.connect (dbname = database,
                                 user = dbUsername,
                                 password = dbPassword,
                                 host = dbHostname,
                                 connect_timeout = 10)
        
        query = """SELECT timestamp, exchange, symbol, price from trade_pairs where symbol::text like 'ETH%%' 
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
        print("Some problem")

def dfNormalize(df):
    
    df1 = df.copy()
    df1.set_index('datetime', inplace=True)
    df1 = df1.asfreq(freq='S', method='pad')
    df1.reset_index(inplace=True)
    df1['datetime'] = df1['datetime'].apply(lambda x: x.replace(microsecond=0))
    
    return df1

def vecmPriceGet(k_ar_diff, dExchanges, exponentialSmoothingFactor):
    
    nTimeseries = len(dExchanges)
    coint_rank = nTimeseries - 1

    priceArray = np.array([i['price'] for i in dExchanges]).transpose()
    
    priceArray = np.log(priceArray)
    
    model, resid = weightedVECM(priceArray, k_ar_diff, exponentialSmoothingFactor, None)
    
    coeff = model.coef_
    alpha = coeff[:, 0: coint_rank]
    gammaBig = coeff[:, coint_rank:]

    totalResid = np.linalg.norm(resid)
    
    iota = np.ones(shape=(nTimeseries,1))
    betaPerp = iota

    alphaAugmented  = np.concatenate((alpha,np.ones(shape=(nTimeseries,1))), axis = 1)

    oneHot = [0 for i in range(nTimeseries)]
    oneHot[-1] = 1
    alphaPerp = np.dot(oneHot, np.linalg.inv(alphaAugmented)).reshape((nTimeseries,1))
    
    gammaBig = gammaBig.reshape((nTimeseries,nTimeseries, k_ar_diff))
    gamma = np.eye(nTimeseries) - np.sum(gammaBig, axis = 2)

    residSum = np.cumsum(np.dot(alphaPerp.transpose(), resid.transpose()))
    CC = 1./np.dot(alphaPerp.transpose(), np.dot(gamma, betaPerp))[0,0]
    pStar = CC * residSum
    
    weighted = np.dot(priceArray, alphaPerp)
    
    shift = shiftGet(pStar, weighted)
    pStar = pStar + shift
    pStar = np.exp(pStar)

    return pStar


# Use regression from scikit-learn to do weighted least squares.  We use exponentially decreasing weights.
def weightedVECM(priceArray, k_ar_diff, exponentialSmoothingFactor, model):
    
    nSample, nTimeseries = priceArray.shape
    coint_rank = nTimeseries - 1
    
    beta = np.zeros(shape=(nTimeseries, coint_rank))
    beta[0,:] = np.ones(coint_rank)
    for i in range(coint_rank):
        beta[i + 1,i] = -1.0
      
    deltaY = np.diff(priceArray, axis = 0)
    y = deltaY[k_ar_diff:,:]
    
    weights = np.flip([exponentialSmoothingFactor**i for i in np.arange(y.shape[0])])
    weights = weights/sum(weights)
    
    rho = sum([weights[i] * np.dot(beta.transpose(), priceArray[-i,:]) for i in range(len(weights))])/sum(weights)
                                                                                                                   
    X = np.zeros(shape=(nSample - k_ar_diff - 1,coint_rank + (nTimeseries * k_ar_diff)))
    for i in range(k_ar_diff + 1, nSample):
        lags = deltaY[i - k_ar_diff - 1:i - 1, :].flatten()
        thisRow = np.concatenate((np.dot(beta.transpose(), priceArray[i - 1,:]) - rho, lags))
        X[i - k_ar_diff - 1,:] = thisRow
    
    if model == None:
        model = LinearRegression(n_jobs=1, fit_intercept=False).fit(X, y, sample_weight=weights)
    
    resid = y - model.predict(X)
    
    return model, resid



def shiftGet(pStar, weighted):
    # minimize sum (weighted - (pStar + c))**2
    # so calculate: sum ( weighted - pStar - c) = 0
    
    startIndex = len(weighted) - len(pStar)
    
    shift = sum(weighted[startIndex:].flatten() - pStar.flatten())/len(pStar)
    return shift

def realizedVolatility(timeseries, rvSmoothingExponent):
    
    weights = np.flip(np.exp(-rvSmoothingExponent * np.arange(len(timeseries)-1)))
    return 100 * np.sqrt(SECONDSPERYEAR * np.average(np.diff(np.log(timeseries)) ** 2, weights=weights))



_ = '''
def timestampGeneration(firstBegin, lastBegin, trainTimedelta, testTimedelta):
    timestampList = []
    currentStamp = firstBegin
    
    while currentStamp <= lastBegin:
        beginTrain = currentStamp.strftime("%Y-%m-%d %H:%M:%S")
        endTrain = (currentStamp + trainTimedelta).strftime("%Y-%m-%d %H:%M:%S")
        
        beginTest = endTrain
        endTest = (currentStamp + trainTimedelta + testTimedelta).strftime("%Y-%m-%d %H:%M:%S")
        
        currentStamp += trainTimedelta + testTimedelta
        timestampList.append([[beginTrain,endTrain], [beginTest,endTest]])
        
    return timestampList

def modelEval(thisParam):
    
    print("Label: ", thisParam['label'])
    
    firstBegin = datetime.datetime(2021, 11, 11, 1, 0, 0)
    lastBegin = datetime.datetime(2021, 11, 11, 6, 0, 0)
    trainTestRatio = 2

    k_ar_diff = thisParam['lag']
    exponentialSmoothingFactor = thisParam['exponentialSmoothingFactor']
    trainTimedelta = datetime.timedelta(days=0, seconds=thisParam['window'])
    testTimedelta = trainTimedelta/trainTestRatio

    timestamps = timestampGeneration(firstBegin, lastBegin, trainTimedelta, testTimedelta)

    modelResiduals = []
    for j,thisTrainTest in enumerate(timestamps):
        [[trainBegin, trainEnd],[testBegin, testEnd]] = thisTrainTest
        
        trainExchanges = dataForVECMGet(trainBegin, trainEnd)
        trainPriceArray = np.log(np.array([i['price'] for i in trainExchanges]).transpose())
        model, resid_train = weightedVECM(trainPriceArray, k_ar_diff, exponentialSmoothingFactor, None)

        testExchanges = dataForVECMGet(testBegin, testEnd)
        testPriceArray = np.log(np.array([i['price'] for i in testExchanges]).transpose())
        _, resid_test = weightedVECM(testPriceArray, k_ar_diff, exponentialSmoothingFactor, model)
        modelResiduals.append({'resid_test':resid_test, 
                               'resid_train': resid_train, 
                               'trainDates':[trainBegin, trainEnd], 
                               'testDates':[testBegin, testEnd]})
              
    return {'params': thisParam, 'residuals': modelResiduals}

def modelSelectionSerial(paramList):
    
    residList = []
    numModel = len(paramList)
    
    for thisParam in paramList:
        modelResiduals = modelEval(thisParam)    
        residList.append(modelResiduals)
        
    return residList   

def paramListMake():
    smoothingCutoff = 100

    lagList = [2**i for i in range(3,5)]
    smoothingRatioList = [1. - .1**i for i in range(2,3)]
    smoothingWindow = [int(np.log(1/smoothingCutoff)/np.log(i)) for i in smoothingRatioList]
    smoothingParams = list(zip(smoothingRatioList, smoothingWindow)) 
    slidingWindowParams = [(1.,2**i) for i in range(8,11)]
    paramList = [{'lag':lag, 'exponentialSmoothingFactor':j[0], 'window':j[1]} for lag in lagList for j in smoothingParams + slidingWindowParams]
    updateInPlaceTemp = [j.update({'label':i}) for i,j in enumerate(paramList)]
    
    return paramList
'''