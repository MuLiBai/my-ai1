import streamlit as st
import random
import time

# 设置页面配置
st.set_page_config(
    page_title="我的智能学习助手",
    page_icon="🎓",
    layout="centered"
)

# 应用标题和介绍
st.title("🎓 我的个性化学习助手")
st.markdown("---")
st.write("欢迎使用你的专属AI学习伙伴！")

# 侧边栏 - 个性化设置
with st.sidebar:
    st.header("⚙️ 个性化设置")
    ai_name = st.text_input("给AI起个名字:", value="学习小助手")
    ai_style = st.selectbox(
        "选择AI风格:",
        ["温柔导师", "幽默朋友", "严谨教授", "激励教练"]
    )

# 显示聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 聊天输入
if prompt := st.chat_input("请输入你的问题..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 生成AI回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 模拟思考
        thinking_text = "🤔 正在思考中..."
        message_placeholder.markdown(thinking_text)
        time.sleep(1)
        
        # 根据风格生成回复
        responses = {
            "温柔导师": [
                f"亲爱的同学，关于'{prompt}'，让我为你详细解释...",
                f"这个问题很好！{prompt}其实可以这样理解...",
            ],
            "幽默朋友": [
                f"哈哈，{prompt}这个问题问得好！让我来告诉你...",
                f"哟，问到点子上了！{prompt}其实是这样的...",
            ],
            "严谨教授": [
                f"从专业角度分析，{prompt}涉及以下关键概念...",
                f"{prompt}这个问题需要系统性地理解...",
            ],
            "激励教练": [
                f"太棒了！你问到了{prompt}这个重要问题！",
                f"优秀的问题！{prompt}正是提升自己的关键...",
            ]
        }
        
        ai_response = random.choice(responses[ai_style])
        
        # 模拟打字效果
        full_response = ""
        for chunk in ai_response.split():
            full_response += chunk + " "
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.05)
        message_placeholder.markdown(full_response)
    
    # 添加AI回复
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 页脚
st.markdown("---")
st.markdown(f"✨ *由 {ai_name} 驱动 | 风格: {ai_style}*")
