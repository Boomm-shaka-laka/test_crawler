import streamlit as st
import re
import logging
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from seleniumwire import webdriver  # 使用 selenium-wire 拦截请求
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

# ==========================================
# 1. 辅助函数 (保持 Markdown 转换逻辑)
# ==========================================
def table_to_markdown(headers, rows):
    if not headers and not rows: return ""
    def esc(x): return str(x).replace("|", "\\|").replace("\n", " ").strip()
    header = "| " + " | ".join(esc(h) for h in headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows]
    return "\n".join([header, sep] + body)

def get_driver():
    """配置并返回 Selenium 驱动"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 重点：Selenium-wire 拦截配置
    wire_options = {
        'ignore_http_methods': ['OPTIONS'],
        # 拦截图片、样式和字体以提高速度
        'request_storage_base_dir': '/tmp/seleniumwire' 
    }
    
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options, seleniumwire_options=wire_options)
    
    # 定义拦截规则 (模拟 Playwright 的 route)
    def interceptor(request):
        if request.path.endswith(('.png', '.jpg', '.gif', '.css', '.woff', '.woff2')):
            request.abort()
            
    driver.request_interceptor = interceptor
    return driver

# ==========================================
# 2. 爬虫任务逻辑
# ==========================================
def scrape_list():
    driver = get_driver()
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 20)
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
                items.append({"href": href, "title": title, "public_time": time})
            except: continue
        return items
    finally:
        driver.quit()

def scrape_detail_worker(item):
    """单个详情页抓取工人"""
    driver = get_driver()
    try:
        driver.get(item["href"])
        
        # 提取来源和时间
        try:
            info_text = driver.find_element(By.XPATH, '//*[@id="right"]/div[1]').text
            source = re.search(r'来源[：:]\s*([^|]+)', info_text)
            item["source"] = source.group(1).strip() if source else ""
        except:
            item["source"] = ""

        # 解析正文为 Markdown (执行 JS 逻辑)
        item["summary"] = driver.execute_script("""
            const zoom = document.getElementById('zoom');
            if (!zoom) return "";
            let res = "";
            function walk(node){
                if(node.nodeType === 3){
                    const t = node.textContent.trim();
                    if(t) res += t + "\\n";
                } else if(node.nodeType === 1){
                    if(node.tagName === 'TABLE'){
                        res += "\\n[表格内容已略]\\n"; // 简单处理，或复用你原有的表格 JS 逻辑
                    } else {
                        node.childNodes.forEach(walk);
                    }
                }
            }
            walk(zoom);
            return res;
        """)
    except Exception as e:
        logger.error(f"详情页抓取失败: {e}")
    finally:
        driver.quit()
    return item

# ==========================================
# 3. Streamlit UI
# ==========================================
st.title("🕷️ 宁波国资委公告爬虫 (Selenium 多线程版)")

if st.button("🚀 开始爬取", type="primary"):
    with st.status("正在抓取数据...", expanded=True) as status:
        # 1. 抓取列表
        status.write("正在获取列表页...")
        list_items = scrape_list()
        
        # 2. 并发抓取详情 (模拟 Playwright 的并发)
        status.write(f"正在并发抓取 {len(list_items)} 条详情 (使用线程池)...")
        with ThreadPoolExecutor(max_workers=3) as executor:
            final_results = list(executor.map(scrape_detail_worker, list_items))
        
        status.update(label="爬取完成！", state="complete")
        
        if final_results:
            df = pd.DataFrame(final_results)
            st.dataframe(df[['title', 'public_time', 'source', 'href']], use_container_width=True)
            with st.expander("查看首条正文"):
                st.markdown(final_results[0].get("summary", "无内容"))