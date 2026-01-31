import streamlit as st
from openai import OpenAI
import os

# --- 页面基础配置 ---
st.set_page_config(
    page_title="AI 深度文案分镜师 (逻辑增强版)",
    page_icon="🎬",
    layout="wide"
)

# --- 自定义 CSS (优化阅读体验) ---
st.markdown("""
<style>
    .stTextArea textarea {
        font-size: 14px !important;
        line-height: 1.5 !important;
    }
    .main-header {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏配置 ---
st.sidebar.title("⚙️ 参数设置")

# 1. API 配置
api_key = st.sidebar.text_input("请输入 API Key (云雾AI)", type="password", help="必须填写 yunwu.ai 的 API 密钥")
base_url = "https://yunwu.ai/v1"

# 2. 模型选择 (覆盖主流强逻辑模型)
model_options = [
    "gpt-4o",  # 首选，逻辑最强
    "claude-3-5-sonnet-20240620", # 文学性强，适合小说推文
    "deepseek-chat",  # 性价比高
    "gemini-1.5-pro-latest",
    "gpt-4o-mini"
]
selected_model = st.sidebar.selectbox("选择 AI 模型", model_options, index=0)
custom_model = st.sidebar.text_input("自定义模型ID (可选)", "")

# 最终使用的模型
final_model = custom_model if custom_model else selected_model

st.sidebar.markdown("---")
st.sidebar.info(f"🔗 接口地址: {base_url}\n\n🤖 当前模型: {final_model}")
st.sidebar.warning("💡 提示：为了达到图2的逻辑效果，建议使用 GPT-4o 或 Claude-3.5，它们的语义理解能力最强。")

# --- 主界面 ---
st.title("🎬 AI 深度文案分镜生成器 (逻辑增强版)")
st.markdown("""
> **核心功能**：本工具专门解决“分镜太碎”、“逻辑混乱”的问题。
> 它会将上传的文本打散，重新根据**画面完整性**进行聚合，生成逻辑清晰的推文分镜。
""")

uploaded_file = st.file_uploader("请上传文案 (.txt)", type=['txt'])

if uploaded_file is not None:
    # 1. 读取文件
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
                # 2. 核心预处理：彻底去格式化，变成“一坨”纯文本
                # 这一步是为了防止AI偷懒直接按原文的换行来分镜
                clean_text = original_text.replace("\n", "").replace("\r", "").replace("　", "").replace(" ", "")
                
                # 3. 核心 Prompt (提示词工程) - 这是实现“图2”效果的关键
                system_prompt = f"""
你是一位拥有10年经验的短视频分镜导演。你的任务是将一段“无格式的纯文本”重构为一份逻辑严密、画面感强的分镜脚本。

【核心原则 - 绝对禁止项】
1. **禁止删减**：原文的每一个字都必须保留，不能少一个字。
2. **禁止瞎编**：严禁添加原文没有的形容词或剧情。
3. **禁止太碎**：严禁把一句话（如“8岁那年家里穷”）单独切成一行，必须结合上下文组成完整画面。

【分镜划分逻辑 - 模仿图2风格】
你需要先在脑海中对文本进行语义断句，然后按照以下标准分段（每段即一个镜头）：

1. **整合背景**：将时间、地点、背景状态的描述合并在一起。
   * 错误示例：1.8岁那年 2.家里穷
   * 正确示例：1.8岁那年家里穷得揭不开锅了，怀孕的母亲带着我在寺外乞讨。
   
2. **整合动作与结果**：将一个动作及其直接结果，或连续的一组动作放在同一个分镜。
   * 正确示例：2.我把僧人端来的粥饭全给了母亲，施粥的将军府老妇人让人领我过来问。

3. **对话独立**：重要的对话通常需要独立成一个分镜，以便给观众展示说话人的神态。
   * 正确示例：3.“都饿成人干了，怎么不吃？”

4. **动作与神态**：如果是对话前的神态描写，可以单独成镜，或者与小声回应结合。
   * 正确示例：4.我局促地拽着自己残破的衣角，低头小声回她。

【输出格式】
请直接输出分镜列表，格式为“数字序号. 内容”，不要包含任何其他废话。

待处理文本如下：
"""
                
                status_box = st.status("正在进行深度语义分析...", expanded=True)
                result_placeholder = st.empty()
                full_response = ""

                try:
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    
                    status_box.write(f"正在调用 {final_model} 进行逻辑重组...")
                    
                    stream = client.chat.completions.create(
                        model=final_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": clean_text}
                        ],
                        stream=True,
                        temperature=0.6, # 降低随机性，提高逻辑稳定性
                        max_tokens=4000
                    )
                    
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            result_placeholder.markdown(full_response)
                            
                    status_box.update(label="✅ 分镜重构完成", state="complete", expanded=False)
                    
                    # 提供下载
                    st.download_button(
                        label="📥 下载整理好的分镜 (.txt)",
                        data=full_response,
                        file_name="逻辑分镜脚本.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    status_box.update(label="❌ 发生错误", state="error")
                    st.error(f"错误信息: {str(e)}")
