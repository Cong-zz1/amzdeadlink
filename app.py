import streamlit as st
import pandas as pd
from io import BytesIO
import time
import random
import requests

# Replace with your actual Google Custom Search API key and search engine ID (cx)
API_KEY = 'AIzaSyAwdeeXOjyDULUWHqzetfWTZbybcEm3EDc'
CX = '533552966603-vf3im8ncgtngblj1cbsr1ua47lpd43gd.apps.googleusercontent.com'

def extract_asin(url):
    """Extract ASIN from Amazon product URL."""
    if "dp/" in url:
        parts = url.split("dp/")
        if len(parts) > 1:
            asin_part = parts[1].split('/')[0][:10]  # Extract only the first 10 characters
            return asin_part
    return None

def extract_image_url(asin):
    """Extract the main image URL from the Amazon product page."""
    headers = {'User-Agent': get_random_user_agent()}
    product_url = f"https://www.amazon.com/dp/{asin}"
    response = requests.get(product_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the image URL using different strategies
    img_tag = soup.find('img', {'id': 'landingImage'})  # Main product image
    if not img_tag:
        img_tag = soup.find('img', {'class': 'a-dynamic-image'})  # Another common class for images
    
    if img_tag and 'src' in img_tag.attrs:
        return img_tag['src']
    
    return None

def fetch_all_results(keyword, amazon_site, max_links=50):
    """Fetch results from Google Custom Search API until the desired number of links is reached."""
    all_results = []
    start_index = 1
    
    progress_bar = st.progress(0)  # Initialize progress bar

    while len(all_results) < max_links:
        # Set a random delay to mimic human behavior
        delay = random.uniform(2, 5)
        time.sleep(delay)
        
        results = google_search(keyword, amazon_site, start_index)
        
        # If no more results are found, break the loop
        if not results:
            break

        all_results.extend(results)
        
        # If more results than needed, truncate the list
        if len(all_results) > max_links:
            all_results = all_results[:max_links]
        
        # Update progress bar
        progress = len(all_results) / max_links
        progress_bar.progress(progress)
        
        start_index += 10  # Google Custom Search API returns 10 results per page

    progress_bar.progress(1.0)  # Ensure the progress bar reaches 100%
    
    return all_results


def main():
    st.title("亚马逊僵尸链接采集工具")
    st.write("遇到问题联系：happy_prince45")
    st.subheader("搜索设置")
    
    amazon_site = st.selectbox("选择亚马逊站点", [
        "amazon.com", "amazon.ca", "amazon.co.uk", "www.amazon.com.au", 
        "www.amazon.in", "www.amazon.sg", "www.amazon.ae"
    ])
    keyword = st.text_input("输入关键词")
    max_links = st.slider("请选择查询结果数量", 10, 50, 200)  # Allow user to set maximum number of links to fetch

    if st.button("搜索"):
        # Fetch results from all pages
        all_results = fetch_all_results(keyword, amazon_site, max_links)

        if all_results:
            # Filter out links containing 'sellercentral'
            filtered_results = [
                (title, link) for title, link in all_results 
                if "sellercentral" not in link
            ]

            if filtered_results:
                # Store filtered results in session state
                st.session_state.results = []
                for title, link in filtered_results:
                    asin = extract_asin(link)
                    image_url = extract_image_url(asin) if asin else None
                    # Use default image if no image found
                    image_tag = f'<img src="{image_url}" style="width:100px;height:100px;object-fit:cover;"/>' if image_url else f'<img src="https://ninjify.shop/wp-content/uploads/2024/08/微信图片_20240831012417.jpg" style="width:100px;height:100px;object-fit:cover;"/>'
                    st.session_state.results.append({"Image": image_tag, "Title": title, "URL": link, "ASIN": asin})

                st.subheader(f"搜索结果显示{max_links}条")
                
                # Display results in table format
                results_df = pd.DataFrame(st.session_state.results)
                results_df['Title'] = results_df.apply(lambda row: f'<a href="{row["URL"]}">{row["Title"]}</a>', axis=1)
                results_df = results_df[['Image', 'Title', 'ASIN']]  # Arrange columns as required
                
                st.markdown(results_df.to_html(escape=False, index=False), unsafe_allow_html=True)
                
                # Prepare DataFrame for download (without Image URL)
                download_df = results_df[['Title', 'ASIN']].copy()
                download_df['URL'] = [result['URL'] for result in st.session_state.results]
                excel_buffer = BytesIO()
                download_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_buffer.seek(0)

                # Download button for the Excel file
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


if __name__ == "__main__":
    main()