import bs4
from bs4 import BeautifulSoup
import urllib
import requests
import pandas as pd
URL = "https://www.indeed.com/cmp/{}/reviews?fcountry=IN&start={}"
company = "Google"
page_start = 0
page_end = 500
title = []
reviewer = []
location = []
date = []
review = []
pros =[]
cons = []
def get_content(URL):
    df = pd.DataFrame()
    for page in range(page_start, page_end, 20):
        html = requests.get(URL.format(company, page))
        soup = BeautifulSoup(html.content, 'html.parser', from_encoding="utf-8")
        for each in soup.find_all(class_= "cmp-review-title" ):
            try: 
                title.append(each.find('span', {'itemprop':"name" }).text.replace('\n', ''))
            except:
                title.append('None')
        for each in soup.find_all(class_= "cmp-review-subtitle" ):
            try: 
                reviewer.append(each.find('span', {'class':"cmp-reviewer"}).text.replace('\n', ''))
            except:
                reviewer.append('None')
            try: 
                location.append(each.find('span', {'class':"cmp-reviewer-job-location"}).text.replace('\n', ''))
            except:
                location.append('None')
            try: 
                date.append(each.find('span', {'class':"cmp-review-date-created"}).text.replace('\n', ''))
            except:
                date.append('None')
        for each in soup.find_all(class_= "cmp-review-content-container" ):
            try: 
                review.append(each.find('span', {'class':"cmp-review-text"}).text.replace('\n', ''))
            except:
                review.append('None')

            try: 
                pros.append(each.find('div', {'class':"cmp-review-pro-text"}).text.replace('\n', ''))
            except:
                pros.append('None')

            try: 
                cons.append(each.find('div', {'class':"cmp-review-con-text"}).text.replace('\n', ''))
            except:
                cons.append('None')
    df['Review Title'] = title
    df['Reviewer Name'] = reviewer
    df['Location'] = location
    df['Date'] = date
    df['Review'] = review
    df['Pros'] = pros
    df['Cons'] = cons
    df.to_csv('indeed_reviews.csv', index=False)
get_content(URL)