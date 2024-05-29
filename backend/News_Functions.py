import requests
import apikeys
from datetime import datetime, timedelta

NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

def get_news(company_name):
    '''
    Inputs:
        company_name: string, name of company to search for news
    Outputs:
        three_articles: list of 3 dictionaries with keys: 
            source, author, title, description, url, urlToImage, publishedAt, content
    '''
    current_date = datetime.now()
    yesterday_date = current_date - timedelta(days=2)
    formatted_date = yesterday_date.strftime('%Y-%m-%d')
    
    
    news_params = {
    "apiKey": apikeys.NEWS_API_KEY,
    "q": company_name,
    "searchIn": 'title',
    "from": str(formatted_date),
    "sortBy": "popularity",
    "language": "en",
    }
    
    news_response = requests.get(NEWS_ENDPOINT, params=news_params)
    articles = news_response.json()["articles"]

    three_articles = articles[:10]

    sources_and_titles = []
    for article in three_articles:
        if article['source']['name'] != '[Removed]':
            source = article['source']['name']
            title = article['title']
            url = article['url']
            sources_and_titles.append({'source': source, 'title': title, 'url': url})
    
    return sources_and_titles 