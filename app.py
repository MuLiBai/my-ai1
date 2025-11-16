import streamlit as st
import requests
import time

# 页面配置
st.set_page_config(
    page_title="小杨同学",
    page_icon="🧠",
    layout="centered"
)

# 安全获取API密钥
def get_api_key():
    """从Secrets或用户输入获取API密钥"""
    
    # 优先使用Secrets中的密钥（生产环境）
    if 'ZHIPU_API_KEY' in st.secrets:
        return st.secrets['ZHIPU_API_KEY']
    
    # 其次使用session state（用户已在当前会话中输入）
    elif 'user_api_key' in st.session_state and st.session_state.user_api_key:
        return st.session_state.user_api_key
    
    # 最后返回None，提示用户输入
    else:
        return None

# 侧边栏设置
with st.sidebar:
    st.header("⚙️ 个性化设置")
    ai_name = st.text_input("给AI起个名字:", value="学习小助手")
    ai_style = st.selectbox(
        "选择AI风格:",
        ["温柔导师", "幽默朋友", "严谨教授", "激励教练"]
    )
with st.sidebar:
    st.header("🔑 API设置")
    
    # 显示当前密钥状态
    secrets_key = st.secrets.get("ZHIPU_API_KEY")
    if secrets_key:
        st.success("✅ 检测到Secrets中的API密钥")
        st.code("密钥已安全存储", language="text")
    else:
        st.warning("⚠️ 未检测到Secrets密钥")
    
    # 用户手动输入（用于测试或覆盖）
    user_key = st.text_input(
        "手动输入API密钥（可选）:",
        type="password",
        placeholder="如需覆盖Secrets密钥，请在此输入",
        key="user_api_key_input"
    )
    
    if user_key:
        st.session_state.user_api_key = user_key
        st.success("✅ 手动密钥已设置")


# 获取最终使用的API密钥
api_key = get_api_key()

if not api_key:
    st.error("""
    ❌ 未设置API密钥
    
    请通过以下方式之一设置：
    1. **推荐**：在Streamlit Cloud的Secrets中设置 ZHIPU_API_KEY
    2. **临时**：在左侧边栏手动输入API密钥
    """)
    st.stop()

# 智谱AI调用函数
def call_zhipu_ai(prompt, conversation_history):
    """调用智谱AI API"""
    
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建消息
    messages = conversation_history + [{"role": "user", "content": prompt}]
    
    data = {
        "model": "glm-3-turbo",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": st.secrets.get("MAX_TOKENS", 500)  # 使用Secrets中的配置或默认值
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"], "success"
        else:
            error_msg = f"API错误: {response.status_code}"
            if response.status_code == 401:
                error_msg += " - API密钥无效"
            elif response.status_code == 429:
                error_msg += " - 请求频率超限"
            return error_msg, "error"
    except Exception as e:
        return f"请求失败: {str(e)}", "error"

# 应用主界面
st.title("小杨同学")

# 显示应用名称（从Secrets获取或使用默认值）
app_name = st.secrets.get("APP_NAME", "AI聊天助手")
st.caption(f"应用: {app_name}")

# 聊天界面代码...
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("输入消息..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("思考中...")
        
        response, status = call_zhipu_ai(prompt, st.session_state.messages)
        
        if status == "success":
            full_response = ""
            for chunk in response.split():
                full_response += chunk + " "
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.03)
            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            st.error(response)

# 调试信息（仅在开发时显示）
with st.expander("🔧 调试信息"):
    st.write("API密钥状态:", "已设置" if api_key else "未设置")
    st.write("密钥来源:", "Secrets" if 'ZHIPU_API_KEY' in st.secrets else "手动输入")
    st.write("Secrets中的所有键:", list(st.secrets.keys()))
st.markdown("---")
st.markdown(f"✨ *由 {ai_name} 驱动 | 风格: {ai_style}
