import requests
import time
from datetime import date, timedelta

# GET A SINGLE PAGE
def moralisGet(url, offset, moralisKey):
    if offset:
      url = url + "&offset=%s" % str(offset)

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": moralisKey
    }
    statusResponse = requests.request("GET", url, headers=headers)
    data = statusResponse.json()
    return data

# GET ALL PAGES
def moralisAll(url, moralisKey, report):
    offset = 0
    allResult = []
    while True:
        data = moralisGet(url, offset, moralisKey)
        try:
            if report:
                print(data['page'] * 500, data['total'])
            if len(data['result']) == 0:
                return allResult
            else:
                allResult.extend(data['result'])
                offset += 500
                time.sleep(1.0)
        except:
            print(data)
            return allResult

def nftTradesURL(tokenAddress, daysBack):
    from_date = str(date.today() - timedelta(days=daysBack))
    to_date = str(date.today())

    urlTrades = 'https://deep-index.moralis.io/api/v2/nft/%s/trades?chain=eth&marketplace=opensea&from_date=%s&to_date=%s' % (tokenAddress, from_date, to_date)
    return urlTrades