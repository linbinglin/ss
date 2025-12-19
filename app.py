import streamlit as st
from openai import OpenAI
import re

# 1. 页面配置
st.set_page_config(page_title="专业解说分镜大师", layout="wide", page_icon="🎬")

# 2. 侧边栏
st.sidebar.title("⚙️ 配置中心")
api_key = st.sidebar.text_input("API Key", type="password")
base_url = st.sidebar.text_input("接口地址", value="https://blog.tuiwen.xyz/v1")

st.sidebar.markdown("---")
model_options = ["gpt-4o", "claude-3-5-sonnet-20240620", "deepseek-chat", "自定义模型"]
selected_model = st.sidebar.selectbox("选择模型", model_options)
if selected_model == "自定义模型":
    model_id = st.sidebar.text_input("手动输入 Model ID", value="gpt-4o")
else:
    model_id = selected_model

# 3. 强化版分镜提示词
SYSTEM_PROMPT = """你是一个专业的电影解说导演，擅长将长文案转化为极具视觉感的分镜脚本。

### 你的工作流程（核心指令）：
1. **粉碎原文**：忽略用户提供的原文中所有的换行和分段。将全文视为一段没有任何格式的纯文字流。
2. **逻辑重构**：根据剧情逻辑、动作改变、场景转换、对话切换，重新切割文本。
3. **强制分行规则**：
   - 动作改变 -> 必须切分。
   - 场景转换 -> 必须切分。
   - 对话切换 -> A说一句是一行，B回一句是另一行，严禁合并对话。
   - 长度限制 -> 每行严禁超过35个汉字！如果一句话很长，请在不改字的前提下，根据停顿切分成多行。
4. **强制排序**：必须使用数字序号（1. 2. 3. ...）开头，不得间断。

### 禁令（绝对禁止）：
- 禁止将两个连续的动作合并在一行。
- 禁止将两个人的对话合并在一行。
- 禁止遗漏原文任何一个字。
- 禁止添加“镜头：特写”之类的额外描述，只需要分段后的原文。

### 输出样式示例：
1. 8岁那年家里穷得揭不开锅了
2. 怀孕的母亲带着我在寺外乞讨
3. 我把僧人端来的粥饭
4. 全给了母亲
5. 施粥的将军府老妇人
6. 让人领我过来问
7. 都饿成人干了怎么不吃
"""

# 4. 主界面设计
st.title("🎬 电影解说文案自动分镜工具")
st.caption("解决合并段落、不排序、逻辑混乱问题 - 强化逻辑版")

uploaded_file = st.file_uploader("上传文案 (TXT)", type=['txt'])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    st.subheader("📄 原始文案预览")
    st.text_area("RAW", content, height=150)

    if st.button("🚀 深度逻辑分镜处理", use_container_width=True):
        if not api_key:
            st.error("请先填写 API Key")
        else:
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                with st.spinner('正在粉碎原文并重新构建逻辑分镜...'):
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"请严格执行分镜指令，将以下文案打碎并按逻辑排序，确保每行不超过35字且有序号：\n\n{content}"}
                        ],
                        temperature=0.1, # 极低随机性，保证严格执行指令
                    )
                    
                    full_result = response.choices[0].message.content
                    
                    # 逻辑处理：计算分镜数
                    lines = [l for l in full_result.split('\n') if re.match(r'^\d+', l.strip())]
                    shot_count = len(lines)

                    st.success(f"✅ 处理完成！共生成 {shot_count} 个分镜。")
                    
                    # 左右对比显示
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"📊 统计：总分镜数 {shot_count}")
                    with col2:
                        estimated_time = shot_count * 4 # 预估每个分镜4秒
                        st.info(f"⏱️ 预估视频时长：约 {estimated_time} 秒")

                    st.subheader("🎥 最终分镜脚本")
                    st.text_area("Final Script", full_result, height=500)
                    
                    st.download_button("📥 下载结果", full_result, file_name="分镜结果.txt")
                    
            except Exception as e:
                st.error(f"出错啦：{str(e)}")

st.markdown("---")
st.markdown("""
**💡 为什么这次更有效？**
1. **Temperature=0.1**: 强制 AI 变得“死板”，它就不会再自作聪明地合并段落。
2. **强制粉碎指令**: 告诉 AI 忽略你上传文件的原有格式，它必须被迫思考。
3. **序号正则统计**: 代码会自动识别 `1.` 开头的行并计数，方便你掌握进度。
""")
