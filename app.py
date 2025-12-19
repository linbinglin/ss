import streamlit as st
from openai import OpenAI
import re

# 1. 页面配置
st.set_page_config(page_title="导演分镜专家 v2.0", layout="wide", page_icon="🎬")

# 初始化 Session State，用于在步骤之间保存数据
if 'step1_result' not in st.session_state:
    st.session_state['step1_result'] = ""

# 2. 侧边栏：全局配置
st.sidebar.title("⚙️ 全局设置")
api_key = st.sidebar.text_input("1. 输入 API Key", type="password")
base_url = st.sidebar.text_input("2. 接口地址", value="https://blog.tuiwen.xyz/v1")

st.sidebar.markdown("---")
st.sidebar.subheader("3. 模型设置")
model_options = [
    "deepseek-chat", 
    "gpt-4o", 
    "claude-3-5-sonnet-20240620", 
    "gemini-1.5-pro",
    "grok-1",
    "自定义模型 (手动输入)"
]
selected_option = st.sidebar.selectbox("选择模型", model_options)

# 重新加入：用户自己填写的选项逻辑
if selected_option == "自定义模型 (手动输入)":
    model_id = st.sidebar.text_input("请输入具体的 Model ID", placeholder="例如：gpt-4-turbo")
else:
    model_id = selected_option

st.title("🎬 电影解说全流程分镜工具")
st.caption("逻辑分镜 + 视觉扩充 | 严格遵循原文零改动原则")

# --- 第一阶段：剧情分析与逻辑分镜 ---
st.header("第一步：逻辑分镜（构建骨架）")
st.info("💡 目标：AI 将深入理解剧情并按动作/场景重新切分。系统会自动抹除原文换行，强制 AI 进行独立思考。")

uploaded_file = st.file_uploader("📂 上传文案 (TXT)", type=['txt'])

if uploaded_file:
    # 处理编码
    raw_bytes = uploaded_file.getvalue()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except:
        raw_text = raw_bytes.decode("gbk")
    
    # 物理抹除原文所有段落，合并为纯文字流，切断 AI 对原格式的记忆
    clean_stream = "".join(raw_text.split())
    
    st.subheader("📄 待处理文字流（已抹除原格式）")
    st.text_area("文本预览", clean_stream, height=80)

    if st.button("🚀 执行专业分镜重构", use_container_width=True):
        if not api_key or not model_id:
            st.error("❌ 请先配置 API Key 和选择模型！")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 第一步提示词：专注切分，严禁改字
            STEP1_PROMPT = """你是一个专业的电影分镜师。
你的唯一任务是：将提供的【纯文字流】重新切分为【分镜脚本】。

### 强制执行规则：
1. **剧情驱动切分**：不要理会原文结构。根据动作起伏、场景切换、角色对话、情绪转折进行分行。
2. **5秒原则（硬指标）**：每个分镜对应的文案长度严禁超过35个汉字。如果原文的一句话很长，你必须在不改变文字的情况下将其切分为连续的多个分镜。
3. **零增删改原则**：
   - 严禁遗漏原文任何一个字。
   - 严禁添加任何原文以外的词句（不准加旁白、不准加镜头说明）。
   - 你的输出只能包含：[数字序号] + [原文文字]。
4. **输出验证**：如果把你的输出内容去掉序号并合并，必须与原文完全一致。

请开始对以下文字流进行专业切分："""

            with st.spinner("导演正在粉碎旧段落，并按镜头感重新规划..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": STEP1_PROMPT},
                            {"role": "user", "content": clean_stream}
                        ],
                        temperature=0.1 # 保持极低随机性，确保文字不被改动
                    )
                    st.session_state['step1_result'] = response.choices[0].message.content
                except Exception as e:
                    st.error(f"调用失败: {str(e)}")

# 展示第一阶段结果并允许用户微调
if st.session_state['step1_result']:
    st.subheader("📋 导演建议分镜（如有不合理处可手动编辑）")
    st.session_state['step1_result'] = st.text_area("分镜脚本预览", st.session_state['step1_result'], height=300)

    st.markdown("---")

    # --- 第二阶段：视觉描述扩充 ---
    st.header("第二步：视觉化描述生成")
    st.warning("请确保第一步的分镜已经完美，然后再执行此步骤。")
    
    char_desc = st.text_area("👤 输入核心角色及着装（用于维持视觉一致性）", 
                             placeholder="例：林凡：20岁，清冷少年，黑色劲装，马尾。\n苏晴：18岁，紫色罗裙，蝴蝶簪。",
                             height=100)
    
    if st.button("🎨 生成 AI 绘画提示词与视频动作", use_container_width=True):
        if not char_desc:
            st.error("❌ 请先填写角色描述，否则 AI 无法生成稳定的画面。")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 第二步提示词：专注画面描述，原文复读
            STEP2_PROMPT = f"""你是一个视觉美术导演。请基于下方的【分镜脚本】和【角色设定】，为每个分镜生成视觉描述。

角色设定：{char_desc}

### 输出规范：
[序号]. [文案内容]
画面描述：[描述当前分镜的静态画面。包含：具体的环境、光影、人物特征、服装、镜头视角。禁止出现动作词。]
视频生成：[描述当前分镜的动态过程。包含：人物具体的动作行为、面部神态变化、镜头运动方式。]
---
### 注意事项：
1. [文案内容]部分必须严格复读我提供的分镜脚本，严禁增删改一个字。
2. 每个分镜必须独立描述，严禁使用“同上”或省略。"""

            with st.spinner("视觉设计师正在工作中..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": STEP2_PROMPT},
                            {"role": "user", "content": st.session_state['step1_result']}
                        ],
                        temperature=0.4
                    )
                    final_output = response.choices[0].message.content
                    st.subheader("🎥 最终视频制作全案")
                    st.write(final_output)
                    st.download_button("📥 下载完整分镜脚本", final_output, file_name="全流程制作脚本.txt")
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

st.markdown("---")
st.caption("分镜助手 v2.1 | 建议单次处理文本 3000 字以内以保证逻辑一致性。")
