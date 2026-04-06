import streamlit as st
import platform
import os
import sys

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="宁波市政府采购网爬虫",
    page_icon="🕷️",
    layout="wide",
)

TARGET_URL   = "https://gzw.ningbo.gov.cn/col/col1229116730/"
TARGET_XPATH = '//*[@id="jw_sgzw_二级栏目列表_标题list"]//ul'

# ── Environment detection ─────────────────────────────────────────────────────
def is_streamlit_cloud() -> bool:
    """Detect Streamlit Cloud by checking for the STREAMLIT_SHARING env var
    or the absence of a display / typical cloud signals."""
    return (
        os.environ.get("STREAMLIT_SHARING_MODE") == "true"
        or os.environ.get("HOME", "") == "/home/appuser"  # Cloud default home
        or not os.environ.get("DISPLAY", "")              # No display server
        and platform.system() == "Linux"
        and "microsoft" not in platform.release().lower()  # not WSL
    )

def is_wsl() -> bool:
    return "microsoft" in platform.release().lower() or \
           "WSL" in os.environ.get("WSL_DISTRO_NAME", "")

# ── Core scraper ─────────────────────────────────────────────────────────────
def scrape(headless: bool = True) -> list[str]:
    """
    Run the SeleniumBase scraper and return a list of text items.
    Works in headed WSL2 (headless=False) or cloud/CI (headless=True).
    Uses Firefox (via geckodriver) — lighter than Chrome.
    """
    from seleniumbase import Driver

    driver = Driver(
        browser="firefox",
        headless=headless,       # True = cloud / CI / WSL without display
        # Note: undetectable & no_sandbox are Chrome-only options;
        # Firefox doesn't need them and ignores them gracefully.
    )

    texts: list[str] = []
    try:
        driver.get(TARGET_URL)
        driver.implicitly_wait(10)

        # Wait until the target element is visible
        driver.wait_for_element_visible(TARGET_XPATH, by="xpath", timeout=20)

        ul_element = driver.find_element(TARGET_XPATH, by="xpath")
        li_elements = ul_element.find_elements("tag name", "li")

        for li in li_elements:
            raw = li.text.strip()
            if raw:
                texts.append(raw)

        # Fallback: if no <li> found, grab the whole ul text
        if not texts:
            raw = ul_element.text.strip()
            texts = [line for line in raw.splitlines() if line.strip()]

    finally:
        driver.quit()

    return texts


# ── Streamlit UI ──────────────────────────────────────────────────────────────
st.title("🕷️ 宁波市政府采购网 · 栏目列表爬虫")
st.caption(f"目标页面：{TARGET_URL}")

# Environment info badge
env_label = "☁️ Streamlit Cloud" if is_streamlit_cloud() else ("🐧 WSL2" if is_wsl() else "💻 本地 Linux/Mac/Win")
st.info(f"当前运行环境：**{env_label}**　｜　Python {sys.version.split()[0]}　｜　{platform.system()} {platform.release()[:40]}")

with st.expander("⚙️ 运行设置", expanded=False):
    headless = st.toggle(
        "无头模式 (Headless)",
        value=True,
        help="云端/WSL无显示器时必须开启；本地有桌面时可关闭以观察浏览器行为",
    )

st.divider()

if st.button("🚀 开始爬取", type="primary", use_container_width=True):
    with st.spinner("正在启动 Firefox，加载页面，请稍候…"):
        try:
            results = scrape(headless=headless)
        except Exception as exc:
            st.error(f"❌ 爬取失败：{exc}")
            st.exception(exc)
            st.stop()

    if not results:
        st.warning("⚠️ 未找到任何列表项，请检查 XPath 或目标页面是否变更。")
    else:
        st.success(f"✅ 共获取到 **{len(results)}** 条数据")
        st.divider()

        # ── Print to terminal (as requested) ──────────────────────────────
        print("\n" + "=" * 60)
        print(f"[爬取结果]  共 {len(results)} 条  ·  来源: {TARGET_URL}")
        print("=" * 60)
        for i, item in enumerate(results, 1):
            print(f"{i:>3}. {item}")
        print("=" * 60 + "\n")

        # ── Display in UI ──────────────────────────────────────────────────
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📋 列表内容")
            for i, item in enumerate(results, 1):
                st.markdown(f"`{i:>2}` {item}")

        with col2:
            st.subheader("📄 纯文本导出")
            plain = "\n".join(f"{i}. {t}" for i, t in enumerate(results, 1))
            st.download_button(
                label="⬇️ 下载 .txt",
                data=plain,
                file_name="ningbo_gzw_list.txt",
                mime="text/plain",
            )
            st.code(plain, language=None)