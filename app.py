import streamlit as st
import requests
import json
import time

st.set_page_config(
    page_title="短剧剧本生成器",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.output-box {
    background: #f8f8f8;
    border-left: 3px solid #333;
    padding: 1.5rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.88rem;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
}
.stButton > button {
    background-color: #1a1a1a;
    color: white;
    border: none;
    padding: 0.6rem 2rem;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 4px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """你是"短剧改编编剧"，任务是把输入小说改编为可拍摄、节奏有效、人物鲜明的短剧剧本。

====================
一、总目标（必须同时满足）
====================
1) 忠于原著：不新增关键剧情，不改因果，不改人物核心性格。
2) 影视化：不是复述小说，而是转成可拍画面与有效对白。
3) 逻辑清晰：人物问答有对应，事件衔接丝滑，观众能跟上。
4) 情绪有效：能调动情绪，但不刻意拉扯同一情绪包袱。
5) 实用输出：格式简洁，便于直接进入拍摄拆解。
6) 描述内容：把女主许多多的心理活动，化为内心OS描述，增加许多多的戏份，展现她的人格魅力

====================
二、优先级（冲突时按此顺序）
====================
P1. 原著事件与因果完整
P2. 人物性格一致 + 对话逻辑成立
P3. 影视可拍性（能拍出来）
P4. 节奏与情绪张力
P5. 文采修饰

====================
三、你必须理解的"影视化优化"
====================
影视化优化不是"多写"也不是"少写"，而是"有效转化"：

A. 可拍转化
- 心理描写 → 内心OS/表情/动作/（强制性\必须符合角色性格）
- 设定信息 → 场景细节或人物互动中自然带出
- 异能/特殊能力 → 详细描述视觉效果（出现方式、反应、后果）

B. 互动转化
- 不允许单人独角戏长期霸屏
- 任一关键动作后，要有他人反应或关系变化反馈

C. 推进转化
- 每段内容必须至少完成一个功能：推剧情 / 推关系 / 推人物性格 / 推悬念
- 纯重复、纯回锅、纯解释同一信息 → 删

====================
四、对白规则（高优先）
====================
1) 对白先服务逻辑，再服务风格。
2) 问与答必须有逻辑对应，允许：正面回答 / 回避（但要显示回避意图）/ 反问（但要推动冲突）/ 打断（但要带来新方向）
3) 角色"说什么"不能脱离原著信息边界。
4) 角色"怎么说"体现性格差异（语气、节奏、措辞、攻击方式）。
5) 禁止把同一句"模板腔"分配给所有角色。

====================
五、人物存在感规则（防工具人）
====================
1) 关键角色每次出场都要有"可识别行为"或"可识别表达"。
2) 不能说话的角色可用内心OS展示，作用是丰富角色性格。
3) 任何角色连续长时间仅"站着看"且无功能 → 判定为工具人，必须改写互动。

====================
六、场景与输出格式（严格执行）
====================
输出时仅使用以下形式：

【场景：地点｜时间（白天/夜晚）】
正文段落...
正文段落...

规则：
1) 只有"场景变化"时才写新的【场景】头。
2) 同一场景内连续描述，不重复场景头。
3) 每个自然段都必须是一个完整"可拍单元"（有动作/对白/结果中的至少两项）。
4) 描述简洁但具体，避免空泛形容词堆砌。
5) 不使用"像……""宛如……"等比喻词。

====================
七、输出结尾必须附加简报
====================
在剧本末尾附加：
- 原著保真：列出未改动的关键事件点
- 影视化优化：列出本次做的3-5个有效优化点
- 逻辑保障：列出3处关键问答或衔接如何成立

====================
参考示例（必须参考此格式与处理方式）
====================

【输入示例 - 原著片段】
林初雪站在拍卖会场中央，心跳如擂鼓。她知道，今天这场拍卖会将决定她的命运。她的手心全是汗，紧张得几乎无法呼吸。她告诉自己要冷静，要冷静，但心跳声却越来越响，仿佛要跳出胸腔。
"各位贵宾，接下来这件拍品非同寻常。"拍卖师故作神秘地说，"这是一枚千年寒玉，传说中能够觉醒灵力的至宝！"
林初雪的瞳孔骤然收缩。千年寒玉？那不正是她母亲临终前托付给她的东西吗？她明明藏得很好，怎么会出现在这里？她的心一下子提到了嗓子眼，脑子里一片混乱。
"一百万！"台下有人出价。
"两百万！"又有人喊价。
林初雪咬紧嘴唇，她知道自己必须拿回那枚寒玉，那是母亲的遗物，也是她唯一的希望。可是她身上只有五十万，根本不够。她该怎么办？她感到绝望，深深的绝望。
就在这时，包厢里传来一个慵懒的男声："一千万。"
全场哗然。林初雪抬头看向二楼包厢，透过薄纱帘幕，她隐约看到一个修长的身影。那个人是谁？为什么要出这么高的价格？她心里充满了疑惑。
"一千万一次，一千万两次——"拍卖师举起木槌。
林初雪再也忍不住了，她冲上前大喊："等等！那是我的东西！"
拍卖师愣住了，台下的宾客也都愣住了。
"小姐，拍卖会有拍卖会的规矩。"拍卖师皮笑肉不笑地说，"你说是你的，有证据吗？"
"我……"林初雪语塞。她确实没有证据。
就在这时，二楼包厢的门打开了。一个穿着黑色长袍的男人缓缓走出来，他居高临下地看着林初雪，嘴角勾起一抹玩味的笑容。
"有意思。"他开口道，"既然这位小姐说寒玉是她的，不如让她证明一下？"
林初雪握紧拳头，深吸一口气，闭上眼睛，开始调动体内沉睡已久的灵力。
突然，展台上的寒玉开始发光！淡蓝色的光芒越来越亮，整个拍卖厅都被照得如同白昼。所有人都震惊了。
"这……这怎么可能？"拍卖师结结巴巴地说。
黑袍男人的眼神变了，从玩味变成了认真。他盯着林初雪，没想到这个普通的女孩竟然真的能引发寒玉共鸣。
"看来，"黑袍男人缓缓开口，"这位小姐确实与寒玉有缘。不过，既然寒玉已经流入拍卖会，就该按规矩来。我出一千万，小姐若是拿不出更高的价格，那寒玉就归我了。"
林初雪的心沉到了谷底。她拿不出一千万。她咬着牙，眼眶发红。

【输出示例 - 剧本】

【场景：拍卖会场｜夜晚】
拍卖师掀开红布。展台上的寒玉在射灯下泛着青白色。
林初雪站在后排第三列，手里攥着一张支票，指节发白。她看清寒玉后身体往前倾，嘴唇动了一下没出声。
拍卖师敲槌："千年寒玉，起拍一百万。"
前排男人举牌："一百五十万。"
左侧女宾客跟着举牌："两百万。"
林初雪把支票翻过来看背面数字，又翻回去，咬住下唇。

【场景：拍卖会场二楼包厢｜夜晚】
黑袍男人坐在栏后的椅子上，手指敲了两下扶手。
侍从俯身听令，转身推开纱帘，朝楼下喊："一千万。"

【场景：拍卖会场｜夜晚】
叫价声停住。
前排举牌的男人把号牌放下，转头看向二楼。
左侧两名女宾客凑近低声说话。
后排有人举起手机对准包厢方向。
拍卖师握槌的手停在半空。
林初雪抬头盯着二楼纱帘，呼吸加快。
拍卖师回过神，举槌："一千万一次——"
林初雪冲到台前，手按在展台边缘："等等！"
拍卖师收回木槌，皱眉看她。台下有人站起来看热闹。
林初雪深吸一口气："这块玉是我母亲的遗物。"
拍卖师脸色一冷："小姐，拍卖会讲证据。你拿什么证明？"
林初雪把支票拍在台面上："我先不加价，我先证明它认我。"
拍卖师看向二楼，没接话。

【场景：拍卖会场二楼栏边｜夜晚】
包厢门打开，黑袍男人走到栏杆边，双手撑在栏杆上俯视她："可以。你证明。"

【场景：拍卖会场展台｜夜晚】
林初雪双手按在展台玻璃上，闭眼，肩膀绷紧。
她的呼吸放慢，手掌下的玻璃表面开始起雾。
雾气蔓延到展台四角，边缘凝出白霜。
寒玉内部亮起淡蓝光，一层层增强。
吊灯下方飘出白色雾气，前排酒杯表面结出细小冰晶。
前排宾客往后退，椅子拖动声响成一片。
拍卖师手一松，木槌掉在地上。
后排有人举着手机连拍。
林初雪睁眼，脸色发白，额头全是汗。她手撑着台面才站稳，抬头看向二楼："够不够？"

【场景：拍卖会场二楼栏边｜夜晚】
黑袍男人盯着寒玉看了三秒，直起身："认主现象成立。"
他转向林初雪："但拍卖流程已启动，规则不变。一千万，你继续出价。"

【场景：拍卖会场展台｜夜晚】
林初雪把支票推到拍卖师面前。
拍卖师低头看一眼，抬起头："五十万。"
台下有人笑出声，有人摇头。
林初雪抬头盯住二楼黑袍男人，声音发紧："你到底想要什么？"
黑袍男人转身往包厢里走，停在门口侧过头："明晚子时，城北废宅。你一个人来，寒玉的事继续谈。"
他推开门："迟到作废。"
包厢门合上。
林初雪把支票收回袖子里，转身离开展台。
保安让开一条路，宾客们盯着她背影议论。

-----------------------------
【剧本简报】
原著保真：拍卖会见到母亲遗物寒玉、无力竞拍、神秘男人出天价压场、被迫当场证明认主、灵力觉醒引发异象、对方以规则压制并抛出下一步约见条件。
影视化优化：心理描写改为手部动作（攥支票/指节发白/翻看数字/咬唇）；灵力觉醒具象化为起雾→结霜→发光→环境结冰的递进视觉链；群体反应拆解为个体可拍动作；删除所有重复心理独白；用支票金额被公开读出触发台下笑声替代"绝望"旁白。
逻辑保障："你有证据"→"我先证明"形成挑战-应战；"够不够"→"认主成立"给出判定结果；"五十万"被读出→台下笑声形成群体反馈；"你想要什么"→"明晚城北废宅"抛出明确后续行动钩子。

====================
现在请按照以上规则和示例，将用户提供的小说原文改编为短剧剧本。
"""


PRESET_MODELS = [
    "gpt-4o",
    "claude-opus-4-7",
    "gemini-3.1-pro-preview",
    "deepseek-chat",
    "deepseek-reasoner",
    "qwen-plus",
    "qwen-turbo",
    "自定义输入",
]


def call_api(api_key, base_url, model, user_content):
    api_key = str(api_key).strip()
    base_url = str(base_url).strip()
    model = str(model).strip()
    user_content = str(user_content).strip()

    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "请将以下小说原文改编为短剧剧本：\n\n" + user_content},
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 8192,
    }

    base_url = base_url.rstrip("/") + "/"
    url = base_url + "chat/completions"

    with requests.post(url, headers=headers, json=payload, stream=True, timeout=180) as resp:
        if resp.status_code >= 400:
            try:
                err_text = resp.text
            except Exception:
                err_text = ""
            raise requests.exceptions.HTTPError(
                str(resp.status_code) + " 上游返回: " + err_text[:500],
                response=resp,
            )

        ctype = resp.headers.get("Content-Type", "")
        if "application/json" in ctype and "event-stream" not in ctype:
            try:
                data = resp.json()
                content = (data.get("choices", [{}])[0].get("message", {}) or {}).get("content") or ""
                if content:
                    yield content
                return
            except Exception:
                pass

        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            try:
                decoded = raw_line.decode("utf-8", errors="ignore")
            except Exception:
                continue

            if decoded.startswith("data:"):
                decoded = decoded[5:].lstrip()
            if not decoded:
                continue
            if decoded == "[DONE]":
                break

            try:
                chunk = json.loads(decoded)
            except Exception:
                continue

            if isinstance(chunk, dict) and chunk.get("error"):
                err = chunk["error"]
                msg = err.get("message") if isinstance(err, dict) else str(err)
                raise RuntimeError("上游返回错误: " + str(msg))

            choices = chunk.get("choices") or []
            if not choices:
                continue

            delta = choices[0].get("delta") or choices[0].get("message") or {}
            piece = delta.get("content") or ""
            if piece:
                yield piece


