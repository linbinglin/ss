import streamlit as st
from openai import OpenAI
import os

# --- 页面基础配置 ---
st.set_page_config(
    page_title="AI 智能分镜 (语感修复版)",
    page_icon="🎬",
    layout="wide"
)

# --- CSS样式 ---
st.markdown("""
<style>
    .stTextArea textarea { font-size: 14px !important; line-height: 1.6 !important; }
    div[data-testid="stStatusWidget"] { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏配置 ---
st.sidebar.title("⚙️ 设置")
api_key = st.sidebar.text_input("请输入 API Key", type="password")
base_url = "https://yunwu.ai/v1"

# 推荐模型 (GPT-4o 对标点和语感的修复能力最强)
model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "gpt-4o-mini"]
selected_model = st.sidebar.selectbox("选择模型", model_options, index=0)
custom_model = st.sidebar.text_input("自定义模型ID (选填)", "")
final_model = custom_model if custom_model.strip() else selected_model

# --- 主界面 ---
st.title("🎬 AI 智能文案分镜 (语感修复版)")
st.info("💡 此版本已修复“语句粘连”和“无标点”的问题，会生成通顺、有呼吸感的分镜脚本。")

uploaded_file = st.file_uploader("上传文案 (.txt)", type=['txt'])

if uploaded_file is not None:
    original_text = uploaded_file.read().decode("utf-8")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 原文")
        st.text_area("Original", original_text, height=400, label_visibility="collapsed")

    with col2:
        st.subheader("🎞️ 分镜脚本")
        generate_btn = st.button("🚀 生成分镜", type="primary", use_container_width=True)

        if generate_btn:
            if not api_key:
                st.error("请填写 API Key")
            else:
                # 1. 清洗文本：用空格代替换行，防止字粘连太死
                clean_text = original_text.replace("\n", " ").replace("\r", " ").replace("　", " ")
                
                # 2. 核心 Prompt (针对你遇到的问题进行了修复)
                system_prompt = f"""
你是一位顶级短视频分镜师。请将用户提供的文本重构为标准分镜脚本。

【核心任务】
用户提供的文本已经被去除了格式，可能缺乏标点。
你必须**先修复语句通顺度，补全标点符号**，然后按照画面逻辑进行分段。

【严格遵守以下规则】
1. **标点修复（至关重要）**：
   - 严禁输出像“8岁那年家里穷得揭不开锅了怀孕的母亲...”这样没有标点的长句。
   - 必须输出为：“8岁那年家里穷得揭不开锅了，怀孕的母亲带着我在寺外乞讨。”（加上逗号和句号）。

2. **分镜逻辑（参考图2风格）**：
   - **合并原则**：将“背景环境”+“人物状态”合并为一镜。
   - **动作原则**：将“动作”+“动作结果”合并为一镜。
   - **对话原则**：重要对话单独成行。

3. **禁止项**：
   - 禁止遗漏原文任何信息。
   - 禁止添加原文没有的内容。
   - **禁止使用方括号 []**，直接输出文字。

【输出格式示例】
1. 8岁那年家里穷得揭不开锅了，怀孕的母亲带着我在寺外乞讨。
2. 我把僧人端来的粥饭全给了母亲，施粥的将军府老妇人让人领我过来问。
3. “都饿成人干了，怎么不吃？”
4. 我局促地拽着自己残破的衣角，低头小声回她。

请处理以下内容：
"""
                
                result_placeholder = st.empty()
                full_response = ""
                
                try:
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    stream = client.chat.completions.create(
                        model=final_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": clean_text}
                        ],
                        stream=True,
                        temperature=0.5, # 降低随机性，保证标点准确
                    )
                    
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            result_placeholder.markdown(full_response)
                            
                    st.download_button("📥 下载脚本", full_response, "分镜脚本.txt")

                except Exception as e:
                    st.error(f"出错: {e}")
