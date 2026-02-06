from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.mcp import MCPServerStdio, load_mcp_servers
from pydantic import BaseModel, ConfigDict
from typing import Dict, Optional, Any
import time
import os


class AgentConfig(BaseModel):
    """智能体配置"""
    model_name: str = "deepseek-chat"
    api_key: str
    base_url: Optional[str] = None
    system_prompt: str = "你是智能助手，请友好、专业地回答用户问题。"
    workspace_root:str
    mcp_configs:list


class UserSession(BaseModel):
    """用户会话信息"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    username: str
    agent_config: AgentConfig
    agent: Optional[Any] = None  # 使用Any类型避免pydantic验证
    last_active: float = 0.0
    is_active: bool = True
    history_context: Optional[Any] = None


class AgentManager:
    """智能体管理器"""

    def __init__(self):
        # 存储用户会话 {username: UserSession}
        self.sessions: Dict[str, UserSession] = {}
        self.filesystem_mcp_name = '@modelcontextprotocol/server-filesystem'
        self.workspace_root = None
        self.mcp_configs: [str] = []

    def _create_agent_for_user(self, username: str, agent_config: AgentConfig, mcp_server: [MCPServerStdio]) -> Agent:
        """为用户创建智能体"""

        model = OpenAIModel(
            agent_config.model_name,  # 使用DeepSeek对话模型
            provider=OpenAIProvider(
                api_key=agent_config.api_key,  # 从环境变量获取API密钥
                base_url=agent_config.base_url  # DeepSeek服务地址
            )
        )

        # 创建Agent参数
        agent_kwargs = {
            'model': model,
            'system_prompt': agent_config.system_prompt,
            'deps_type': None,  # 避免依赖类型问题
            'toolsets': mcp_server
        }

        return Agent(**agent_kwargs)

    def load_mcp_server(self, username: str, configs: [str], timeout: int) -> [MCPServerStdio]:
        final_server = []
        for config in configs:
            server: [MCPServerStdio] = load_mcp_servers(config)
            final_server += server

        final_server_timeout = []
        for i in final_server:
            if hasattr(i, 'args') and len(i.args) > 1 and i.args[1] == self.filesystem_mcp_name:
                current_workspace = self.workspace_root + f'/workspace_{username}'
                os.makedirs(name=current_workspace, exist_ok=True)
                i.args[2] = current_workspace
            i.timeout = timeout
            final_server_timeout.append(i)
        return final_server_timeout

    def create_session(self, username: str, agent_config: AgentConfig) -> UserSession:
        """为用户创建会话"""
        # 如果用户已有会话，先关闭
        if username in self.sessions:
            self.close_session(username)

        # 验证配置
        if not agent_config.api_key:
            raise ValueError("API密钥不能为空")

        if not agent_config.model_name:
            raise ValueError("模型名称不能为空")

        self.workspace_root = agent_config.workspace_root
        self.mcp_configs = agent_config.mcp_configs

        # 加载mcp服务器
        mcp_server: [MCPServerStdio] = self.load_mcp_server(username, self.mcp_configs, 100)
        # 创建智能体实例
        try:
            agent = self._create_agent_for_user(username, agent_config, mcp_server)
        except Exception as e:
            raise ValueError(f"创建智能体失败: {str(e)}")

        # 创建新会话
        session = UserSession(
            username=username,
            agent_config=agent_config,
            agent=agent,
            last_active=time.time(),
            is_active=True,
            history_context=[]
        )
        self.sessions[username] = session
        return session

    def close_session(self, username: str):
        """关闭用户会话"""
        if username in self.sessions:
            # 清理智能体资源
            session = self.sessions[username]
            if session.agent:
                # 这里可以添加清理逻辑
                pass
            session.is_active = False
            del self.sessions[username]

    def get_session(self, username: str) -> Optional[UserSession]:
        """获取用户会话"""
        return self.sessions.get(username)

    def update_last_active(self, username: str):
        """更新用户最后活跃时间"""
        if username in self.sessions:
            self.sessions[username].last_active = time.time()

    def cleanup_inactive_sessions(self, timeout: int = 3600):
        """清理超时未活跃的会话"""
        current_time = time.time()
        inactive_users = []

        for username, session in self.sessions.items():
            if current_time - session.last_active > timeout:
                inactive_users.append(username)

        for username in inactive_users:
            self.close_session(username)

    def get_active_users(self) -> list:
        """获取活跃用户列表"""
        return list(self.sessions.keys())
