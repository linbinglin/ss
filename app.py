import streamlit as st
from openai import OpenAI
import os

# --- 页面基础配置 ---
st.set_page_config(
    page_title="AI 深度文案分镜师 (修复版)",
    page_icon="🎬",
    layout="wide"
)

# --- CSS样式 ---
st.markdown("""
<style>
    .stTextArea textarea { font-size: 14px !important; line-height: 1.5 !important; }
    .main-header { font-size: 24px; font-weight: bold; color: #333; }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏配置 ---
st.sidebar.title("⚙️ 参数设置")

api_key = st.sidebar.text_input("请输入 API Key (云雾AI)", type="password", help="必须填写 yunwu.ai 的 API 密钥")
base_url = "https://yunwu.ai/v1"

# 常见正确模型列表
model_options = [
    "gpt-4o",                # 推荐：逻辑最强
    "claude-3-5-sonnet-20240620", # 推荐：文采好
    "gemini-1.5-pro-latest", # Google 模型
    "deepseek-chat",         # 性价比
    "gpt-4o-mini"
]
selected_model = st.sidebar.selectbox("选择 AI 模型", model_options, index=0)
custom_model = st.sidebar.text_input("自定义模型ID (不确定请留空)", "", help="注意：如果填错ID会导致生成空白！")

# 优先使用自定义模型
final_model = custom_model if custom_model.strip() else selected_model

st.sidebar.markdown("---")
st.sidebar.info(f"🔗 接口: {base_url}\n\n🤖 模型: {final_model}")

# --- 主界面 ---
st.title("🎬 AI 深度文案分镜生成器 (防空修复版)")
st.warning("⚠️ 注意：如果生成结果为空，请清空侧边栏的【自定义模型ID】，直接使用下拉菜单中的 GPT-4o 测试。")

uploaded_file = st.file_uploader("请上传文案 (.txt)", type=['txt'])

if uploaded_file is not None:
    original_text = uploaded_file.read().decode("utf-8")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 原文内容")
        st.text_area("原始文本", original_text, height=400, disabled=True)

    with col2:
        st.subheader("🎞️ 分镜生成区")
        generate_btn = st.button("🚀 开始重构分镜", type="primary", use_container_width=True)

        if generate_btn:
            if not api_key:
                st.error("请在侧边栏填写 API Key！")
            else:
                # 1. 清洗文本
                clean_text = original_text.replace("\n", "").replace("\r", "").replace("　", "").replace(" ", "")
                
                # 2. 提示词
                system_prompt = f"""
你是一位短视频分镜导演。请将这段纯文本重构为分镜脚本。
【原则】：
1. 严禁删减原文任何一个字。
2. 严禁把一句话切得太碎，必须根据画面完整性（背景+动作+心理）进行语义合段。
3. 严格模仿以下逻辑：
   - 将“背景描述”与“发生的动作”合并为一段。
   - 将“动作”与“动作带来的直接后果”合并为一段。
   - 对话独立成段。

【输出格式】：
纯数字列表，如：
1. [内容...]
2. [内容...]
"""
                
                result_placeholder = st.empty()
                status_box = st.status("正在连接 AI 模型...", expanded=True)
                full_response = ""
                has_content = False # 标记是否接收到了内容

                try:
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    
                    status_box.write(f"正在调用 {final_model}...")
                    
                    stream = client.chat.completions.create(
                        model=final_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": clean_text}
                        ],
                        stream=True,
                        temperature=0.6,
                    )
                    
                    # 3. 接收流
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            result_placeholder.markdown(full_response)
                            has_content = True # 只要收到了一个字，就标记为真
                    
                    # 4. 关键修正：检查是否为空
                    if not has_content:
                        status_box.update(label="❌ 生成失败：模型未返回任何内容", state="error")
                        st.error(f"错误：模型 {final_model} 返回了空内容。")
                        st.markdown("""
                        **排查建议：**
                        1. **模型名称错误**：你填写的 `{final_model}` 可能不存在。请清空自定义栏，使用 `gpt-4o` 试试。
                        2. **额度不足**：请检查云雾 AI 账户余额。
                        3. **文本过长**：如果文本极长，尝试删减一部分测试。
                        """)
                    else:
                        status_box.update(label="✅ 分镜重构完成", state="complete", expanded=False)
                        st.download_button(
                            label="📥 下载分镜脚本 (.txt)",
                            data=full_response,
                            file_name="分镜脚本.txt",
                            mime="text/plain"
                        )

                except Exception as e:
                    status_box.update(label="❌ 发生错误", state="error")
                    st.error(f"API 调用报错: {str(e)}")
                    st.info("提示：请检查 API Key 是否正确，或尝试更换模型。")
