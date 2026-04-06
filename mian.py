import streamlit as st
from seleniumbase import Driver
import pandas as pd
import os
# 1. 强制设置环境变量，让 SeleniumBase 使用 /tmp 目录存放驱动
os.environ["SELENIUMBASE_DRIVERS_PATH"] = "/tmp/seleniumbase_drivers"
st.set_page_config(page_title="简易爬虫器", layout="centered")

st.title("🌐 SeleniumBase 爬虫演示")
st.write("输入网址，抓取页面标题。")

url = st.text_input("请输入网址:", "https://www.example.com")

if st.button("开始爬取"):
    with st.spinner("正在启动浏览器并抓取数据..."):
        try:
            # 2. 初始化驱动
            # 显式指定 driver_path 指向刚才设置的环境变量路径
            driver = Driver(
                browser="chrome", 
                headless=True, 
                uc=True,
                driver_path="/tmp/seleniumbase_drivers" 
            )
            
            driver.get(url)
            page_title = driver.get_title()
            current_url = driver.get_current_url()
            
            # 也可以抓取一些特定内容，比如所有的 h1 标签
            h1_elements = driver.find_elements("tag name", "h1")
            h1_texts = [el.text for el in h1_elements]
            
            driver.quit()

            # 显示结果
            st.success("抓取成功！")
            
            col1, col2 = st.columns(2)
            col1.metric("页面标题", page_title)
            col2.metric("实际 URL", current_url)

            if h1_texts:
                st.subheader("找到的 H1 标签:")
                st.write(h1_texts)
            else:
                st.info("未发现 H1 标签。")

        except Exception as e:
            st.error(f"发生错误: {e}")