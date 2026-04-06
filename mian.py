import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # ✅ 关键：伪装 User-Agent，防止被政府网站防火墙拦截
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    options.add_argument(f'user-agent={ua}')
    
    # 禁用图片加载提高速度
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    # 指向 Streamlit Cloud 预装的驱动
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

st.title("🏛️ 宁波国资委列表抓取测试")

TARGET_URL = "https://gzw.ningbo.gov.cn/col/col1229116730/"
# 你提供的精确 XPath
TARGET_XPATH = '//*[@id="jw_sgzw_二级栏目列表_标题list"]/div/div/ul'

if st.button("🔍 开始定位并抓取"):
    with st.spinner("正在打开页面..."):
        driver = get_driver()
        try:
            driver.get(TARGET_URL)
            
            # 增加显式等待，最长等待 20 秒
            wait = WebDriverWait(driver, 20)
            
            st.write("⏳ 正在等待元素加载...")
            # 定位到 ul 容器
            ul_element = wait.until(
                EC.presence_of_element_located((By.XPATH, TARGET_XPATH))
            )
            
            # 获取该 ul 下所有的 li
            lis = ul_element.find_elements(By.TAG_NAME, "li")
            
            if lis:
                st.success(f"✅ 成功找到 {len(lis)} 条记录！")
                
                # 提取文本并显示
                results = [li.text.strip() for li in lis if li.text.strip()]
                
                for index, text in enumerate(results):
                    st.write(f"**{index + 1}.** {text}")
            else:
                st.warning("找到了容器，但里面没有 li 元素。")
                
        except Exception as e:
            st.error(f"❌ 抓取失败!")
            st.code(str(e))
            # 调试：抓取当前页面源码片段，看看是不是被防火墙挡了
            if "driver" in locals():
                st.write("页面源码片段 (用于排查):")
                st.text(driver.page_source[:500])
        finally:
            if "driver" in locals():
                driver.quit()
