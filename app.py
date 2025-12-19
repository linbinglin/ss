import streamlit as st
from openai import OpenAI
import os

# 1. 页面配置
st.set_page_config(page_title="AI 文案自动分镜工具", layout="wide", page_icon="🎬")

# 2. 侧边栏：配置参数
st.sidebar.title("⚙️ 全局配置")
api_key = st.sidebar.text_input("1. 输入 API Key", type="password", help="从中转平台获取的令牌 (sk-...)")
base_url = st.sidebar.text_input("2. 接口地址", value="https://blog.tuiwen.xyz/v1", help="中转接口的基础URL")

# 侧边栏：模型选择逻辑
st.sidebar.markdown("---")
st.sidebar.subheader("3. 模型设置")
model_options = [
    "deepseek-chat", 
    "gpt-4o", 
    "claude-3-5-sonnet-20240620", 
    "gemini-1.5-pro",
    "grok-1",
    "doubao-pro-128k",
    "自定义模型 (手动输入)"
]
selected_option = st.sidebar.selectbox("选择或输入模型名称", model_options)

# 如果选择“自定义模型”，则显示文本输入框
if selected_option == "自定义模型 (手动输入)":
    model_id = st.sidebar.text_input("请输入具体的 Model ID", placeholder="例如：gpt-4-turbo")
else:
    model_id = selected_option

# 3. 主界面
st.title("🎬 电影解说文案自动分镜工具")
st.info("💡 操作流程：配置侧边栏参数 -> 上传文案 -> AI 自动分析分镜 -> 下载结果")

# 系统提示词（Prompt）保持不变
SYSTEM_PROMPT = """你是一个优秀的电影解说工作员。请对提供的文本进行分镜处理。
必须严格遵守以下规则：
1. 逐字逐句理解内容，进行分段处理。
2. 分镜逻辑：每个角色对话切换、场景切换、动作画面改变，必须设为下一个分镜。
3. 严禁遗漏：不可遗漏原文任何一句话、一个字，不能改变原文故事结构，禁止添加原文以外的内容。
4. 物理限制：每个分镜文案不能太长。因为一个分镜停留约5秒，35个字符接近5秒。因此，单行分镜文案严格控制在35个汉字以内。如果原句过长，请在不改变原意和文字的前提下，将其拆分为多个连续分镜。
5. 格式要求：使用数字编号开头，每行一个分镜。
"""

# 4. 文件上传与逻辑处理
uploaded_file = st.file_uploader("选择本地 TXT 文案文件", type=['txt'])

if uploaded_file is not None:
    # 读取文本内容
    try:
        content = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        content = uploaded_file.getvalue().decode("gbk") # 兼容某些中文编码
        
    st.subheader("📝 原文内容预览")
    st.text_area("Original Text", content, height=150)

    if st.button("🚀 开始生成分镜脚本", use_container_width=True):
        if not api_key:
            st.warning("⚠️ 请先在侧边栏填写 API Key")
        elif not model_id:
            st.warning("⚠️ 请选择或输入 Model ID")
        else:
            try:
                # 初始化客户端
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                with st.spinner(f'正在使用 {model_id} 分析剧情中...'):
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": content}
                        ],
                        temperature=0.2, # 越低越严谨，防止AI自由发挥
                    )
                    
                    result = response.choices[0].message.content
                    
                    st.success("✅ 分镜处理完成！")
                    st.subheader("🎥 整理后的分镜内容")
                    st.text_area("Output Script", result, height=500)
                    
                    # 提供下载功能
                    st.download_button(
                        label="📥 下载分镜脚本 (.txt)",
                        data=result,
                        file_name=f"分镜脚本_{model_id}.txt",
                        mime="text/plain"
                    )
                    
            except Exception as e:
                st.error(f"❌ 运行出错：{str(e)}")
                st.info("提示：请检查 API Key 是否正确，或该模型是否在您的中转包额度内。")

# 5. 底部版权或说明
st.markdown("---")
st.caption("文案分镜助手 v1.1 | 建议单次处理文本量不超过 5000 字以获得最佳效果。")