with st.sidebar:
    st.markdown("## API Config")
    st.markdown("---")

    with st.form("api_config_form", clear_on_submit=False):
        api_key_input = st.text_input("API Key", type="password", placeholder="sk-xxx")
        base_url_input = st.text_input("Base URL", value="https://yunwu.ai/v1/")
        model_choice = st.selectbox("Model", options=PRESET_MODELS, index=0)
        custom_input = st.text_input(
            "自定义 Model ID（仅当上方选择'自定义输入'时生效）",
            value="",
            placeholder="e.g. gemini-3-pro-preview",
        )
        submitted = st.form_submit_button("保存配置", use_container_width=True)

    # 用 session_state 持久化
    if submitted:
        st.session_state["api_key"] = api_key_input.strip()
        st.session_state["base_url"] = base_url_input.strip() or "https://yunwu.ai/v1/"
        if model_choice == "自定义输入":
            st.session_state["model"] = custom_input.strip()
        else:
            st.session_state["model"] = model_choice

    cur_model = st.session_state.get("model", "")
    st.caption("当前模型: " + (cur_model if cur_model else "（未保存）"))
    st.markdown("---")


st.markdown("## 短剧剧本生成器")
st.markdown("将小说原文一键转化为可拍摄的短剧剧本")

input_method = st.radio(
    "input",
    options=["粘贴文本", "上传文件"],
    horizontal=True,
    label_visibility="collapsed",
)

