import streamlit as st
from openai import OpenAI
import re

# 1. 页面配置
st.set_page_config(page_title="AI 导演分镜系统 v5.1", layout="wide", page_icon="🎬")

if 'storyboard_raw' not in st.session_state:
    st.session_state['storyboard_raw'] = ""

# 2. 侧边栏配置
st.sidebar.title("⚙️ 配置中心")
api_key = st.sidebar.text_input("1. API Key", type="password")
base_url = st.sidebar.text_input("2. 接口地址", value="https://blog.tuiwen.xyz/v1")

model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义模型"]
selected_option = st.sidebar.selectbox("3. 选择大脑", model_options)
if selected_option == "自定义模型":
    model_id = st.sidebar.text_input("Model ID")
else:
    model_id = selected_option

st.title("🎬 电影解说全流程分镜工具")
st.caption("分步逻辑 | 严格编号 | 视觉动作单元切分")

# --- 第一阶段：逻辑分镜重组 ---
st.header("第一步：逻辑分镜（构建纯净骨架）")
st.info("💡 **分镜准则**：必须有数字编号；严禁添加原文以外的注释；每个分镜仅包含一个核心动作或视觉单元；字数控制在 25-35 字左右。")

uploaded_file = st.file_uploader("📂 上传文案 (TXT)", type=['txt'])

if uploaded_file:
    raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    # 彻底清洗换行，保证 AI 必须重新思考
    full_story = "".join(raw_text.split())

    if st.button("🚀 生成逻辑分镜脚本", use_container_width=True):
        if not api_key:
            st.error("请填入 API Key")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 第一步提示词：极致纯净，强化后半段处理
            STEP1_PROMPT = """你是一个极其严谨的电影分镜师。你的任务是将提供的【纯文字流】拆解为【数字编号的分镜脚本】。

### 核心规则：
1. **严格编号**：每一个分镜必须以“1.” “2.” “3.” 这种数字序号开头，不得遗漏。
2. **拒绝注释**：严禁在分镜中添加任何括号、分析、镜头意图或额外描述。只需输出“数字. 原文”。
3. **视觉单元切分（严禁合并）**：
   - 一个分镜只能包含一个视觉重点或核心动作。
   - 即使是后半段内容，也必须保持与前半段相同的拆解精度。
   - 严禁为了省事将两个不同的动作（如：他跑回家、他坐下喝水）合并在一个分镜里。
4. **字数与时长对齐**：
   - 每个分镜目标字数为 25-35 字。
   - 绝对严禁超过 40 字。
5. **原文零改动**：不准改字、删字、加字。

### 思考逻辑：
读懂剧情 -> 识别动作转折 -> 检查当前累积字数 -> 确认这是一个独立的5秒视觉单元 -> 编号并输出原文。
"""

            with st.spinner("正在逐句深度解析并精确分镜..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": STEP1_PROMPT},
                                  {"role": "user", "content": f"请对以下文字流进行等权重的精确分镜，从头到尾保持高精度拆解，必须带数字编号：\n\n{full_story}"}],
                        temperature=0.1 # 降低随机性，保证编号和文字的稳定性
                    )
                    st.session_state['storyboard_raw'] = response.choices[0].message.content
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

# 展示并进行字数实时统计
if st.session_state['storyboard_raw']:
    st.subheader("📋 纯净分镜脚本预览")
    
    # 辅助统计：计算总分镜数
    temp_lines = [l for l in st.session_state['storyboard_raw'].split('\n') if re.match(r'^\d+', l.strip())]
    st.write(f"📊 当前已识别分镜总数：**{len(temp_lines)}**")

    # 渲染带有字数检测的列表
    for line in temp_lines:
        text_only = re.sub(r'^\d+[\.、\s]+', '', line)
        length = len(text_only)
        if length > 40:
            st.error(f"❌ {line} (字数超标: {length})")
        else:
            st.success(f"✅ {line} (字数: {length})")

    st.session_state['storyboard_raw'] = st.text_area("✍️ 如有合并过多的地方，请在此手动回车分行并重新编号", st.session_state['storyboard_raw'], height=300)

    st.markdown("---")

    # --- 第二阶段：全视觉描述 ---
    st.header("第二步：视觉扩充（基于分镜生成提示词）")
    
    char_desc = st.text_area("👤 角色及着装核心设定", 
                             placeholder="例：林凡：25岁，玄色刺绣长袍，目光如电。柳依依：18岁，紫色罗裙。",
                             height=100)
    
    if st.button("🎨 生成 MJ + 即梦提示词", use_container_width=True):
        if not char_desc:
            st.error("请填写核心角色描述。")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            STEP2_PROMPT = f"""你是一个视觉美术导演。请根据提供的【分镜脚本】和【角色设定】，生成画面指令。

核心角色信息：{char_desc}

### 输出格式（严格执行）：
---
[序号]. [文案原文]
画面描述：[Midjourney专用。描述静态场景、光影、全量人物特征、着装、构图视角。禁止动词。]
视频生成：[即梦专用。描述人物具体的单一核心动作、神态变化、镜头运动。确保5秒内完成。]
---
注意：必须为脚本中的【每一个】编号分镜生成对应的描述，严禁合并分镜。"""

            with st.spinner("视觉设计师正在绘制中..."):
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "system", "content": STEP2_PROMPT},
                                  {"role": "user", "content": st.session_state['storyboard_raw']}],
                        temperature=0.4
                    )
                    final_output = response.choices[0].message.content
                    st.subheader("🎥 最终视频制作脚本")
                    st.write(final_output)
                    st.download_button("📥 下载完整分镜脚本", final_output, file_name="电影感分镜脚本.txt")
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

st.markdown("---")
st.caption("分镜助手 v5.1 | 解决了后半段疲劳及编号缺失问题")
