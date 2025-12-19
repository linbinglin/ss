import streamlit as st
import requests

st.set_page_config(page_title="漫剧全流程AI分镜助手", layout="wide")

st.title("🎨 漫剧全流程AI分镜助手 (MJ + 即梦专用)")

# --- 侧边栏配置 ---
with st.sidebar:
    st.header("1. API 配置")
    provider = st.selectbox("选择模型", ["DeepSeek-V3", "GPT-4o", "Claude-3.5-Sonnet"])
    api_key = st.text_input("API Key", type="password")
    
    st.header("2. 人物设定 (必填)")
    char_ref = st.text_area("粘贴人物描述文本...", height=200, placeholder="例如：安妙衣（女主）：（描述...）")

# --- 主界面 ---
col1, col2 = st.columns(2)

with col1:
    st.header("3. 剧情文本上传")
    uploaded_script = st.file_uploader("上传分镜.txt", type=["txt"])
    
with col2:
    st.header("使用说明")
    st.info("""
    - **逻辑说明**：AI会自动按35字/动作切分。
    - **一致性**：会自动将侧边栏的人物设定填入每个分镜。
    - **输出**：直接复制结果到MJ生成图片，再将图片与视频描述填入即梦。
    """)

if st.button("🚀 生成全量分镜脚本"):
    if not (api_key and char_ref and uploaded_script):
        st.warning("请补全 API Key、人物设定和剧情文件。")
    else:
        script_content = uploaded_script.read().decode("utf-8")
        
        # 构造提示词
        full_prompt = f"""
        人物设定如下：
        {char_ref}

        待处理剧情文本：
        {script_content}

        请按照我要求的格式进行分镜处理：
        1. 确保每段文案 < 35字，不漏字。
        2. 画面描述要包含场景和人物固定装束。
        3. 视频生成要包含镜头语言和动态动作。
        """

        with st.spinner("导演正在构思每一帧画面..."):
            try:
                # 此处以 DeepSeek/OpenAI 通用格式为例
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                base_url = "https://api.deepseek.com/v1/chat/completions" # 根据实际API修改
                
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "你是一位专业的漫剧导演，擅长将文字转化为视觉语言。"},
                        {"role": "user", "content": full_prompt}
                    ],
                    "temperature": 0.3
                }
                
                response = requests.post(base_url, headers=headers, json=payload)
                result = response.json()['choices'][0]['message']['content']
                
                st.subheader("✅ 生成分镜预览")
                st.text_area("全量脚本", value=result, height=800)
                
                st.download_button("下载完整分镜脚本", result, file_name="final_storyboard.txt")
                
            except Exception as e:
                st.error(f"处理失败: {e}")
