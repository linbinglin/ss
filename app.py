import streamlit as st
from openai import OpenAI
import io

# --- 页面设置 ---
st.set_page_config(page_title="漫剧AI智能分镜系统", layout="wide")

st.title("🎬 漫剧AI智能分镜与提示词生成系统")
st.markdown("""
本系统支持：自动分镜、35字限制分割、人物一致性提示词生成、MJ+即梦AI描述词导出。
""")

# --- 侧边栏配置 ---
st.sidebar.header("⚙️ API 配置")
api_url = st.sidebar.text_input("接口地址", value="https://blog.tuiwen.xyz/v1")
api_key = st.sidebar.text_input("API Key", type="password")
model_options = ["deepseek-chat", "gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro", "grok-1", "doubao-pro-128k"]
model_id = st.sidebar.selectbox("选择模型名称", model_options)

# --- 主界面输入 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. 导入文案与角色")
    uploaded_file = st.file_uploader("上传文案文本 (.txt)", type="txt")
    character_desc = st.text_area("人物外观描述 (重要：用于人物一致性)", 
                                  placeholder="例如：\n安妙衣：瘦弱女子，病态白皙，眉心一点红，凌乱的青丝，素色破旧棉袍。\n赵尘：冷酷王爷，束发金冠，黑色锦袍，腰佩金刀。",
                                  height=200)

with col2:
    st.header("2. 设定与操作")
    ratio = st.selectbox("视频比例", ["9:16 (竖屏漫剧)", "16:9 (横屏)", "1:1"])
    process_btn = st.button("🚀 开始分析并生成分镜提示词", use_container_width=True)

# --- 核心处理逻辑 ---
if process_btn:
    if not api_key or not uploaded_file:
        st.error("请先输入 API Key 并上传文案文件。")
    else:
        # 读取文件内容
        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        raw_script = stringio.read()

        # 初始化 OpenAI 客户端
        client = OpenAI(api_key=api_key, base_url=api_url)

        # 构造 System Prompt (你的核心大脑)
        system_prompt = f"""
        你是一个顶级的漫剧导演和AI提示词专家。
        任务：对用户提供的文案进行[二次深度分镜]并生成[AI绘画和视频提示词]。

        ### 严格执行规则：
        1. **35字分割原则**：为了匹配5秒视频，每个分镜的文案严禁超过35个字。若原分镜内容过长，必须在不改变原意的情况下拆分为多个子分镜。
        2. **原文完整性**：禁止修改、遗漏原文中的任何一个字。
        3. **格式要求**：
           ---
           **[分镜编号]**
           **文案内容**：(原文，不可修改)
           **画面描述**：(用于Midjourney生成图片。包含：场景、环境细节、人物完整外观设定、构图视角、光影效果。注意：不要描述动作。)
           **视频生成**：(用于即梦AI生成视频。包含：角色具体的动作轨迹、镜头语言、表情微动、5秒内的动态变化。)
           ---

        ### 角色一致性要求：
        在每一组“画面描述”中，必须完整调用以下人物外观设定，严禁简化：
        {character_desc}

        ### 比例要求：
        画面比例设定为 {ratio}。
        """

        try:
            with st.spinner("AI 正在深度解析剧情并生成提示词，请稍候..."):
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"请对以下文案进行处理：\n\n{raw_script}"}
                    ],
                    temperature=0.7
                )
                
                result = response.choices[0].message.content
                
                st.header("✅ 生成结果")
                st.markdown(result)
                
                # 提供下载选项
                st.download_button("下载分镜脚本", result, file_name="storyboard_output.txt")
                
        except Exception as e:
            st.error(f"处理失败: {str(e)}")

# --- 底部页脚 ---
st.markdown("---")
st.caption("提示：请确保你的中转接口支持你选择的模型 ID。")
