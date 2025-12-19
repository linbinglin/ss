import streamlit as st
from openai import OpenAI

# 1. 页面配置
st.set_page_config(page_title="AI 导演分镜工作流", layout="wide", page_icon="🎬")

# 初始化 Session State
if 'step1_result' not in st.session_state:
    st.session_state['step1_result'] = ""

# 侧边栏
st.sidebar.title("⚙️ 全局配置")
api_key = st.sidebar.text_input("API Key", type="password")
base_url = st.sidebar.text_input("接口地址", value="https://blog.tuiwen.xyz/v1")
model_id = st.sidebar.selectbox("选择模型", ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义"])
if model_id == "自定义":
    model_id = st.sidebar.text_input("输入模型 ID")

st.title("🎬 电影解说全流程分镜工具")

# --- 第一阶段：纯文本逻辑切分 ---
st.header("第一阶段：原文逻辑分镜（零增删）")
st.info("⚠️ 此步骤仅负责对原文进行分行和编号。规则：不准多一个字，不准少一个字，不准改一个字。")

uploaded_file = st.file_uploader("上传文案 (TXT)", type=['txt'])

if uploaded_file:
    # 处理编码
    raw_bytes = uploaded_file.getvalue()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except:
        raw_text = raw_bytes.decode("gbk")
    
    # 预处理：去掉干扰的空行，保证文本连续
    processed_text = "".join([line.strip() for line in raw_text.splitlines() if line.strip()])
    
    st.subheader("📄 原文内容确认")
    st.text_area("待处理全文", processed_text, height=100)

    if st.button("🚀 开始精确切分", use_container_width=True):
        if not api_key:
            st.error("请填入 API Key")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 强化版“零改动”提示词
            STEP1_PROMPT = """你是一个机械化的文本切分器。你的任务是将用户提供的文案，按照逻辑进行分行并添加序号。

### 核心铁律（必须死守）：
1. **禁止增删改**：严禁遗漏原文任何一个字，严禁添加任何原文之外的文字（包括不准添加“场景：”、“旁白：”、“镜头：”等修饰词）。
2. **唯一任务**：你只负责在合适的地方按下“回车键”并加上数字序号。
3. **切分准则**：
   - 每行文字（含标点）绝对不能超过40个字（为了适配5秒视频）。
   - 必须根据动作转折、场景切换、对话切换进行分行。
   - 即使原文一句话很长，只要超过40个字，就必须从中间逻辑断点处切开。
4. **输出验证**：如果把你的输出内容去掉序号并合并，必须与原文完全一致，哪怕一个标点符号都不能变。

### 输出示例要求：
1.原文内容第一部分
2.原文内容第二部分
...
"""
            
            with st.spinner("正在进行手术级切分..."):
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": STEP1_PROMPT},
                        {"role": "user", "content": f"请对以下原文进行物理切分，严禁改变或添加文字：\n\n{processed_text}"}
                    ],
                    temperature=0.0  # 设置为0，彻底消除AI的创造性
                )
                st.session_state['step1_result'] = response.choices[0].message.content

# 展示第一阶段结果
if st.session_state['step1_result']:
    st.subheader("📋 逻辑分镜结果（核对原文文字）")
    st.session_state['step1_result'] = st.text_area("请检查是否有多余字句，如有可手动修改", st.session_state['step1_result'], height=300)

    st.markdown("---")

    # --- 第二阶段：视觉提示词扩充 ---
    st.header("第二阶段：基于分镜生成视觉描述")
    
    char_desc = st.text_area("👤 角色及着装描述（用于维持视觉一致性）", 
                             placeholder="例如：林风：20岁，黑色劲装，马尾辫。\n苏晴：18岁，紫色罗裙，蝴蝶发饰。",
                             height=100)
    
    if st.button("🎨 生成 AI 绘画与视频指令", use_container_width=True):
        if not char_desc:
            st.warning("请填写角色描述，确保 MJ 画出来的人物不走样。")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 这里的提示词允许 AI 发挥想象力去描述画面，但要求 [原文文案] 保持不变
            STEP2_PROMPT = f"""你是一个视觉设计师。请为下方的分镜文案配上视觉描述。
            
            角色统一设定：{char_desc}
            
            ### 任务要求：
            1. 每一组输出包含：序号、原文文案、画面描述、视频生成。
            2. **原文复读**：[文案]部分必须直接引用我提供的内容，严禁改动。
            3. **画面描述（MJ）**：描述静态细节。包含场景、人物外貌、服装、光影、视角。禁止动作。
            4. **视频生成（即梦）**：基于画面，描述动态。包含动作变化、神态、镜头运动。
            
            ### 输出格式：
            [序号]. [原文文案（禁止改动）]
            画面描述：...
            视频生成：...
            ---
            """
            
            with st.spinner("正在构建视觉宇宙..."):
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": STEP2_PROMPT},
                        {"role": "user", "content": st.session_state['step1_result']}
                    ],
                    temperature=0.5
                )
                final_output = response.choices[0].message.content
                st.subheader("🎥 最终全流程脚本")
                st.write(final_output)
                st.download_button("📥 下载完整脚本", final_output, file_name="全流程分镜脚本.txt")

st.markdown("---")
st.caption("提示：第一步设置 Temperature 为 0，确保了 AI 不会乱加戏；第二步设置 Temperature 为 0.5，确保了画面描述足够丰富。")
