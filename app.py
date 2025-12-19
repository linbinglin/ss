import streamlit as st
from openai import OpenAI
import re  # 必须导入正则表达式库

# 1. 页面配置
st.set_page_config(page_title="AI 电影导演 v4.1", layout="wide", page_icon="🎬")

# 初始化 Session State
if 'step1_result' not in st.session_state:
    st.session_state['step1_result'] = ""

# 2. 侧边栏：配置中心
st.sidebar.title("⚙️ 系统配置")
api_key = st.sidebar.text_input("1. 输入 API Key", type="password")
base_url = st.sidebar.text_input("2. 接口地址", value="https://blog.tuiwen.xyz/v1")

st.sidebar.markdown("---")
st.sidebar.subheader("3. 模型设置")
model_options = [
    "deepseek-chat", 
    "gpt-4o", 
    "claude-3-5-sonnet-20240620", 
    "gemini-1.5-pro",
    "自定义模型 (手动输入)"
]
selected_option = st.sidebar.selectbox("选择模型", model_options)

if selected_option == "自定义模型 (手动输入)":
    model_id = st.sidebar.text_input("请输入具体的 Model ID", placeholder="例如：gpt-4-turbo")
else:
    model_id = selected_option

st.title("🎬 电影解说全流程分镜工具")
st.caption("精准字数控制 | 叙事节奏优化 | MJ + 即梦提示词生成")

# --- 第一阶段：逻辑分镜 ---
st.header("第一步：精准节奏分镜")
st.info("💡 **分镜准则**：目标字数 **25-35字**。此长度配音约为 4-5秒，完美对齐视频素材。")

uploaded_file = st.file_uploader("📂 上传文案 (TXT)", type=['txt'])

if uploaded_file:
    # 处理编码
    raw_bytes = uploaded_file.getvalue()
    try:
        raw_text = raw_bytes.decode("utf-8")
    except:
        raw_text = raw_bytes.decode("gbk")
    
    # 彻底抹除格式，合并为纯文字流
    clean_stream = "".join(raw_text.split())

    if st.button("🚀 执行精准节奏分镜", use_container_width=True):
        if not api_key or not model_id:
            st.error("❌ 请先配置 API Key 和选择模型！")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 第一步提示词：增加字数区间的强硬要求
            STEP1_PROMPT = """你是一个极其严谨的电影分镜导演。
你的任务是将文字流拆分为【5秒内可完成】的视觉分镜。

### 核心分镜准则（物理级要求）：
1. **黄金字数区间**：每个分镜文案必须控制在 **25 到 35 个汉字** 之间。
2. **合并与拆分逻辑**：
   - 如果原文一句话太短（如10字），必须合并相邻内容凑足25-35字，确保镜头有内容可拍。
   - 如果原文一句话太长（如50字以上），必须从逻辑断点切开，分成两个分镜。
3. **单一视觉原则**：一个分镜（5秒）只允许包含一个核心动作或一个核心场景描述。
4. **零增删改**：禁止改动原文任何字词，不准加戏，不准删减。
5. **格式**：数字序号. 文案内容
"""

            with st.spinner("正在精准计算叙事节奏..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": STEP1_PROMPT},
                            {"role": "user", "content": f"请对以下文字流进行精准分镜：\n\n{clean_stream}"}
                        ],
                        temperature=0.1
                    )
                    st.session_state['step1_result'] = response.choices[0].message.content
                except Exception as e:
                    st.error(f"调用失败: {str(e)}")

# 展示分镜并进行实时字数监测
if st.session_state['step1_result']:
    st.subheader("📋 分镜草案检查（颜色代表字数合规度）")
    
    # 解析并统计字数
    lines = st.session_state['step1_result'].split('\n')
    for line in lines:
        if line.strip():
            # 使用正则表达式去掉开头的数字和标点
            text_only = re.sub(r'^\d+[\.、\s]+', '', line)
            char_count = len(text_only)
            
            if char_count > 40:
                st.error(f"🔴 过长 ({char_count}字) - 建议拆分：{line}")
            elif char_count < 20:
                st.warning(f"🟡 过短 ({char_count}字) - 建议合并：{line}")
            else:
                st.success(f"🟢 完美 ({char_count}字)：{line}")

    st.session_state['step1_result'] = st.text_area("✍️ 在此微调分镜（调整完点击下方按钮生成提示词）", st.session_state['step1_result'], height=300)

    st.markdown("---")

    # --- 第二阶段：视觉描述 ---
    st.header("第二步：视觉扩充（MJ + 即梦）")
    
    char_desc = st.text_area("👤 角色及着装核心设定（非常重要）", 
                             placeholder="例：林凡：25岁，玄色长袍，腰间挂剑，目光如电。\n柳依依：18岁，紫色罗裙，发簪缀珍珠。",
                             height=100)
    
    if st.button("🎨 生成视觉提示词与动作方案", use_container_width=True):
        if not char_desc:
            st.error("❌ 请填写角色描述，否则画面无法保持一致。")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            STEP2_PROMPT = f"""你是一个视觉导演。根据提供的【分镜文案】和【角色设定】，设计分镜画面。

角色设定：{char_desc}

### 输出规范：
[序号]. [文案内容]
画面描述：[静态描述：场景、光影、人物特征、服装细节、视角。禁止动词。]
视频生成：[动态描述：描述分镜内唯一的那个核心动作，确保5秒内能做完。包含神态变化和镜头运动。]
---
### 核心要求：
1. 原文文案严禁改动。
2. 每个分镜必须包含完整的角色外貌特征，防止AI绘画跳戏。"""

            with st.spinner("正在规划视觉宇宙..."):
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
                    st.subheader("🎥 最终制作全案")
                    st.write(final_output)
                    st.download_button("📥 下载完整脚本", final_output, file_name="电影感分镜脚本.txt")
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

st.markdown("---")
st.caption("分镜助手 v4.1 | 修复 re 模块导入问题 | 强化黄金字数区间控制")
