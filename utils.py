import requests
from bs4 import BeautifulSoup
import urllib.parse

def google_search(keyword, site, page=0, headers=None):
    search_results = []
    query = f'site:{site} "We don\'t know when or if this item will be back in stock." {keyword}'
    
    # 计算start参数的值，Google API 每页最多返回10个结果
    start = page * 10 + 1
    
    # 构建API请求URL
    search_url = (
        f'https://www.googleapis.com/customsearch/v1?key={AIzaSyAwdeeXOjyDULUWHqzetfWTZbybcEm3EDc}&cx={533552966603-vf3im8ncgtngblj1cbsr1ua47lpd43gd.apps.googleusercontent.com}&q={urllib.parse.quote(query)}&start={start}'
    )
    
    response = requests.get(search_url, headers=headers)
    data = response.json()
    
    # 从API响应中解析搜索结果
    if 'items' in data:
        for item in data['items']:
            title = item.get('title')
            link = item.get('link')
            search_results.append((title, link))
    
    return search_results

def bing_search(keyword, site, page=0, headers=None):
    search_results = []
    query = f'site:{site} "We don\'t know when or if this item will be back in stock." {keyword}'
    search_url = f'https://www.bing.com/search?q={urllib.parse.quote(query)}&first={page * 10 + 1}'
    
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    for result in soup.find_all('li', class_='b_algo'):
        title_element = result.find('h2')
        link_element = result.find('a')
        if title_element and link_element:
            title = title_element.text
            link = link_element['href']
            search_results.append((title, link))
    
    return search_results
