import requests
import pandas as pd
import os

def get_articles(code) :
    url = "https://news-api14.p.rapidapi.com/v2/search/articles"
    headers = {
    "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
    "x-rapidapi-host": "news-api14.p.rapidapi.com"
    }
    values = []
    querystring = {"query":code,"language":"id","limit":"10"}
    response = requests.get(url, headers=headers, params=querystring)
    for article in response.json()['data'] :
        article_record = []
        article_record.append(code)
        article_record.append(article["title"])
        article_record.append(article["excerpt"])
        article_record.append(article["url"])
        article_record.append(article["publisher"]['name'])
        article_record.append(article["date"])
        values.append(article_record)
    return values
  
def to_dataframe(values) :
    df = pd.DataFrame(values, columns=["Code", "Title", "Description", "URL", "Publisher", "Date"])
    return df
  
def change_date_format(articles_df) :
    articles_df["Date"] = pd.to_datetime(articles_df["Date"])
    articles_df["Date"] = articles_df["Date"].apply(lambda x: x.strftime("%Y-%m-%d"))
    return articles_df

def fill_publisher(row):
    if "https" in row["Publisher"] or row["Publisher"] == '':
        return row["URL"].split("/")[2].replace("www.", "")
    else :
        return row["Publisher"]