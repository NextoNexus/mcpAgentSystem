# 智能体系统（Agent System）

## 项目简介

本项目是一个基于 Python 和 FastAPI 构建的智能体系统，包含客户端和服务端两部分。客户端使用 Tkinter 实现图形化界面，服务端则通过 FastAPI 提供 RESTful API 接口。系统支持用户登录、智能体会话管理、多用户聊天以及 MCP（Model Context Protocol）工具集成。

---

## 技术栈

### 后端（服务端）
- **FastAPI**：用于构建高性能的 RESTful API。
- **Pydantic AI**：用于定义智能体模型和配置。
- **OpenAI Provider**：支持调用 DeepSeek 等大语言模型。
- **PostgreSQL**：用于用户登录验证的数据库存储。
- **MCP Server**：支持加载外部工具（如文件系统、办公工具等）。
- **Uvicorn**：作为 ASGI 服务器运行 FastAPI 应用。
- **AsyncIO**：实现异步任务处理，如定时清理不活跃会话。

### 前端（客户端）
- **Tkinter**：Python 内置 GUI 库，用于构建桌面客户端。
- **Requests**：用于与服务端进行 HTTP 通信。
- **Threading**：实现多线程操作，确保 UI 不阻塞。

### 其他依赖
- **Pydantic**：用于数据校验和序列化。
- **JSON**：配置文件解析与管理。
- **OS/Pathlib**：路径管理和工作目录操作。

---

## 功能特性

### 客户端功能
1. **用户登录与登出**
   - 支持用户名、模型名称、API 密钥、系统提示词等配置。
   - 支持通过环境变量传递 API 密钥。
2. **智能体初始化**
   - 登录成功后自动初始化智能体实例。
   - 显示当前配置信息（模型名称、URL 源、提示词等）。
3. **聊天交互**
   - 用户可向智能体发送消息并接收响应。
   - 聊天记录实时显示，并带有时间戳。
4. **活跃用户查看**
   - 可查看当前在线用户的列表及其状态。
5. **连接测试**
   - 测试客户端与服务端之间的网络连接。

### 服务端功能
1. **用户认证**
   - 通过 PostgreSQL 数据库存储和验证用户凭据。
2. **会话管理**
   - 为每个用户创建独立的智能体会话。
   - 自动清理长时间未活跃的会话。
3. **MCP 工具集成**
   - 支持动态加载多种 MCP 工具（如文件系统、地图工具等）。
   - 管理员用户可额外访问高级工具。
4. **RESTful API**
   - 提供 `/login`、`/logout`、`/chat`、`/users` 等接口。
   - 支持跨域请求（CORS）。

---

## 目录结构
agentSystem/
├── client/
│   └── remoteAgentClient.py      # 客户端主程序
├── server/
│   ├── main.py                   # 服务端主程序
│   ├── agent_manager.py          # 智能体管理器
│   ├── utils.py                  # 工具函数（如数据库连接）
│   └── config/                   # MCP 配置文件目录
│       ├── mcp_config_base.json
│       ├── mcp_config_office.json
│       └── mcp_config_map.json
└── workspace/                    # 用户工作空间目录

---

## 部署指南

### 环境准备
1. **Python 版本**
   - 推荐使用 Python 3.9 或更高版本。
2. **安装依赖**
   ```bash
   pip install fastapi uvicorn pydantic-ai openai psycopg2-binary requests
   ```
3. **PostgreSQL 数据库**
   - 创建数据库 `dgjt` 并导入用户表 `schema_user.user_login`。
   - 表结构示例：
     ```sql
     CREATE TABLE schema_user.user_login (
         username VARCHAR(50) PRIMARY KEY,
         password VARCHAR(100)
     );
     ```
4. **补充**
   - 采用JavaScript编写的mcp服务器如果需要本地部署则需要用npm install ...安装npm库。

### 启动服务端
1. 进入 `server/` 目录：
   ```bash
   cd server
   ```
2. 启动服务端：
   ```bash
   python main.py
   ```
3. 默认监听地址：`http://localhost:8000`

### 启动客户端
1. 进入 `client/` 目录：
   ```bash
   cd client
   ```
2. 启动客户端：
   ```bash
   python remoteAgentClient.py
   ```

---

## 使用说明

### 客户端操作流程
1. 输入用户名、模型名称、API 密钥等信息。
2. 点击“登录并初始化智能体”按钮完成登录。
3. 在聊天区域输入消息并与智能体交互。
4. 可随时点击“登出”结束会话。

### 服务端 API 示例
#### 登录接口
```bash
POST /login
Content-Type: application/json

{
  "username": "testuser",
  "password": "123456",
  "model_name": "deepseek-chat",
  "api_key": "$DEEPSEEK_API_KEY",
  "system_prompt": "你是智能助手，请友好、专业地回答用户问题。"
}
```

#### 发送消息
```bash
POST /chat
Content-Type: application/json

{
  "username": "testuser",
  "message": "你好！"
}
```

#### 查看活跃用户
```bash
GET /users
```

---

## 注意事项
1. **安全性**
   - 生产环境中应避免硬编码数据库密码，建议使用环境变量或配置文件。
   - API 密钥可通过 `$` 符号引用环境变量，增强安全性。
2. **性能优化**
   - 对于高并发场景，建议使用 Gunicorn 或类似的 WSGI 服务器替代 Uvicorn。
3. **扩展性**
   - 可通过增加 MCP 配置文件扩展更多工具功能。

---

## 贡献与反馈
如有问题或改进建议，请提交 Issue 或 Pull Request。感谢您的支持！

---
```
