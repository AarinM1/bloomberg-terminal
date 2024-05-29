import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, LineElement, CategoryScale, LinearScale, PointElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import './App.css';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Title, Tooltip, Legend, Filler);

// Time periods to convert keys to strings for display
const timePeriods = {
  '1d': '1 Day',
  '1w': '1 Week',
  '1mo': '1 Month',
  '3mo': '3 Months',
  '6mo': '6 Months',
  '1y': '1 Year',
  '2y': '2 Years',
  '5y': '5 Years',
};
function App() {
  // variables
  const [articles,setArticles] = useState([]);
  const [companyName,setCompanyName] = useState('');
  const [displayCompanyName,setDisplayCompanyName] = useState('');
  const [tickerSymbol,setTickerSymbol] = useState('');
  const [error, setError] = useState(null);
  const [stockInfo,setStockInfo] = useState(null);
  const [high, setHigh] = useState(null);
  const [low, setLow] = useState(null);
  const [latestClosingPrice,setLatestClosingPrice] = useState(null);
  const [stockData,setStockData] = useState([]);
  const [percentChange,setPercentChange] = useState(null);
  const [closingCostRange,setClosingCostRange] = useState({min: null, max: null});
  const [showContent,setShowContent] = useState(false);
  const [selectedPeriod,setSelectedPeriod] = useState('1y');
  const [buyStockResult, setBuyStockResult] = useState({should_buy_stock: 'Loading...', buy_stock_precision_score: 'Loading...'});

  // update the set latestClosingPrice when stockInfo is updated
  useEffect(() => {
    if (stockInfo && stockInfo.Close) {
      setLatestClosingPrice(stockInfo.Close);
    }
  }, [stockInfo]);

  // when enter button is clicked, input period is number of days
  const enterButtonClick = (period) => {
    // if company name and/or ticker symbol is not entered, show error
    if (!companyName && !tickerSymbol) {
      setError('Please enter both a company name and ticker symbol');
      return;
    }
    if (!companyName) {
      setError('Please enter a company name');
    }
    if (!tickerSymbol) {
      setError('Please enter a ticker symbol');
    }

    // set veriables and default values
    setDisplayCompanyName(companyName);
    setError(null);
    setStockInfo(null);
    setPercentChange(null);
    setShowContent(true);
    setBuyStockResult({ should_buy_stock: 'Loading...', buy_stock_precision_score: 'Loading...' });

    // backend api urls
    const newsApiUrl = `/api/news?name=${companyName}`;
    const dailyStockInfoApiUrl = `/api/today_stock_info?symbol=${tickerSymbol}`;
    const stockDataApiUrl = `/api/get_stock_data?symbol=${tickerSymbol}&period=${period}`;
    const buyStockApiUrl = `/api/buy_stock?symbol=${tickerSymbol}`;

    let newError = '';

    // fetch from news api
    fetch(newsApiUrl)
      .then(response => response.json())
      .then(data => {
        setArticles(data.articles);
        // if no articles are found, show error
        if (data.articles.length === 0) {
          newError += 'Company name not found. ';
          setError(newError.trim());
        }
      })
      .catch(error => {
        console.error('Error fetching news data:', error);
      });

    // fetch from stock info api
    fetch(dailyStockInfoApiUrl)
      .then(response => response.json())
      .then(data => {
        setHigh(data.High);
        setLow(data.Low);
        setStockInfo(data);
      })
      .catch(error => {
        // runs if wrong ticker symbol is entered
        console.error('Error fetching stock info:', error);
        if (!newError.includes('ticker')) {
          newError += ' Invalid ticker symbol. ';
          setError(newError.trim());
        }
      });

    fetch(stockDataApiUrl)
      .then(response => response.json())
      .then(data => {
        setStockData(data.stock_data);
        setPercentChange(data.percent_change);
        setClosingCostRange(data.closing_cost_range);
      })
      .catch(error => {
        // runs if wrong ticker symbol is entered
        console.error('Error fetching stock data:', error);
        if (!newError.includes('ticker')) {
          newError += ' Invalid ticker symbol. ';
          setError(newError.trim());
        }
      });

    fetch(buyStockApiUrl)
      .then(response => response.json())
      .then(data => {
        setBuyStockResult(data);
      })
      .catch(error => {
        // runs if wrong ticker symbol is entered
        console.error('Error fetching buy stock data:', error);
        if (!newError.includes('ticker')) {
          newError += ' Invalid ticker symbol. ';
          setError(newError.trim());
        }
      });
  };

  // when any of the buttons are clicked on the chart to change the time period
  const handleTimePeriodClick = (periodKey) => {
    setSelectedPeriod(periodKey);
    enterButtonClick(periodKey);
  };

  const chartData = {
    labels: stockData.map(item => item.Date),
    datasets: [
      {
        label: 'Stock Price',
        data: stockData.map(item => item.Close),
        borderColor: 'blue',
        backgroundColor: 'lightblue',
        fill: true,
        lineTension: 0.0,
        pointRadius: 0,
      },
    ],
  };

  // period for displaying
  const periodLabel = timePeriods[selectedPeriod];

  return (
    // display frontend
    <div className="App">
      <h1>Bloomberg Terminal</h1>
      <p>Enter stock details to get information.</p>
      <input
        type="text"
        placeholder="Company Name"
        value={companyName}
        onChange={(e) => setCompanyName(e.target.value)}
      />
      <input
        type="text"
        placeholder="Ticker Symbol"
        value={tickerSymbol}
        onChange={(e) => setTickerSymbol(e.target.value)}
      />
      <button onClick={() => enterButtonClick('1y')}>Enter</button>
      {error && <p className="error">{error}</p>}

      {showContent && (
        <>
          <h2>Latest News on {displayCompanyName.toUpperCase()}</h2>
          <div className="news-container">
            <ul>
              {articles.map((article, index) => (
                <li key={index} className="news-item">
                  <strong>{article.title}</strong><br />
                  Source: <a href={article.url} target="_blank" rel="noopener noreferrer">{article.source}</a>
                </li>
              ))}
            </ul>
          </div>

          {stockInfo && (
            <div className="stock-info">
              <h2>{displayCompanyName.toUpperCase()}'s Stock Information</h2>
              <p>24 Hour Range: ${low} - ${high}</p>
              <p>Latest Closing Price: ${latestClosingPrice}</p>
              <p>Latest Forward PE: {stockInfo['Forward PE']}</p>
              <p>Latest Market Cap: ${stockInfo['Market Cap']}</p>
            </div>
          )}

          <div className="time-period-buttons">
            <button onClick={() => handleTimePeriodClick('1d')}>1 Day</button>
            <button onClick={() => handleTimePeriodClick('1w')}>1 Week</button>
            <button onClick={() => handleTimePeriodClick('1mo')}>1 Month</button>
            <button onClick={() => handleTimePeriodClick('3mo')}>3 Months</button>
            <button onClick={() => handleTimePeriodClick('6mo')}>6 Months</button>
            <button onClick={() => handleTimePeriodClick('1y')}>1 Year</button>
            <button onClick={() => handleTimePeriodClick('2y')}>2 Years</button>
            <button onClick={() => handleTimePeriodClick('5y')}>5 Years</button>
          </div>
          {percentChange !== null && (
            <div>
              <p>{periodLabel} Percent Change: {percentChange}%</p>
              <p>{periodLabel} Range: ${closingCostRange.min} - ${closingCostRange.max}</p>
            </div>
          )}
          {buyStockResult.should_buy_stock !== 'Loading...' ? (
            <div>
              <p>Should Buy Stock? {buyStockResult.should_buy_stock}</p>
              <p>This is a recommendation using a ML model with a precision score of {buyStockResult.buy_stock_precision_score}.</p>
            </div>
          ) : (
            <div>
              <p>Should Buy Stock? <span className="placeholder">Loading...</span></p>
              <p>This is a recommendation using a ML model. Please do your own research as well.</p>
            </div>
          )}
          <Line data={chartData} />
        </>
      )}
    </div>
  );
}

export default App;
