import streamlit as st
import pandas as pd
import pymysql
import sqlalchemy
from io import BytesIO
import time
import random
import requests
from bs4 import BeautifulSoup
from utils import google_search, bing_search

# 连接到Google Cloud SQL数据库
def get_database_connection():
    db_config = {
        'user': 'your_username',  # 替换为你的数据库用户名
        'password': '',  # 留空，使用Cloud SQL IAM或其他安全方式
        'host': 'your_instance_ip_or_host',
        'database': 'your_database_name'
    }
    engine = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL(
            drivername='mysql+pymysql',
            username=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            database=db_config['database']
        )
    )
    return engine

# 创建用户表
def create_user_table(engine):
    with engine.connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
            """
        )

# 注册用户
def register_user(engine, username, password):
    with engine.connect() as connection:
        result = connection.execute(
            "SELECT * FROM users WHERE username = %s", (username,)
        )
        if result.fetchone():
            return False  # 用户已存在
        connection.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )
        return True

# 验证用户
def verify_user(engine, username, password):
    with engine.connect() as connection:
        result = connection.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username, password)
        )
        return result.fetchone() is not None

def login_or_register(engine):
    st.subheader("登录或注册")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    
    if st.button("登录"):
        if verify_user(engine, username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"欢迎回来，{username}!")
        else:
            st.error("用户名或密码错误")

    if st.button("注册"):
        if register_user(engine, username, password):
            st.success("注册成功，请登录")
        else:
            st.error("用户名已存在，请选择其他用户名")

# 在应用主函数中处理登录状态
def main():
    engine = get_database_connection()
    create_user_table(engine)

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        login_or_register(engine)
    else:
        st.title(f"欢迎，{st.session_state.username}!")
        st.write("你已经成功登录，现在可以使用该工具。")
        app_functionality()

# 应用的主功能逻辑
def app_functionality():
    st.title("亚马逊僵尸链接查询工具")
    st.write("遇到问题联系：happy_prince45")
    st.subheader("搜索设置")
    search_engine = st.selectbox("选择搜索引擎", ["Google", "Bing"])
    amazon_site = st.selectbox("选择亚马逊站点", [
        "amazon.com", "amazon.ca", "amazon.co.uk", "www.amazon.com.au", 
        "www.amazon.in", "www.amazon.sg", "www.amazon.ae"
    ])
    keyword = st.text_input("输入关键词")
    max_links = st.slider("查询链接数限制", 3, 15, 5)

    if st.button("搜索"):
        all_results = fetch_all_results(search_engine, keyword, amazon_site, max_links)

        if all_results:
            filtered_results = [
                (title, link) for title, link in all_results 
                if "sellercentral" not in link
            ]

            if filtered_results:
                st.session_state.results = []
                for title, link in filtered_results:
                    asin = extract_asin(link)
                    image_url = extract_image_url(asin) if asin else None
                    image_tag = f'<img src="{image_url}" style="width:100px;height:100px;object-fit:cover;"/>' if image_url else f'<img src="https://ninjify.shop/wp-content/uploads/2024/08/微信图片_20240831012417.jpg" style="width:100px;height:100px;object-fit:cover;"/>'
                    st.session_state.results.append({"Image": image_tag, "Title": title, "URL": link, "ASIN": asin})

                st.subheader(f"搜索结果-试用版限制{max_links}条，如果要取消限制，请联系管理员")
                
                results_df = pd.DataFrame(st.session_state.results)
                results_df['Title'] = results_df.apply(lambda row: f'<a href="{row["URL"]}">{row["Title"]}</a>', axis=1)
                results_df = results_df[['Image', 'Title', 'ASIN']]
                
                st.markdown(results_df.to_html(escape=False, index=False), unsafe_allow_html=True)
                
                download_df = results_df[['Title', 'ASIN']].copy()
                download_df['URL'] = [result['URL'] for result in st.session_state.results]
                excel_buffer = BytesIO()
                download_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_buffer.seek(0)

                st.download_button(
                    label="导出并下载Excel",
                    data=excel_buffer,
                    file_name="search_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.write("未找到相关结果（已排除包含'sellercentral'的链接）")
        else:
            st.write("未找到相关结果")

    st.subheader("联系方式")
    st.write("关注公众号“Hapince出海日记”")
    st.image("image/publicwechat.jpg")

def fetch_all_results(search_engine, keyword, amazon_site, max_links=50):
    page = 0
    all_results = []
    
    progress_bar = st.progress(0)

    while len(all_results) < max_links:
        delay = random.uniform(2, 5)
        time.sleep(delay)
        
        if search_engine == "Google":
            headers = {'User-Agent': get_random_user_agent()}
            results = google_search(keyword, amazon_site, page, headers=headers)
        elif search_engine == "Bing":
            headers = {'User-Agent': get_random_user_agent()}
            results = bing_search(keyword, amazon_site, page, headers=headers)
        
        if not results:
            break

        all_results.extend(results)
        
        if len(all_results) > max_links:
            all_results = all_results[:max_links]
        
        progress = len(all_results) / max_links
        progress_bar.progress(progress)
        
        page += 1

    progress_bar.progress(1.0)
    
    return all_results

def get_random_user_agent():
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.54',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    return random.choice(USER_AGENTS)

def extract_asin(url):
    if "dp/" in url:
        parts = url.split("dp/")
        if len(parts) > 1:
            asin_part = parts[1].split('/')[0][:10]
            return asin_part
    return None

def extract_image_url(asin):
    headers = {'User-Agent': get_random_user_agent()}
    product_url = f"https://www.amazon.com/dp/{asin}"
    response = requests.get(product_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    img_tag = soup.find('img', {'id': 'landingImage'})
    if not img_tag:
        img_tag = soup.find('img', {'class': 'a-dynamic-image'})
    
    if img_tag and 'src' in img_tag.attrs:
        return img_tag['src']
    
    return None

if __name__ == "__main__":
    main()
