import os.path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import asyncio
from datetime import datetime
import sys
import signal
from pydantic import BaseModel, Field

from agent_manager import AgentManager, AgentConfig
from utils import LoginValidater


# 数据模型
class UserLogin(BaseModel):
    username: str
    password: str
    model_name: str = Field(..., description="模型名称，如 gpt-3.5-turbo")
    api_key: str = Field(..., description="API密钥")
    base_url: Optional[str] = Field(None, description="模型API基础URL")
    system_prompt: str = Field(..., description="系统提示词")


class UserMessage(BaseModel):
    username: str
    message: str


class AgentResponse(BaseModel):
    response: str
    timestamp: str


class UserInfo(BaseModel):
    username: str
    model_name: str
    is_active: bool
    last_active: str


# 初始化应用和智能体管理器
app = FastAPI(title="智能体服务端")
agent_manager = AgentManager()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 登录端点
@app.post("/login")
async def login(user: UserLogin):
    """用户登录"""
    if not user.username:
        raise HTTPException(status_code=400, detail="用户名不能为空")

    # 验证所有必需字段
    validation_errors = []
    if not user.model_name:
        validation_errors.append("模型名称")
    if not user.api_key:
        validation_errors.append("API密钥")
    if not user.system_prompt:
        validation_errors.append("系统提示词")

    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail=f"以下字段不能为空: {', '.join(validation_errors)}"
        )

    # 登陆验证
    validater = LoginValidater('dgjt', 'postgres', '123456', 'localhost', '5432', 'schema_user.user_login')
    res = validater.connect_db()
    print()
    if not res: raise HTTPException(status_code=500, detail=f"连接数据库失败，请与管理员联系")
    (pass_usr, pass_pwd) = validater.validate_login(user.username, user.password)
    if not pass_usr:
        raise HTTPException(status_code=400, detail='用户名不存在，请与管理员联系')
    elif not pass_pwd:
        raise HTTPException(status_code=400, detail='密码错误，请与管理员联系')

    # 验证通过
    # 检查用户是否已在其他位置登录
    existing_session = agent_manager.get_session(user.username)
    if existing_session and existing_session.is_active:
        # 关闭现有会话（允许新登录）
        agent_manager.close_session(user.username)

    # 创建智能体配置
    # 基本工具函数
    mcp_configs = [
        './config/mcp_config_base.json',
        './config/mcp_config_office.json'
    ]
    # 管理员可以额外拥有一些工具函数
    if user.username == 'admin':
        mcp_configs.append('./config/mcp_config_map.json')

    agent_config = AgentConfig(
        model_name=user.model_name,
        api_key=user.api_key,
        base_url=user.base_url,
        system_prompt=user.system_prompt,
        workspace_root=os.path.abspath('../workspace'),
        mcp_configs=mcp_configs
    )

    try:
        # 创建新会话
        session = agent_manager.create_session(user.username, agent_config)
        return {
            "message": f"用户 {user.username} 登录成功",
            "session_created": True,
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


# 登出端点
@app.post("/logout/{username}")
async def logout(username: str):
    """用户登出"""
    agent_manager.close_session(username)
    return {"message": f"用户 {username} 已登出"}


# 发送消息给智能体
@app.post("/chat", response_model=AgentResponse)
async def chat(user_message: UserMessage):
    print('message:',user_message.message)
    """与智能体对话"""
    # 获取用户会话
    session = agent_manager.get_session(user_message.username)
    if not session:
        raise HTTPException(status_code=404, detail="用户会话不存在，请重新登录")

    if not session.agent:
        raise HTTPException(status_code=500, detail="智能体未正确初始化")

    # 更新活跃时间
    agent_manager.update_last_active(user_message.username)

    try:
        # 使用智能体处理消息
        # print('聊天记录长度：', len(session.history_context))
        result = await session.agent.run(user_message.message, message_history=session.history_context)
        session.history_context = list(result.all_messages())
        response_text = result.output

        return AgentResponse(
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能体处理错误: {str(e)}")


# 获取活跃用户列表
@app.get("/users", response_model=List[UserInfo])
async def get_active_users():
    """获取所有活跃用户"""
    users = []
    for username, session in agent_manager.sessions.items():
        users.append(UserInfo(
            username=username,
            model_name=session.agent_config.model_name,
            is_active=session.is_active,
            last_active=datetime.fromtimestamp(session.last_active).isoformat()
        ))
    return users


# 获取用户配置信息
@app.get("/user_config/{username}")
async def get_user_config(username: str):
    """获取用户配置信息"""
    session = agent_manager.get_session(username)
    if not session:
        raise HTTPException(status_code=404, detail="用户会话不存在")

    return {
        "username": username,
        "model_name": session.agent_config.model_name,
        "base_url": session.agent_config.base_url,
        "system_prompt": session.agent_config.system_prompt[:100] + "..." if len(
            session.agent_config.system_prompt) > 100 else session.agent_config.system_prompt
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "active_users": len(agent_manager.sessions),
        "timestamp": datetime.now().isoformat()
    }


# 清理任务
async def cleanup_task():
    """清理不活跃会话的后台任务"""
    while True:
        await asyncio.sleep(300)  # 每5分钟清理一次
        agent_manager.cleanup_inactive_sessions(timeout=1800)  # 30分钟超时


@app.on_event("startup")
async def startup_event():
    """启动时初始化清理任务"""
    asyncio.create_task(cleanup_task())


def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    print("\n正在关闭服务端...")
    sys.exit(0)


if __name__ == "__main__":
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 50)
    print("智能体服务端")
    print("=" * 50)
    print("服务端运行在: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)

    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"服务启动失败: {e}")
        sys.exit(1)
