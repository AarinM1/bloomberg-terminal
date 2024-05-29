import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


def get_stock_data(symbol):
    '''
    Input:
        symbol: stock ticker symbol
    Output: 
        data: pandas df from yahoo finance api  
    Notes:
        columns for the stock daily: date, open, close, high, low, volume, dividends, stock splits
    '''
    stock = yf.Ticker(symbol)
    data = stock.history(period="max")
    data.index = pd.to_datetime(data.index)
    return data

def clean_data(data):
    '''
    Input: 
        data: pandas df from yahoo finance get_stock_data function
    Output: 
        data: pandas df 
    Notes:
        removed Dividends & Stock Splits columns, added Tomorrow & Target columns, removed data before 2000
    '''
    del data["Dividends"]
    del data["Stock Splits"]
    del data["Volume"]
    del data["Low"]
    del data["High"]
    del data["Open"]
    data["Tomorrow"] = data["Close"].shift(-1)
    data["Target"] = (data["Tomorrow"] > data["Close"]).astype(int)
    data = data.loc["2000-01-01":].copy()
    return data

def create_model(train_data):
    '''
    Input: 
        train_data: pandas df for training
    Output: 
        model: Random Forest Model
    Notes: 
        n-estimators is the number of decision trees we want to train, the higher, the better up till a limit
        min-sample split: protect against overfit, the higher the less accurate the model will be, but the less it will overfit
        randomstate: helps test model. i.e randomstate = 1
    '''
    model = RandomForestClassifier(n_estimators=300, min_samples_split=50)
    return model
# RandomForest works by a bunch of individual decision trees with randomized parameters and then averaging the
# results from the decision trees, so more RESISTANT TO OVERFITTING
# run relatively quickly 
# can pick up non-linear tendencies in the data

def add_predictors(data):
    '''
    Input: 
        data: pandas df stock data
    Output: 
        data: updated df with new column for each new predictor
        new_predictor: array with close_ratio for each benchmark
    Notes: 
        adding rolling averages predictors for 1 day, 1 week, 1 month, 3 months (1 qtr), 1 year, 5 years
    '''
    benchmarks = [2, 5, 21, 21*3, 252, 252*5]
    new_predictors = []

    for benchmark in benchmarks:
        rolling_averages = data.rolling(benchmark).mean()
        
        ratio_column = f"Close_Ratio_{benchmark}"
        data[ratio_column] = data["Close"] / rolling_averages["Close"] # todays close / rolling avg of last benchmark days

        new_predictors += [ratio_column]

    data = data.dropna(subset=data.columns[data.columns != "Tomorrow"]) # looses oldest 5 yrs of data from benchmark 252*5
    return data, new_predictors

def predict(train, test, predictors, model):
    '''
    Inputs: 
            train: pandas df for training data for the model
            test: pandas df for testing model 
            predictors: array of column titles that will be inputs for ML
            model: Random Forest Model
    Outputs:
        combined: pandas df with columns: date, Target, Predictions
    Notes:
        Use predict_proba function to find probability of going up, 
            set cut-off at 60% to increase accuracy of prediction
    '''
    model.fit(train[predictors], train["Target"])
    preds = model.predict_proba(test[predictors])[:, 1] # 2nd column, probabilty the stock price goes up
    
    preds_60 = preds.copy()
    preds_60[preds_60 >= 0.60] = 1 # increase confidence of model that price will go up (60%)
    preds_60[preds_60 < 0.60] = 0
    preds_60 = pd.Series(preds_60, index=test.index, name="Predictions_60%")

    
    combined = pd.concat([test["Target"], preds_60], axis=1)
    return combined

def backtest(data, model, predictors, start=252*10, step=21*3):
    '''
    Inputs:
        data: pandas df
        model: Random Forest Model
        predictors: array of column titles that will be inputs for ML
        start: integer, default is stock trading days in 10 years, 
            starts by from the 10th year of data
        step: integer, default is stock trading days in 3 months,
            increment value of a quarter of a year
    Outputs:
        res: pandas df with columns: date, Target, Predictions for each trading day
    '''
    all_predictions = []

    for i in range(start, data.shape[0], step): # loop across data year by year, make predictions each year except first 10 yrs
        train = data.iloc[0:i].copy() # all years prior to current yr
        test = data.iloc[i:(i + step)].copy() # current yr
        predictions = predict(train, test, predictors, model)
        all_predictions.append(predictions)
    
    res = pd.concat(all_predictions)
    
    return res

def buy_stock(stock):
    '''
    Input:
        stock: stock ticker symbol
    Output:
        predictions: pandas df with columns: date, Target, Predictions
        data: pandas df with stock data (date, open, close, high, low, volume, tomorrow, target, close_ratios)
    Notes:
        Calls all above functions in one function for a single input stock
    '''
    data = get_stock_data(stock)
    data = clean_data(data)
    train_data = data.iloc[:-100] # All rows except the last 100
    test_data = data.iloc[-100:] # last 100 rows
    model = create_model(train_data)
    data, new_predictors = add_predictors(data)
    new_predictors += ['Close']
    start_value = data.shape[0] // 5
    predictions = backtest(data, model, new_predictors, start=start_value)

    return predictions

def today_stock_info(stock_symbol):
    '''
    Input:
        stock: string, stock ticker symbol
    Output:
        data: dictionary with keys: High, Low, Close
    Notes:
        Gets the high, low, and close of the stock for the latest day
    '''
    stock = yf.Ticker(stock_symbol)
    today_history = stock.history(period='1d')
    
    today_high = round(today_history.iloc[0]['High'], 2)
    today_low = round(today_history.iloc[0]['Low'], 2)
    today_close = round(today_history.iloc[0]['Close'], 2)

    stock_info = stock.info
    today_forward_pe = round(stock_info['forwardPE'], 2)
    today_market_cap =  '{:.2e}'.format(stock_info['marketCap'])

    data =  {
        'High': today_high,
        'Low': today_low,
        'Close': today_close,
        'Forward PE': today_forward_pe,
        'Market Cap': today_market_cap}
    
    return data
