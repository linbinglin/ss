import streamlit as st
from openai import OpenAI

# 1. 页面配置
st.set_page_config(page_title="AI 视频分镜专家", layout="wide", page_icon="🎬")

# 2. 侧边栏配置
st.sidebar.title("⚙️ 全局配置")
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
    "doubao-pro-128k",
    "自定义模型 (手动输入)"
]
selected_option = st.sidebar.selectbox("选择模型", model_options)

if selected_option == "自定义模型 (手动输入)":
    model_id = st.sidebar.text_input("请输入具体的 Model ID")
else:
    model_id = selected_option

# 3. 核心提示词优化 (解决不分镜问题的关键)
SYSTEM_PROMPT = """你是一个顶级的短视频分镜拆解专家。你的任务是将用户提供的文案重新进行【镜头化拆解】。

### 核心分镜指令（必须严格执行）：
1. 彻底打破原文段落：禁止直接套用用户上传的段落格式。请将全文视为一个流动的叙事流，重新进行切分。
2. 镜头级拆分：每当剧情出现以下变化，必须强制换行并作为下一个分镜：
   - 动作改变（如：从走路变成坐下）
   - 场景改变（如：从室内来到室外）
   - 情绪转折（如：从哭泣变成大笑）
   - 对话切换（每一句对话必须独立成行）
   - 重点强调（如：一个特写镜头感的内容）
3. 严格字数限制（硬性指标）：
   - 每个分镜文案绝对不能超过35个汉字（为了适配5秒内的语音）。
   - 如果原句很长（超过35字），你必须在保持语义完整的前提下将其拆分为连续的两个或多个分镜，严禁保留长难句。
4. 零增删原则：严禁遗漏原文任何一个字，严禁添加任何原文之外的解说词或描述。
5. 格式要求：每一行前面必须加上数字编号。

### 输出示例：
原文：8岁那年家里穷得揭揭不开锅了，怀孕的母亲带着我在寺外乞讨，我把僧人端来的粥饭全给了母亲。
输出：
1.8岁那年家里穷得揭不开锅了
2.怀孕的母亲带着我在寺外乞讨
3.我把僧人端来的粥饭
4.全给了母亲

请处理以下文案："""

# 4. 主界面
st.title("🎬 电影解说文案自动分镜工具")
st.markdown("---")

uploaded_file = st.file_uploader("📂 上传 TXT 格式的文案文件", type=['txt'])

if uploaded_file:
    # 自动处理编码
    raw_bytes = uploaded_file.getvalue()
    try:
        content = raw_bytes.decode("utf-8")
    except:
        content = raw_bytes.decode("gbk")
        
    st.subheader("📄 原文预览")
    st.text_area("Original Content", content, height=150)

    if st.button("🚀 生成分镜脚本", use_container_width=True):
        if not api_key or not model_id:
            st.error("❌ 请先完成侧边栏的 API Key 和模型配置！")
        else:
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                with st.spinner(f'正在使用 {model_id} 进行深度分镜分析...'):
                    # 增加流式输出，提升用户体验
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"请将这段文案重新分镜，注意每行不超过35字，必须打破原段落：\n\n{content}"}
                        ],
                        temperature=0.3, # 低随机性，严格遵循指令
                    )
                    
                    result = response.choices[0].message.content
                    
                    st.success("✅ 深度分镜拆解完成！")
                    st.subheader("🎥 最终分镜脚本")
                    st.text_area("Result Script", result, height=500)
                    
                    st.download_button(
                        label="📥 下载分镜脚本",
                        data=result,
                        file_name=f"分镜结果_{model_id}.txt",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"❌ API 调用失败: {str(e)}")

st.markdown("---")
st.caption("提示：如果分镜效果仍不理想，建议更换 Claude-3.5-Sonnet 或 GPT-4o 模型，这类模型对‘字数限制’和‘逻辑拆分’的遵循度最高。")
