import streamlit as st
import os

# --- 必须放在最前面：重定向驱动存放路径到可写的 /tmp 目录 ---
os.environ["SELENIUMBASE_DRIVERS_PATH"] = "/tmp/seleniumbase_drivers"

from seleniumbase import Driver

st.title("🌐 Streamlit Cloud 爬虫方案")

url = st.text_input("输入网址:", "https://www.google.com")

if st.button("开始爬取"):
    # 每次运行时检查驱动是否存在，不存在则下载到 /tmp
    # 这是解决 Permission denied 的核心步骤
    if not os.path.exists("/tmp/seleniumbase_drivers/chromedriver"):
        with st.spinner("首次运行，正在环境部署..."):
            os.system('sbase install chromedriver /tmp/seleniumbase_drivers')

    with st.spinner("正在抓取内容..."):
        try:
            # 初始化驱动：不需要传路径参数，它会自动读取环境变量
            driver = Driver(browser="chrome", headless=True, uc=True)
            
            driver.get(url)
            title = driver.get_title()
            
            st.success(f"抓取成功！页面标题为: {title}")
            driver.quit()
            
        except Exception as e:
            st.error(f"运行出错: {e}")