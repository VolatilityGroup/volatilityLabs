#%%
import moralis

moralisKey = 'NNoCZq119D6XKqw5UGXHrVMcAembtBdFNIHp0kVXDWlw1pLFMoYV50H4CAUQdOZr'
apeAddress = '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D'
punkAddress = '0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB'
azukiAddress = '0xED5AF388653567Af2F388E6224dC7C4b3241C544'

#%%
url = 'https://deep-index.moralis.io/api/v2/nft/%s?chain=eth&format=decimal' % apeAddress
allResults = moralis.moralisAll(url, moralisKey)

# %%
url = "https://deep-index.moralis.io/api/v2/info/endpointWeights"
temp = moralis.moralisGet(url,None, moralisKey)

#%%
from datetime import date, timedelta
tokenAddress = azukiAddress
daysBack = 10
from_date = str(date.today() - timedelta(days=daysBack))
to_date = str(date.today())

urlTrades = 'https://deep-index.moralis.io/api/v2/nft/%s/trades?chain=eth&marketplace=opensea&from_date=%s&to_date=%s' % (tokenAddress, from_date, to_date)
allResults = moralis.moralisAll(urlTrades, moralisKey, True)
#allResults = moralis.moralisGet(urlTrades, None, moralisKey)
# %%

# get all NFT info
url = 'https://deep-index.moralis.io/api/v2/nft/search?q=Bored%20Ape&filter=name'
allResults = moralis.moralisGet(url, None, moralisKey)

# %%

temp = [i['token_address'] for i in allResults['result']]
# %%
