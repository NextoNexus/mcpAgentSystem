import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
import requests
import threading
import queue
from datetime import datetime
import json
import os


class AgentClient:
    """智能体客户端"""

    def __init__(self, root, server_url="http://localhost:8000"):
        self.root = root
        self.server_url = server_url
        self.username = None
        self.is_logged_in = False
        self.current_config = None  # 存储当前配置

        # 消息队列用于线程安全更新UI
        self.message_queue = queue.Queue()

        self.setup_ui()
        self.check_messages()

    def setup_ui(self):
        """设置用户界面"""
        self.root.title("智能体客户端")
        self.root.geometry("900x700")

        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="智能体系统配置",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        # 用户名
        ttk.Label(main_frame, text="用户名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(main_frame, width=40)
        self.username_entry.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)

        # 模型名称
        ttk.Label(main_frame, text="模型名称:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_entry = ttk.Entry(main_frame, width=40)
        self.model_entry.grid(row=2, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.model_entry.insert(0, "deepseek-chat")

        # API密钥
        ttk.Label(main_frame, text="API密钥:").grid(row=3, column=0, sticky=tk.W, pady=5)
        # self.api_key_entry = ttk.Entry(main_frame, width=40, show="*")
        # self.api_key_entry.grid(row=3, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)

        # 在API密钥输入行添加提示
        api_key_frame = ttk.Frame(main_frame)
        api_key_frame.grid(row=3, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.api_key_entry = ttk.Entry(api_key_frame, width=40, show="*")
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 添加提示标签
        ttk.Label(api_key_frame, text="(支持以$开头的环境变量)",
                  font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(5, 0))

        # 模型URL源
        ttk.Label(main_frame, text="模型URL源(可选):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.base_url_entry = ttk.Entry(main_frame, width=40)
        self.base_url_entry.grid(row=4, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.base_url_entry.insert(0, "https://api.deepseek.com")

        # 系统提示词
        ttk.Label(main_frame, text="系统提示词:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        self.system_prompt_text = scrolledtext.ScrolledText(
            main_frame,
            width=40,
            height=6,
            wrap=tk.WORD
        )
        self.system_prompt_text.grid(
            row=5, column=1, columnspan=3,
            sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5
        )
        self.system_prompt_text.insert(
            "1.0",
            "你是智能助手，请友好、专业地回答用户问题。"
        )

        # 配置区域分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10
        )

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=4, pady=10)

        self.login_button = ttk.Button(
            button_frame,
            text="登录并初始化智能体",
            command=self.login,
            width=20
        )
        self.login_button.pack(side=tk.LEFT, padx=5)

        self.logout_button = ttk.Button(
            button_frame,
            text="登出",
            command=self.logout,
            width=20,
            state=tk.DISABLED
        )
        self.logout_button.pack(side=tk.LEFT, padx=5)

        self.test_connection_button = ttk.Button(
            button_frame,
            text="测试连接",
            command=self.test_connection,
            width=20
        )
        self.test_connection_button.pack(side=tk.LEFT, padx=5)

        # 状态显示
        self.status_label = ttk.Label(
            main_frame,
            text="状态: 未配置",
            foreground="red"
        )
        self.status_label.grid(row=8, column=0, columnspan=4, sticky=tk.W, pady=5)

        # 聊天区域分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
            row=9, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10
        )

        # 聊天历史区域
        ttk.Label(main_frame, text="聊天记录:", font=("Arial", 10, "bold")).grid(
            row=10, column=0, columnspan=4, sticky=tk.W, pady=5
        )

        self.chat_history = scrolledtext.ScrolledText(
            main_frame,
            width=80,
            height=15,
            state=tk.DISABLED
        )
        self.chat_history.grid(
            row=11, column=0, columnspan=4,
            sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5
        )

        # 消息输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=12, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(input_frame, text="输入消息:").pack(side=tk.LEFT, padx=(0, 5))

        # self.message_entry = ttk.Entry(input_frame, width=50)
        # self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.message_entry = tk.Text(
            input_frame,
            width=50,
            height=4,
            wrap=tk.WORD,
            state=tk.DISABLED  # 初始状态为禁用
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        # self.message_entry.bind("<Return>", lambda event: self.send_message())
        self.message_entry.config(state=tk.DISABLED)

        self.send_button = ttk.Button(
            input_frame,
            text="发送",
            command=self.send_message,
            state=tk.DISABLED,
            width=10
        )
        self.send_button.pack(side=tk.LEFT, padx=5)

        # 活跃用户区域
        user_frame = ttk.LabelFrame(main_frame, text="活跃用户", padding="5")
        user_frame.grid(row=13, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)

        self.user_listbox = tk.Listbox(user_frame, height=4)
        self.user_listbox.pack(fill=tk.BOTH, expand=True)

        self.refresh_users_button = ttk.Button(
            user_frame,
            text="刷新用户列表",
            command=self.refresh_active_users
        )
        self.refresh_users_button.pack(pady=5)

    def validate_inputs(self):
        """验证输入是否完整"""
        username = self.username_entry.get().strip()
        model_name = self.model_entry.get().strip()
        api_key = self.api_key_entry.get().strip()
        system_prompt = self.system_prompt_text.get("1.0", tk.END).strip()

        missing_fields = []
        if not username:
            missing_fields.append("用户名")
        if not model_name:
            missing_fields.append("模型名称")
        if not api_key:
            missing_fields.append("API密钥")
        if not system_prompt:
            missing_fields.append("系统提示词")

        return missing_fields

    def login(self):
        """用户登录并初始化智能体"""
        # 验证输入
        missing_fields = self.validate_inputs()
        if missing_fields:
            messagebox.showwarning("警告", f"以下字段不能为空:\n{', '.join(missing_fields)}")
            return

        username = self.username_entry.get().strip()
        model_name = self.model_entry.get().strip()
        api_key_input = self.api_key_entry.get().strip()
        base_url = self.base_url_entry.get().strip() or None
        system_prompt = self.system_prompt_text.get("1.0", tk.END).strip()

        # 处理API密钥输入：支持直接输入或环境变量
        api_key = api_key_input
        if api_key_input.startswith("$"):
            # 如果是环境变量格式，例如$OPENAI_API_KEY
            env_var = api_key_input[1:]  # 去掉$符号
            api_key = os.environ.get(env_var, "")
            if not api_key:
                messagebox.showerror("错误", f"环境变量 {env_var} 未设置或为空")
                return

        # 在后台线程中执行登录
        def do_login():
            try:
                login_data = {
                    "username": username,
                    "model_name": model_name,
                    "api_key": api_key,  # 使用处理后的API密钥
                    "base_url": base_url,
                    "system_prompt": system_prompt
                }

                response = requests.post(
                    f"{self.server_url}/login",
                    json=login_data,
                    timeout=10
                )

                if response.status_code == 200:
                    self.current_config = login_data
                    self.message_queue.put(("login_success", username))
                else:
                    error_msg = response.json().get('detail', '未知错误')
                    self.message_queue.put(("error", f"登录失败: {error_msg}"))
            except requests.exceptions.ConnectionError:
                self.message_queue.put(("error", "无法连接到服务器"))
            except requests.exceptions.Timeout:
                self.message_queue.put(("error", "连接超时"))
            except Exception as e:
                self.message_queue.put(("error", f"登录异常: {str(e)}"))

        threading.Thread(target=do_login, daemon=True).start()

    def logout(self):
        """用户登出"""
        if not self.is_logged_in:
            return

        def do_logout():
            try:
                response = requests.post(
                    f"{self.server_url}/logout/{self.username}",
                    timeout=5
                )
                self.message_queue.put(("logout_success", None))
            except Exception as e:
                self.message_queue.put(("error", f"登出失败: {str(e)}"))

        threading.Thread(target=do_logout, daemon=True).start()

    def send_message(self):
        """发送消息给智能体"""
        # 从Text控件获取内容
        message = self.message_entry.get("1.0", tk.END).strip()
        if not message:
            return

        if not self.is_logged_in:
            messagebox.showwarning("警告", "请先登录并初始化智能体")
            return

        # 显示用户消息
        self.add_to_chat_history(f"👤: {message}")

        # 清空输入框
        self.message_entry.delete("1.0", tk.END)

        # 在后台线程中发送消息
        def send_to_agent():
            try:
                response = requests.post(
                    f"{self.server_url}/chat",
                    json={
                        "username": self.username,
                        "message": message
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    self.message_queue.put(("agent_response", data["response"]))
                else:
                    error_msg = response.json().get('detail', '未知错误')
                    self.message_queue.put(("error", f"发送消息失败: {error_msg}"))
            except requests.exceptions.Timeout:
                self.message_queue.put(("error", "请求超时，请稍后重试"))
            except requests.exceptions.ConnectionError:
                self.message_queue.put(("error", "无法连接到服务器"))
            except Exception as e:
                self.message_queue.put(("error", f"发送消息异常: {str(e)}"))

        threading.Thread(target=send_to_agent, daemon=True).start()

    def test_connection(self):
        """测试服务器连接"""

        def do_test():
            try:
                response = requests.get(
                    f"{self.server_url}/health",
                    timeout=5
                )

                if response.status_code == 200:
                    self.message_queue.put(("info", "服务器连接正常"))
                else:
                    self.message_queue.put(("error", "服务器响应异常"))
            except requests.exceptions.ConnectionError:
                self.message_queue.put(("error", "无法连接到服务器"))
            except Exception as e:
                self.message_queue.put(("error", f"连接测试失败: {str(e)}"))

        threading.Thread(target=do_test, daemon=True).start()

    def refresh_active_users(self):
        """刷新活跃用户列表"""
        if not self.is_logged_in:
            messagebox.showwarning("警告", "请先登录")
            return

        def fetch_users():
            try:
                response = requests.get(f"{self.server_url}/users", timeout=5)
                if response.status_code == 200:
                    users = response.json()
                    self.message_queue.put(("update_users", users))
                else:
                    self.message_queue.put(("error", "获取用户列表失败"))
            except requests.exceptions.ConnectionError:
                self.message_queue.put(("error", "无法连接到服务器"))
            except Exception as e:
                self.message_queue.put(("error", f"获取用户列表异常: {str(e)}"))

        threading.Thread(target=fetch_users, daemon=True).start()

    def add_to_chat_history(self, message):
        """添加消息到聊天历史"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"

        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, formatted_message)
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)

    def check_messages(self):
        """检查消息队列并更新UI"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()

                if msg_type == "login_success":
                    self.handle_login_success(data)
                elif msg_type == "logout_success":
                    self.handle_logout_success()
                elif msg_type == "agent_response":
                    self.add_to_chat_history(f"🤖: {data}")
                elif msg_type == "update_users":
                    self.update_user_list(data)
                elif msg_type == "info":
                    messagebox.showinfo("信息", data)
                elif msg_type == "error":
                    messagebox.showerror("错误", data)

                self.message_queue.task_done()
        except queue.Empty:
            pass

        # 每100ms检查一次消息队列
        self.root.after(100, self.check_messages)

    def handle_login_success(self, username):
        """处理登录成功"""
        self.username = username
        self.is_logged_in = True

        # 更新UI状态
        self.username_entry.config(state=tk.DISABLED)
        self.model_entry.config(state=tk.DISABLED)
        self.api_key_entry.config(state=tk.DISABLED)
        self.base_url_entry.config(state=tk.DISABLED)
        self.system_prompt_text.config(state=tk.DISABLED)

        self.login_button.config(state=tk.DISABLED)
        self.logout_button.config(state=tk.NORMAL)

        self.message_entry.config(state=tk.NORMAL)
        # 将焦点设置到输入框
        self.message_entry.focus_set()

        self.send_button.config(state=tk.NORMAL)

        # 判断API密钥类型
        api_key_display = "直接输入"
        if self.api_key_entry.get().strip().startswith("$"):
            api_key_display = "环境变量"

        self.status_label.config(
            text=f"状态: 已登录 ({username}) | 模型: {self.current_config['model_name']} | API: {api_key_display}",
            foreground="green"
        )

        # 清空聊天历史
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.delete(1.0, tk.END)
        self.chat_history.config(state=tk.DISABLED)

        # 获取活跃用户列表
        self.refresh_active_users()

        # 显示配置信息
        config_info = f"配置信息:\n"
        config_info += f"  模型: {self.current_config['model_name']}\n"
        config_info += f"  URL源: {self.current_config['base_url'] or '默认'}\n"
        config_info += f"  提示词: {self.current_config['system_prompt'][:50]}..."

        self.add_to_chat_history(f"智能体已初始化\n{config_info}")

        messagebox.showinfo("登录成功", f"欢迎 {username}!\n智能体已成功初始化")

    def handle_logout_success(self):
        """处理登出成功"""
        self.username = None
        self.is_logged_in = False
        self.current_config = None

        # 更新UI状态
        self.username_entry.config(state=tk.NORMAL)
        self.model_entry.config(state=tk.NORMAL)
        self.api_key_entry.config(state=tk.NORMAL)
        self.base_url_entry.config(state=tk.NORMAL)
        self.system_prompt_text.config(state=tk.NORMAL)

        self.login_button.config(state=tk.NORMAL)
        self.logout_button.config(state=tk.DISABLED)

        self.message_entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)

        self.status_label.config(text="状态: 未配置", foreground="red")

        # 清空用户列表
        self.user_listbox.delete(0, tk.END)

        # 添加登出消息到聊天历史
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, "\n[系统] 已登出，智能体会话已关闭\n")
        self.chat_history.config(state=tk.DISABLED)

        messagebox.showinfo("登出成功", "已成功登出，智能体会话已关闭")

    def update_user_list(self, users):
        """更新用户列表"""
        self.user_listbox.delete(0, tk.END)
        if not users:
            self.user_listbox.insert(tk.END, "暂无其他活跃用户")
            return

        for user in users:
            status = "活跃" if user["is_active"] else "非活跃"
            user_info = f"{user['username']} - {user['model_name']} ({status})"
            self.user_listbox.insert(tk.END, user_info)


def main():
    """主函数"""
    root = tk.Tk()

    # 设置服务器URL
    server_url = "http://localhost:8000"

    # 创建客户端
    client = AgentClient(root, server_url)

    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()