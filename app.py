import streamlit as st
from openai import OpenAI
import time

# --- 页面基础配置 ---
st.set_page_config(
    page_title="AI 智能文案分镜助手",
    page_icon="🎬",
    layout="wide"
)

# --- 侧边栏配置 ---
st.sidebar.title("⚙️ 设置")

# 1. API 配置
api_key = st.sidebar.text_input("请输入 API Key (云雾AI)", type="password", help="请填写您的 yunwu.ai API 密钥")
base_url = "https://yunwu.ai/v1"  # 固定要求的中转地址

# 2. 模型选择 (包含用户要求的模型)
model_options = [
    "gpt-4o",
    "deepseek-chat",  # DeepSeek V3
    "deepseek-reasoner", # DeepSeek R1
    "claude-3-5-sonnet-20240620",
    "gemini-1.5-pro-latest",
    "grok-beta",
    "doubao-pro-32k", # 假设中转支持的豆包模型名称，可根据实际情况修改
    "gpt-4o-mini"
]
# 允许用户手动输入模型名称（防止API模型名称变动）
selected_model = st.sidebar.selectbox("选择 AI 模型", model_options)
custom_model = st.sidebar.text_input("自定义模型名称 (如果上述列表不可用)", "")

# 最终使用的模型ID
final_model = custom_model if custom_model else selected_model

st.sidebar.markdown("---")
st.sidebar.info(f"当前连接节点: {base_url}\n\n当前模型: {final_model}")

# --- 主界面 ---
st.title("🎬 智能文案分镜生成器")
st.markdown("""
本工具将自动把文本转化为视频分镜脚本。
**处理逻辑：**
1. 自动清除原文所有段落格式，防止AI偷懒。
2. 根据**对话、场景、动作**严格拆解分镜。
3. 保证**不漏一字、不加一字**。
""")

# 3. 文件上传
uploaded_file = st.file_uploader("请上传文案 (.txt)", type=['txt'])

# --- 核心处理逻辑 ---
if uploaded_file is not None:
    # 读取文件
    original_text = uploaded_file.read().decode("utf-8")
    
    # 预处理：显示原文统计
    st.subheader("📄 原文预览")
    with st.expander("点击查看原文内容", expanded=False):
        st.text_area("原文", original_text, height=200)

    # 核心动作：点击开始分镜
    if st.button("🚀 开始生成分镜", type="primary"):
        if not api_key:
            st.error("请先在左侧侧边栏输入 API Key！")
        else:
            # 1. 预处理文本：去掉所有换行符，强制变成一行，迫使AI重新思考结构
            flattened_text = original_text.replace("\n", "").replace("\r", "").replace("　", "")
            
            # 2. 构建系统提示词 (Prompt Engineering) - 严格遵循你的5点要求
            system_prompt = f"""
你是一个专业的视频分镜脚本师。请对用户提供的文本进行严格的分镜处理。

【重要原则】
1. **完整性**：输出的内容必须包含原文的每一个字，**严禁删减**，也**严禁添加**原文以外的任何剧情或描述。
2. **结构重组**：原文已被压缩为一行。你需要根据语义重新划分。
3. **分镜触发条件**：
   - 角色对话切换时 -> 新分镜
   - 场景地点切换时 -> 新分镜
   - 动作画面发生明显改变时 -> 新分镜
4. **节奏控制**：
   - 分镜文案不能太长（避免视觉疲劳）。
   - 分镜文案不能太短（避免画面过于破碎）。
   - 请根据语义逻辑合理断句。

【输出格式要求】
请直接输出数字编号的分镜列表，不要包含任何开场白或结束语。
格式如下：
1. [文案内容]
2. [文案内容]
3. [文案内容]
...

请处理以下文本：
"""
            
            # 显示处理状态
            status_box = st.status("正在请求 AI 模型进行分镜拆解...", expanded=True)
            
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                status_box.write(f"正在连接模型: {final_model}...")
                status_box.write("正在进行语义分析与场景重组...")
                
                # 流式输出 (Stream) 以获得更好的体验
                stream = client.chat.completions.create(
                    model=final_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": flattened_text}
                    ],
                    stream=True,
                    temperature=0.7 # 稍微降低创造性，保证忠实于原文
                )
                
                st.subheader("🎞️ 分镜脚本结果")
                result_container = st.empty()
                full_response = ""
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        result_container.markdown(full_response)
                
                status_box.update(label="✅ 分镜处理完成！", state="complete", expanded=False)
                
                # 提供下载按钮
                st.download_button(
                    label="📥 下载分镜脚本 (.txt)",
                    data=full_response,
                    file_name="分镜脚本.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                status_box.update(label="❌ 发生错误", state="error")
                st.error(f"调用 API 时发生错误: {str(e)}")
                st.info("提示：请检查您的 API Key 是否正确，或所选模型ID是否有效。")

else:
    st.info("请先上传一个 TXT 文件以开始。")
