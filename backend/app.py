from flask import Flask, jsonify, request
import News_Functions
import Stock_Functions
from sklearn.metrics import precision_score
import pandas as pd

app = Flask(__name__)

@app.route('/api/news')
def news():
    # returns news articles for a given stock
    input_stock_name = request.args.get('name')
    articles = News_Functions.get_news(input_stock_name)
    response_data = jsonify(articles=articles)
    return response_data

@app.route('/api/today_stock_info')
def today_stock_info():
    # returns today's stock info for a given stock
    input_stock_symbol = request.args.get('symbol')
    data = Stock_Functions.today_stock_info(input_stock_symbol)
    response_data = jsonify(data)
    return response_data

@app.route('/api/get_stock_data')
def get_stock_data():
    # get stock symobl and period, default period set to 1 yr
    input_stock_symbol = request.args.get('symbol')
    period = request.args.get('period', '1y')

    data = Stock_Functions.get_stock_data(input_stock_symbol)
    cleaned_data = Stock_Functions.clean_data(data)
    cleaned_data.reset_index(inplace=True)
    cleaned_data['Date'] = cleaned_data['Date'].dt.strftime('%Y-%m-%d')
    filtered_data = cleaned_data[['Date', 'Close']]

    # days dictionary
    period_days = {
        '1d': 1+1,
        '1w': 5+1,
        '1mo': 21+1,
        '3mo': 21*3+1,
        '6mo': 21*6+1,
        '1y': 252+1,
        '2y': 252*2+1,
        '5y': 252*5+1,
    }
    days = period_days.get(period, 252+1)
    filtered_data = filtered_data.tail(days)

    if len(filtered_data) >= days:
        latest_data = filtered_data.iloc[-1]
        old_data = filtered_data.iloc[0]
        percent_change = ((latest_data['Close'] - old_data['Close']) / old_data['Close']) * 100
        percent_change = round(percent_change, 2)

        closing_prices = filtered_data['Close']
        closing_cost_range = {
            'min': round(min(closing_prices), 2),
            'max': round(max(closing_prices), 2)
        }
    else:
        percent_change = None
        closing_cost_range = {'min': None, 'max': None}

    response_data = {
        'stock_data': filtered_data.to_dict(orient='records'),
        'percent_change': percent_change,
        'closing_cost_range': closing_cost_range
    }

    return jsonify(response_data)

@app.route('/api/buy_stock')
def buy_stock():
    input_stock_symbol = request.args.get('symbol')
    predictions = Stock_Functions.buy_stock(input_stock_symbol)
    should_buy_stock = bool(predictions.iloc[-1][1])
    buy_stock_precision_score = precision_score(predictions["Target"], predictions["Predictions_60%"])

    should_buy_stock = "Yes" if should_buy_stock else "No"
    buy_stock_precision_score = f"{buy_stock_precision_score * 100:.2f}%"

    res = {
        'should_buy_stock': should_buy_stock,
        'buy_stock_precision_score': buy_stock_precision_score
    }

    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True)
