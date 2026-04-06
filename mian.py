import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

st.title("🌐 Streamlit Cloud 终极爬虫方案")

url = st.text_input("输入网址:", "https://www.google.com")

if st.button("开始爬取"):
    with st.spinner("正在启动系统级浏览器..."):
        try:
            # 1. 配置无头模式和防崩溃参数（云端必备）
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            # 2. 核心操作：直接使用 packages.txt 安装的系统级驱动
            service = Service("/usr/bin/chromedriver")
            
            # 3. 启动浏览器
            driver = webdriver.Chrome(service=service, options=options)
            
            # 4. 执行爬虫逻辑
            driver.get(url)
            title = driver.title
            
            st.success("抓取成功！")
            st.metric("页面标题", title)
            
        except Exception as e:
            st.error(f"运行出错: {e}")
            
        finally:
            # 确保无论成功失败，都关闭浏览器释放内存
            if 'driver' in locals():
                driver.quit()