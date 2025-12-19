import streamlit as st
from openai import OpenAI
import re

# 页面配置
st.set_page_config(page_title="AI 视频分镜全流程工具", layout="wide", page_icon="🎬")

# 侧边栏：API 配置
st.sidebar.title("⚙️ 配置中心")
api_key = st.sidebar.text_input("1. 输入 API Key", type="password")
base_url = st.sidebar.text_input("2. 接口地址", value="https://blog.tuiwen.xyz/v1")

st.sidebar.markdown("---")
st.sidebar.subheader("3. 模型设置")
model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义模型"]
selected_model = st.sidebar.selectbox("选择模型", model_options)
if selected_model == "自定义模型":
    model_id = st.sidebar.text_input("手动输入 Model ID", value="gpt-4o")
else:
    model_id = selected_model

# 系统提示词定义 (核心逻辑)
SYSTEM_PROMPT = """你是一个顶级的电影解说导演和视觉设计师。你的任务是将文案拆解为高度精准的【分镜脚本】+【Midjourney提示词】+【即梦AI视频提示词】。

### 核心执行逻辑：
1. **二次精确分镜**：
   - 严格遵守时长对齐：每行文案绝对严禁超过40个汉字（对应约5秒音频）。
   - 如果一句话太长，必须按语义拆分为多个连续分镜。
   - 每个分镜必须包含：剧情编号、原文文案、画面描述、视频生成。

2. **视觉一致性（重要）**：
   - 在每一个分镜的【画面描述】中，必须完整包含所有出现人物的外表、着装、配饰、场景细节。
   - 禁止使用“同上”或省略描述，必须保证每一行Prompt发给Midjourney都能独立生成长相一致的图。

3. **动静分离原则**：
   - **画面描述（用于MJ生成图片）**：只描述静态元素。包括：场景（环境、光影、天气）、人物外貌（五官、发型、发饰）、服装（材质、颜色、样式）、视角（全景、特写、俯拍）、氛围。禁止描述任何动作动作（如：走、跑、打）。
   - **视频生成（用于即梦生成视频）**：基于画面描述，添加动态行为。包括：人物的具体动作、面部神态变化、镜头语言（平移、推拉、跟拍）、光影的流动。

4. **输出格式（严格执行）**：
---
[序号]. [分镜文案内容]
画面描述：[场景细节], [人物A描述], [人物B描述], [环境光影], [构图视角]
视频生成：[动态行为], [神态变化], [镜头语言控制], [视频氛围感]
---

### 示例参照：
1. 我拉过灵曦的手 转身离开
画面描述：京城街角，赵清月拉着赵灵曦的手，（赵清月，清冷美人，银丝蝴蝶簪，白色刺绣纱衣）,（赵灵曦，明艳张扬，金丝花纹簪，黄色襦裙），傍晚暖橘色斜晖。
视频生成：赵清月突然用力牵起灵曦的手，眼神决绝，身体侧转，镜头跟随两人背影拉开，画面带有明显的离别感。
"""

# 界面展示
st.title("🎬 AI 电影解说全流程分镜工具")
st.info("本工具将文案拆解为适合 MJ 生成图片的静态描述，以及适合即梦生成视频的动态描述。")

# 输入区
col_a, col_b = st.columns([1, 1])

with col_a:
    uploaded_file = st.file_uploader("📂 上传剧情文案 (TXT)", type=['txt'])
    raw_content = ""
    if uploaded_file:
        raw_content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
        st.text_area("文案预览", raw_content, height=200)

with col_b:
    char_profiles = st.text_area(
        "👤 核心角色描述 (必填)", 
        placeholder="例：赵清月：20岁，清冷美人，肤白如雪，银丝蝴蝶坠珠簪，一身白色刺绣绫罗纱衣。\n赵灵曦：18岁，杏眼桃腮，黄色妆花襦裙。",
        height=265
    )

if st.button("🚀 深度解析并生成全套分镜", use_container_width=True):
    if not api_key or not raw_content or not char_profiles:
        st.error("⚠️ 请确保 API Key、文案和角色描述均已填写。")
    else:
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            with st.spinner('导演正在分析剧情、构建画面并设计镜头...'):
                user_input = f"""
                核心角色描述参考：
                {char_profiles}

                需要处理的文案原文：
                {raw_content}
                
                请开始工作，确保每行文案不超过40字，且画面与视频描述分开。
                """
                
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.3,
                )
                
                result = response.choices[0].message.content
                
                st.success("✅ 全套分镜脚本生成完毕！")
                
                # 展示结果
                st.markdown("### 🎥 生成的分镜全稿")
                st.write(result)
                
                # 下载按钮
                st.download_button(
                    label="📥 下载分镜脚本",
                    data=result,
                    file_name="AI视觉分镜脚本.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            st.error(f"❌ 运行失败: {str(e)}")

st.markdown("---")
st.caption("提示：由于生成内容较多，建议使用 GPT-4o 或 Claude-3.5-Sonnet 以获得最稳定的逻辑输出。")