novel_text = ""

if input_method == "粘贴文本":
    with st.form("novel_form"):
        raw = st.text_area("text", height=280,
                           placeholder="请粘贴小说原文...",
                           label_visibility="collapsed")
        confirm = st.form_submit_button("确认原文", use_container_width=True)
    if confirm:
        st.session_state["novel_text"] = str(raw).strip()
    novel_text = st.session_state.get("novel_text", "")

else:
    uploaded_file = st.file_uploader(
        "file",
        type=["txt"],
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        try:
            novel_text = uploaded_file.read().decode("utf-8")
            st.success("读取成功，共 " + str(len(novel_text)) + " 字")
        except UnicodeDecodeError:
            try:
                uploaded_file.seek(0)
                novel_text = uploaded_file.read().decode("gbk")
                st.success("读取成功(GBK)，共 " + str(len(novel_text)) + " 字")
            except Exception as e:
                st.error("解码失败: " + str(e))
                novel_text = ""

if novel_text:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("字数", str(len(novel_text)) + " 字")
    with col2:
        st.metric("预计场景", "~" + str(max(1, len(novel_text) // 300)) + " 场")
    with col3:
        # 将 final_model 改为 cur_model
        st.metric("模型", cur_model if cur_model else "未选择")

st.markdown("---")
generate_btn = st.button("开始生成剧本", use_container_width=True)

if generate_btn:
    safe_key = st.session_state.get("api_key", "")
    safe_url = st.session_state.get("base_url", "https://yunwu.ai/v1/")
    safe_model = st.session_state.get("model", "")
    safe_text = str(novel_text).strip() if novel_text else ""

    if not safe_key:
        st.error("请先在左侧填写 API Key 并点击『保存配置』")
        st.stop()
    if not safe_model:
        st.error("请先在左侧选择或输入 Model ID 并点击『保存配置』")
        st.stop()
    if not safe_text:
        st.error("请输入或上传原文")
        st.stop()

    progress_bar = st.progress(0, text="connecting...")
    status_box = st.empty()
    output_box = st.empty()

    full_output = ""
    start_time = time.time()

    try:
        progress_bar.progress(15, text="analyzing...")
        time.sleep(0.3)
        progress_bar.progress(30, text="generating...")

        token_count = 0
        for piece in call_api(safe_key, safe_url, safe_model, safe_text):
            full_output = full_output + piece
            token_count = token_count + len(piece)
            p = min(30 + int(token_count / 50), 90)
            progress_bar.progress(p, text="writing...")
            output_box.markdown(
                '<div class="output-box">' + full_output + "</div>",
                unsafe_allow_html=True,
            )

        elapsed = round(time.time() - start_time, 1)
        progress_bar.progress(100, text="done")
        status_box.success("完成，共 " + str(len(full_output)) + " 字，用时 " + str(elapsed) + " 秒")

        st.download_button(
            label="下载剧本 TXT",
            data=full_output.encode("utf-8"),
            file_name="script.txt",
            mime="text/plain",
            use_container_width=True,
        )

    except requests.exceptions.ConnectionError:
        progress_bar.empty()
        st.error("连接失败，请检查 Base URL")
    except requests.exceptions.HTTPError as e:
        progress_bar.empty()
        code = getattr(e.response, "status_code", 0) if e.response is not None else 0
        body = ""
        try:
            if e.response is not None:
                body = e.response.text[:300]
        except Exception:
            pass
        if code == 401:
            st.error("API Key 无效")
        elif code == 429:
            st.error("请求频率超限")
        elif code == 404:
            st.error("模型不存在或路径错误，请检查 Model ID 与 Base URL")
        elif code == 0:
            st.error("上游返回异常（无 HTTP 状态码）：" + str(e))
        else:
            st.error("HTTP 错误 " + str(code) + "：" + (body or str(e)))
    except RuntimeError as e:
        progress_bar.empty()
        st.error(str(e))
    except requests.exceptions.Timeout:
        progress_bar.empty()
        st.error("请求超时，请缩短原文后重试")
    except Exception as e:
        progress_bar.empty()
        st.error("错误: " + str(e))
