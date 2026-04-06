import streamlit as st
import re
import logging
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# 0. 基础配置
# ==========================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://gzw.ningbo.gov.cn"
TARGET_URL = f"{BASE_URL}/col/col1229116730/"
LIST_XPATH = '/html/body/div/div[3]/div/div/div[2]/div/div/div/ul'

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # ✅ 必须添加伪装的 User-Agent
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={ua}')
    
    # 禁用图片提升速度
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# ==========================================
# 1. 爬虫核心逻辑 (同步多线程版)
# ==========================================
def scrape_list():
    driver = get_driver()
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.XPATH, LIST_XPATH)))
        
        items = []
        lis = driver.find_elements(By.XPATH, f"{LIST_XPATH}/li")
        for li in lis:
            try:
                a = li.find_element(By.TAG_NAME, "a")
                p = li.find_element(By.TAG_NAME, "p")
                href = a.get_attribute("href")
                title = a.text.strip()
                time = p.text.strip()
                if href.startswith("/"): href = BASE_URL + href
                items.append({"href": href, "title": title, "public_time": time})
            except: continue
        return items
    finally:
        driver.quit()

def scrape_detail_worker(item):
    driver = get_driver()
    try:
        driver.get(item["href"])
        # 复用你原本的 JS 解析逻辑
        item["summary"] = driver.execute_script("""
            const zoom = document.getElementById('zoom');
            if (!zoom) return "";
            let text = zoom.innerText || zoom.textContent;
            return text.trim();
        """)
        # 提取来源
        try:
            info_text = driver.find_element(By.XPATH, '//*[@id="right"]/div[1]').text
            source_match = re.search(r'来源[：:]\s*([^|]+)', info_text)
            item["source"] = source_match.group(1).strip() if source_match else ""
        except:
            item["source"] = "未知"
    except Exception as e:
        logger.error(f"详情页失败: {item['href']} | {e}")
        item["summary"] = "抓取失败"
    finally:
        driver.quit()
    return item

# ==========================================
# 2. Streamlit 界面
# ==========================================
st.set_page_config(page_title="Selenium 爬虫测试", layout="wide")
st.title("🕷️ 宁波国资委公告 (Selenium 多线程优化版)")

if st.button("🚀 开始爬取", type="primary"):
    with st.status("正在抓取...", expanded=True) as status:
        status.write("正在解析列表页...")
        list_items = scrape_list()
        
        if list_items:
            status.write(f"发现 {len(list_items)} 条公告，正在并发解析详情...")
            # Streamlit Cloud 内存小，建议 max_workers 设为 2 或 3
            with ThreadPoolExecutor(max_workers=2) as executor:
                final_results = list(executor.map(scrape_detail_worker, list_items))
            
            status.update(label="抓取完成！", state="complete")
            df = pd.DataFrame(final_results)
            st.dataframe(df[['title', 'public_time', 'source', 'href']], use_container_width=True)
            
            with st.expander("查看第一条公告正文"):
                st.write(final_results[0].get("summary", "无内容"))
        else:
            status.update(label="未能获取列表", state="error")
