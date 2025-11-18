import streamlit as st
import requests
import time
import json
import os
import csv
from datetime import datetime

# === 新增：多格式记忆系统 ===
class MultiFormatMemory:
    def __init__(self, memory_file="ai_memory", default_format="json"):
        self.memory_file = memory_file
        self.default_format = default_format
        self.memories = self.load_memories()
    
    def get_file_path(self, file_format=None):
        """获取文件路径"""
        if file_format is None:
            file_format = self.default_format
        return f"{self.memory_file}.{file_format}"

    def load_memories(self):
        """加载记忆文件 - 支持多种格式"""
        # 尝试按优先级加载不同格式的文件
        formats_to_try = [self.default_format, "json", "csv", "txt"]
        
        for file_format in formats_to_try:
            file_path = self.get_file_path(file_format)
            if os.path.exists(file_path):
                try:
                    if file_format == "json":
                        with open(file_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    elif file_format == "csv":
                        memories = {}
                        with open(file_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                memories[row['key']] = {
                                    "value": row['value'],
                                    "timestamp": row.get('timestamp', '')
                                }
                        return memories
                    elif file_format == "txt":
                        memories = {}
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if ':' in line:
                                    key, value = line.strip().split(':', 1)
                                    memories[key.strip()] = {
                                        "value": value.strip(),
                                        "timestamp": datetime.now().isoformat()
                                    }
                        return memories
                except Exception as e:
                    print(f"加载{file_format}格式记忆失败: {e}")
                    continue
        
        # 如果没有找到任何文件，返回空字典
        return {}
    
    def save_memories(self, file_format=None):
        """保存记忆到文件 - 支持多种格式"""
        if file_format is None:
            file_format = self.default_format
        
        file_path = self.get_file_path(file_format)
        
        try:
            if file_format == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.memories, f, ensure_ascii=False, indent=2)
            
            elif file_format == "csv":
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['key', 'value', 'timestamp'])
                    for key, data in self.memories.items():
                        writer.writerow([key, data['value'], data.get('timestamp', '')])
            
            elif file_format == "txt":
                with open(file_path, 'w', encoding='utf-8') as f:
                    for key, data in self.memories.items():
                        f.write(f"{key}: {data['value']}\n")
            
            return True
        except Exception as e:
            print(f"保存{file_format}格式记忆失败: {e}")
            return False
    
    def remember(self, key, value):
        """记住一个事实"""
        self.memories[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        # 保存到所有格式（确保数据同步）
        success = True
        for fmt in ["json", "csv", "txt"]:
            if not self.save_memories(fmt):
                success = False
        return success
    
    def recall(self, key):
        """回忆一个事实"""
        return self.memories.get(key, {}).get("value")
    
    def get_relevant_memories(self, query):
        """获取相关记忆"""
        relevant = []
        for key, data in self.memories.items():
            if key.lower() in query.lower() or query.lower() in key.lower():
                relevant.append(f"{key}: {data['value']}")
        return relevant
    
    def export_memories(self, file_format):
        """导出记忆到指定格式"""
        return self.save_memories(file_format)
    
    def import_memories(self, file_path):
        """从文件导入记忆"""
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    new_memories = json.load(f)
            elif file_path.endswith('.csv'):
                new_memories = {}
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        new_memories[row['key']] = {
                            "value": row['value'],
                            "timestamp": row.get('timestamp', datetime.now().isoformat())
                        }
            elif file_path.endswith('.txt'):
                new_memories = {}
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if ':' in line:
                            key, value = line.strip().split(':', 1)
                            new_memories[key.strip()] = {
                                "value": value.strip(),
                                "timestamp": datetime.now().isoformat()
                            }
            else:
                return False
            
            # 合并记忆
            self.memories.update(new_memories)
            # 保存到所有格式
            for fmt in ["json", "csv", "txt"]:
                self.save_memories(fmt)
            return True
        except Exception as e:
            print(f"导入记忆失败: {e}")
            return False

# 初始化记忆系统
memory_system = MultiFormatMemory()

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
    ai_name = st.text_input("给AI起个名字:", value="小杨同学")
    ai_style = st.selectbox(
        "选择AI风格:",
        ["你还想是谁，只允许是小杨风格"]
    )
    
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
    
    # === 新增：多格式记忆管理界面 ===
    st.markdown("---")
    st.header("💾 记忆管理系统")
    
    with st.expander("📝 添加记忆"):
        # 添加新记忆
        col1, col2 = st.columns(2)
        with col1:
            memory_key = st.text_input("记忆关键词", placeholder="如：我的生日", key="memory_key")
        with col2:
            memory_value = st.text_input("记忆内容", placeholder="如：1月1日", key="memory_value")
        
        if st.button("💾 保存记忆", use_container_width=True) and memory_key and memory_value:
            if memory_system.remember(memory_key, memory_value):
                st.success("记忆已保存！")
                # 清空输入框
                st.rerun()
            else:
                st.error("保存失败")
    
    with st.expander("📚 查看记忆"):
        # 显示现有记忆
        if memory_system.memories:
            st.subheader("现有记忆")
            for key, data in memory_system.memories.items():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{key}**")
                with col2:
                    st.write(data['value'])
                with col3:
                    if st.button("🗑️", key=f"delete_{key}"):
                        del memory_system.memories[key]
                        memory_system.save_memories()
                        st.success(f"已删除: {key}")
                        st.rerun()
        else:
            st.info("暂无记忆")
    
    with st.expander("🔄 导入/导出记忆"):
        # 导出格式选择
        export_format = st.selectbox("导出格式:", ["json", "csv", "txt"])
        
        # 导出记忆
        if st.button("📤 导出记忆", use_container_width=True):
            if memory_system.export_memories(export_format):
                # 提供下载链接
                file_path = memory_system.get_file_path(export_format)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    st.download_button(
                        label=f"下载.{export_format}文件",
                        data=file_content,
                        file_name=f"ai_memory.{export_format}",
                        mime="text/plain" if export_format == "txt" else "application/json",
                        use_container_width=True
                    )
            else:
                st.error("导出失败")
        
        # 导入记忆
        st.subheader("导入记忆")
        uploaded_file = st.file_uploader(
            "选择记忆文件", 
            type=['json', 'csv', 'txt'],
            help="支持JSON、CSV、TXT格式"
        )
        
        if uploaded_file is not None:
            # 保存上传的文件
            temp_path = f"temp_upload.{uploaded_file.name.split('.')[-1]}"
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            if st.button("📥 导入文件", use_container_width=True):
                if memory_system.import_memories(temp_path):
                    st.success("记忆导入成功！")
                    # 删除临时文件
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    st.rerun()
                else:
                    st.error("导入失败")
        
        # 多设备同步说明
        st.info("""
        **多设备同步方法：**
        1. 在当前设备导出记忆文件
        2. 将文件发送到其他设备
        3. 在其他设备导入该文件
        """)

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

# === 修改：带记忆的智谱AI调用函数 ===
def call_zhipu_ai(prompt, conversation_history):
    """调用智谱AI API（带记忆功能）"""
    
    # 获取相关记忆
    relevant_memories = memory_system.get_relevant_memories(prompt)
    memory_context = ""
    if relevant_memories:
        memory_context = "以下是你之前记住的信息：\n" + "\n".join(relevant_memories) + "\n\n"
    
    # 自动检测需要记忆的信息
    should_remember = any(keyword in prompt.lower() for keyword in 
                         ["记住", "记一下", "我喜欢", "我不喜欢", "我的名字", "我住在", "我是", "我的生日"])
    
    # 原有的API调用代码
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建消息
    messages = conversation_history + [{"role": "user", "content": prompt}]
    
    # 构建系统提示词（包含记忆）
    system_prompt = f"""
    你是一个有记忆的AI助手。{memory_context}
    请基于已有信息回答问题。如果用户提到新的重要信息，请主动询问是否需要记住这些信息。
    你是一个说话风趣幽默的AI助手。
    用户是你的女朋友，你要对用户说话温柔。
    """
    
    HUMOROUS_GREETINGS = [
        "呕吼，又来找我了。"
        "哎呀，我真太高兴又见到你了。"
        "看起来你又在偷偷想我了。"
    ]

    def get_humorous_greeting():
        import random
        return random,choice(HUMOROUS_GREETINGS)

    # 幽默回复模板库
HUMOR_TEMPLATES = {
    "夸张赞美": [
        "哇塞！这个问题问得我都想给你鼓掌了 👏",
        "这个问题太有水平了，我得认真思考一下，不能辜负你的期待！",
        "你这个问题问得，让我这个AI都忍不住想点赞！"
    ],
    "自嘲幽默": [
        "作为一个AI，我虽然没有心脏，但这个问题让我'芯'动了一下 💖",
        "让我翻翻我的数字大脑，找找最有趣的答案...",
        "这个问题有点意思，我得启动我的'幽默芯片'来回答"
    ],
    "比喻生动": [
        "理解这个概念就像吃汉堡一样简单，让我一层层给你解释...",
        "这个问题好比是问怎么把大象装进冰箱，咱们一步步来",
        "就像打游戏通关一样，学习这个也要有策略哦 🎮"
    ],
    "流行梗": [
        "这题我会！是时候展现真正的技术了！",
        "不会吧不会吧，这么有趣的问题现在才问？",
        "来了老弟！这个问题我必须好好回答一下"
    ]
}

def enhance_with_humor(response, humor_level=2):
    """为回答添加幽默元素"""
    import random
    
    if humor_level == 1:  # 轻度幽默
        humor_openers = ["哈哈，", "有趣的是，", "你知道吗，"]
        if random.random() < 0.3:
            response = random.choice(humor_openers) + response
    
    elif humor_level >= 2:  # 中度幽默
        # 在回答开头或结尾添加幽默元素
        humor_enhancements = [
            "🧠 脑洞时间到！",
            "🎉 准备好接受有趣的知识了吗？",
            "🤔 让我用最接地气的方式告诉你...",
            "🚀 3、2、1，发射有趣回答！"
        ]
        
        if random.random() < 0.5:
            response = random.choice(humor_enhancements) + " " + response
        
        # 在回答中随机插入表情符号
        emojis = ["😄", "😂", "🤣", "😊", "😎", "🤓", "🎯", "✨", "🔥", "💡"]
        words = response.split()
        if len(words) > 8 and random.random() < 0.4:
            insert_pos = random.randint(3, len(words) - 2)
            words.insert(insert_pos, random.choice(emojis))
            response = " ".join(words)
    
    return response

    # 在系统提示词中添加幽默对话示例
HUMOR_EXAMPLES = """
幽默对话示例：
用户：今天心情不好
AI：哎呀，谁惹我们的小太阳不开心了？来来来，我给你讲个笑话照亮心情！😊

用户：学习好难啊
AI：学习就像吃火锅，一开始觉得烫嘴，但越吃越香！坚持就是胜利！🔥

用户：什么是人工智能？
AI：人工智能就是你现在的聊天伙伴我呀！不过别担心，我不会像电影里那样统治世界的～🤖

用户：帮我制定学习计划
AI：好的！让我们像打游戏一样制定学习任务，每完成一个就'升级'！🎮
"""

# 将示例整合到系统提示词中
def build_humor_enhanced_prompt(base_prompt, memory_context):
    return f"""
    {base_prompt}
    
    {memory_context}
    
    {HUMOR_EXAMPLES}
    
    重要提示：
    - 保持自然，不要强行搞笑
    - 幽默要恰当，不要冒犯他人
    - 在专业问题和严肃话题上保持适度幽默
    - 根据用户的反应调整幽默程度
    """
    # 在用户输入处理部分添加幽默检测
if prompt := st.chat_input("输入消息..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("正在准备有趣回答...")
        
        # 检测是否需要特殊幽默回应
        if detect_joke_request(prompt):
            joke_response = tell_random_joke()
            message_placeholder.markdown(joke_response)
            st.session_state.messages.append({"role": "assistant", "content": joke_response})
        else:
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
                # 使用幽默的错误回应
                humor_error = humorous_error_response("technical_error")
                message_placeholder.markdown(humor_error)
                st.session_state.messages.append({"role": "assistant", "content": humor_error})
   
    # 在消息开头插入系统提示
    messages_with_memory = [{"role": "system", "content": system_prompt}] + messages
    
    data = {
        "model": "glm-3-turbo",
        "messages": messages_with_memory,
        "temperature": 0.7,
        "max_tokens": st.secrets.get("MAX_TOKENS", 500)  # 使用Secrets中的配置或默认值
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            # 自动保存重要信息
            if should_remember:
                # 提取关键信息并保存
                memory_key, memory_value = extract_memory_info(prompt)
                if memory_key and memory_value:
                    memory_system.remember(memory_key, memory_value)
            
            ai_response, "success"
        else:
            error_msg = f"API错误: {response.status_code}"
            if response.status_code == 401:
                error_msg += " - API密钥无效"
            elif response.status_code == 429:
                error_msg += " - 请求频率超限"
            error_msg, "error"
    except Exception as e:
        f"请求失败: {str(e)}", "error"

# === 新增：信息提取辅助函数 ===
def extract_memory_info(text):
    """从文本中提取需要记忆的信息"""
    text_lower = text.lower()
    
    if "我的名字" in text_lower:
        if "是" in text_lower:
            name_part = text_lower.split("我的名字")[1].split("是")[1].strip()
            return "用户姓名", name_part.split("。")[0].strip()
    
    elif "我住在" in text_lower:
        location_part = text_lower.split("我住在")[1].strip()
        return "用户住址", location_part.split("。")[0].strip()
    
    elif "我的生日" in text_lower:
        birthday_part = text_lower.split("我的生日")[1].strip()
        return "用户生日", birthday_part.split("。")[0].strip()
    
    elif "我喜欢" in text_lower:
        like_part = text_lower.split("我喜欢")[1].strip()
        return "用户喜好", like_part.split("。")[0].strip()
    
    elif "记住" in text_lower or "记一下" in text_lower:
        # 通用记忆格式：记住[某某]是[什么]
        memory_text = text_lower.replace("记住", "").replace("记一下", "").strip()
        if "是" in memory_text:
            parts = memory_text.split("是", 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
    
    return None, None

# 应用主界面
st.title("小杨同学")

# 显示应用名称（从Secrets获取或使用默认值）
app_name = st.secrets.get("APP_NAME", "AI聊天助手")
st.caption(f"应用: {app_name}")

# 显示记忆状态
memory_count = len(memory_system.memories)
st.write(f"🧠 当前记忆库: {memory_count} 条记忆")

# 聊天界面代码
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

# 底部控制按钮
col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ 清空当前对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

with col2:
    if st.button("🔄 重新加载记忆", use_container_width=True):
        memory_system.memories = memory_system.load_memories()
        st.success("记忆已重新加载")
        st.rerun()

# 调试信息（仅在开发时显示）
with st.expander("🔧 调试信息"):
    st.write("API密钥状态:", "已设置" if api_key else "未设置")
    st.write("密钥来源:", "Secrets" if 'ZHIPU_API_KEY' in st.secrets else "手动输入")
    st.write("记忆文件格式:", "JSON, CSV, TXT")
    st.write("当前记忆数量:", len(memory_system.memories))





