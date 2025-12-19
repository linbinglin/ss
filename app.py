import streamlit as st
import requests
import json

st.set_page_config(page_title="漫剧全流程分镜工具", layout="wide")

# 标题与样式
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTextArea textarea { font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 漫剧全流程 AI 分镜生成器")
st.info("适配：Midjourney (图片) + 即梦AI (视频) | 比例 9:16 | 5秒短视频逻辑")

# 侧边栏：API 设置
st.sidebar.header("⚙️ API 配置")
api_url = st.sidebar.text_input("API 地址", value="https://blog.tuiwen.xyz/v1/chat/completions")
api_key = st.sidebar.text_input("API Key", type="password")
model_id = st.sidebar.text_input("Model ID", value="gpt-4o") # 建议使用长文本理解强的模型

# 主界面
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📋 输入区")
    char_desc = st.text_area("1. 人物角色描述 (必填)", 
        placeholder="例如：\n赵清月：清冷美人，银丝蝴蝶簪，白色绫罗纱衣...\n赵尘：冷峻王爷，玄色长袍...", height=200)
    
    uploaded_file = st.file_uploader("2. 上传故事原文 (.txt)", type=['txt'])
    raw_text = ""
    if uploaded_file:
        raw_text = uploaded_file.read().decode("utf-8")
    
    script_text = st.text_area("原文预览/编辑", value=raw_text, height=300)

# 处理逻辑
def generate_storyboard():
    if not api_key or not script_text or not char_desc:
        st.error("请填完所有必要信息（API Key、人物描述、原文）")
        return

    with st.spinner("正在进行多维度分析：计算字数、分配场景、调用角色信息..."):
        system_prompt = f"""你是一个顶级的漫剧导演和分镜师。你需要将小说文案转化为适合9:16比例生成的详细分镜。

### 核心约束：
1. **时间对齐（极其重要）**：文案配音约35个字符对应5秒视频。如果一段文案超过30-35个字符，必须拆分为多个分镜。
2. **人物一致性**：必须严格、完整地调用下方提供的【人物角色描述】，不能有任何缺失。
3. **动静分离**：
   - 【画面描述】：专供Midjourney。仅描述场景、人物外观、着装、光影、构图（9:16比例）。**禁止出现动作词。**
   - 【视频生成】：专供即梦AI。描述镜头语言（推拉摇移）、人物动作、神态变化、情感流动。
4. **场景逻辑**：确保相邻分镜场景衔接自然，不产生割裂感。
5. **完整性**：输出必须包含原文的每一个字，严禁修改原文。

### 人物角色描述字典：
{char_desc}

### 输出格式：
[分镜序号]
原文内容：[对应的原文内容]
画面描述：[9:16比例，场景背景 + 人物外观描述 + 视角/景别]
视频生成：[动作描述 + 神态变化 + 镜头运动语言]
---
"""

        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请处理以下文案：\n{script_text}"}
                ],
                "temperature": 0.2
            }
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"发生错误: {str(e)}"

# 生成按钮
if st.button("✨ 生成漫剧全流程分镜"):
    result = generate_storyboard()
    st.session_state['result'] = result

with col_right:
    st.subheader("🖼️ 生成结果")
    if 'result' in st.session_state:
        st.text_area("分镜详情", value=st.session_state['result'], height=600)
        st.download_button("💾 下载分镜结果", st.session_state['result'], file_name="storyboard_final.txt")
