import streamlit as st
import requests
import json

# 设置页面
st.set_page_config(page_title="漫剧全流程分镜处理工具", layout="wide")

# 自定义 CSS 样式
st.markdown("""
    <style>
    .stTextArea textarea { font-family: 'Courier New', Courier, monospace; }
    .reportview-container { background: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 漫剧文案分镜处理工具 (V2.0)")
st.caption("基于原文切分 | 35字/5秒规则 | 角色外观注入 | MJ+即梦提示词")

# --- 侧边栏配置 ---
st.sidebar.header("⚙️ API 与模型配置")
target_url = st.sidebar.text_input("API 接口地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
api_key = st.sidebar.text_input("API Key", type="password")

# 模型选项
model_list = ["deepseek-chat", "gpt-4o", "claude-3-5-sonnet-20240620", "gemini-1.5-pro", "grok-1", "doubao-pro-4k", "自定义"]
model_choice = st.sidebar.selectbox("选择 AI 模型", model_list)
if model_choice == "自定义":
    model_id = st.sidebar.text_input("请输入模型 ID (Model ID)")
else:
    model_id = model_choice

# --- 主界面 ---
col_in, col_out = st.columns([1, 1])

with col_in:
    st.subheader("📥 输入区域")
    # 角色描述注入
    char_profile = st.text_area("1. 人物角色描述字典 (必填，用于保持一致性)", 
        placeholder="例如：\n赵尘：玄色长袍，冷峻面孔，腰间佩玉...\n安妙衣：白色辫子绫罗纱衣，清冷，银丝蝴蝶簪...", height=150)
    
    # 文件上传
    uploaded_file = st.file_uploader("2. 上传原文文本 (.txt)", type=['txt'])
    raw_text = ""
    if uploaded_file:
        raw_text = uploaded_file.read().decode("utf-8")
    
    script_input = st.text_area("3. 故事原文 (可手动输入或修改)", value=raw_text, height=350)

# --- 核心 Prompt 构造 ---
system_prompt = f"""你是一个专业漫剧分镜师。你需要将文案拆解为适合 9:16 视频创作的分镜。

### 强制执行规则：
1. **分镜切分逻辑**：
   - 只要出现【角色对话切换】、【场景切换】、【动作改变】，必须切分为下一个分镜。
   - **35字原则**：为了匹配5秒视频，若一段内容超过35个字符，必须强制拆分为多个分镜。
2. **文本完整性**：
   - 严禁遗漏原文中的任何一个字！
   - 严禁修改原文、严禁添加评论。
   - 必须按照序号(1. 2. 3.)顺序输出。
3. **角色一致性**：
   - 必须在每个涉及该角色的分镜中，完整调用【角色描述字典】中的外观和着装描述。
   - 字典：{char_profile}
4. **描述词生成 (动静分离)**：
   - 【画面描述】：用于 Midjourney 生成 9:16 图片。描述：场景、光影、人物外观着装、视角、景别。**禁止动作词**。
   - 【视频生成】：用于即梦AI生成视频。描述：人物动作、神态变化、镜头语言（推拉摇移）。

### 输出格式样例：
1.
原文内容：[此处必须是原文，不许漏字]
画面描述：[场景+人物外观+构图]
视频生成：[动作+神态+镜头语言]
---
"""

# --- 处理逻辑 ---
if st.button("🚀 开始自动化分镜与提示词生成"):
    if not api_key:
        st.warning("请在侧边栏填入 API Key")
    elif not script_input or not char_profile:
        st.warning("请输入原文内容和角色描述")
    else:
        with st.spinner("AI 正在深度推理、对齐时间轴并生成视觉描述..."):
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                payload = {
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"请对此文案进行处理：\n{script_input}"}
                    ],
                    "temperature": 0.1  # 极致的稳定性，防止AI乱改
                }
                
                response = requests.post(target_url, headers=headers, json=payload, timeout=180)
                response.raise_for_status()
                result_json = response.json()
                
                if 'choices' in result_json:
                    final_result = result_json['choices'][0]['message']['content']
                    st.session_state['final_result'] = final_result
                else:
                    st.error("接口返回格式异常，请检查 API 或中转站配置。")
            except Exception as e:
                st.error(f"处理失败: {str(e)}")

# --- 结果展示与下载 ---
with col_out:
    st.subheader("🖼️ 分镜结果预览")
    if 'final_result' in st.session_state:
        # 实时显示在文本框里
        st.text_area("分镜详情 (可直接复制)", value=st.session_state['final_result'], height=600)
        
        # 下载功能
        st.download_button(
            label="📥 下载分镜结果文件",
            data=st.session_state['final_result'],
            file_name="AI分镜提示词结果.txt",
            mime="text/plain"
        )
    else:
        st.info("生成后分镜内容将出现在此处")
