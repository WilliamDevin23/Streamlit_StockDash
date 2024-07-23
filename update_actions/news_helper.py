import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
import base64
from datetime import datetime

def get_articles(code) :
    if code == "IHSG" :
        QUERY = "IHSG"
    elif code == "LQ45" :
        QUERY = "LQ45"
    else :
        QUERY = "saham+{}".format(code)
    
    url = "https://news.google.com/rss/search?q={}&hl=id&gl=ID&ceid=ID:id".format(QUERY)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features='xml')

    values = []
    titles = soup.find_all("title")
    urls = soup.find_all("link")
    pub_dates = soup.find_all("pubDate")
    pubs = soup.find_all("source")
    for i in range(len(titles)) :
        if len(values) == 10 :
            break
        article_record = []

        title = titles[i+1].get_text().split(" - ")[0]
        url_ = urls[i+1].get_text()
        pub_date_splitted = pub_dates[i].get_text().split()
        pub_date = " ".join([pub_date_splitted[n] for n in range(1,4)])
        source = pubs[i].get_text()

        article_record.append(code)
        article_record.append(title)
        article_record.append(url_)
        article_record.append(pub_date)
        article_record.append(source)

        values.append(article_record)
    return values
  
def to_dataframe(values) :
    values = np.reshape(values, (-1, 5))
    df = pd.DataFrame(values, columns=["Code", "Title", "URL", "Date", "Publisher"])
    return df
  
def change_date_format(df) :
    df["Date"] = df["Date"].apply(lambda x: datetime.strptime(x, "%d %b %Y"))
    return df

def get_link(link) :
    try :
        link_2 = link.replace("https://news.google.com/rss/articles/", "")
        end_idx = link_2.index("?")
        link_2 = link_2[:end_idx]
        link_2 = re.sub(r'[^A-Za-z0-9\+=/]', 'A', link_2)
        if len(link_2) % 4 != 0 :
            link_2 += "="* (4 - len(link_2) % 4)
        translated = base64.b64decode(link_2)
        translated = translated.decode("iso-8859-1")
        url_match = re.findall(r"https*:[\-\.A-Za-z0-9/]*", translated)[0]
        return url_match
    except Exception as e :
        return link