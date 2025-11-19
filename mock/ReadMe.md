# Mock API 服务

一个基于Flask的Mock API服务，支持通过配置文件动态定义接口、入参验证和返回值模板，方便进行API接口测试和开发。

## 功能特性

- ✅ **配置文件驱动**：所有接口定义、入参、返回值都通过配置文件管理
- ✅ **动态路由注册**：根据配置文件自动注册所有接口路由
- ✅ **模板变量支持**：响应数据支持动态模板变量替换
- ✅ **请求验证**：支持配置必需的请求头、查询参数、请求体字段
- ✅ **请求日志**：可配置是否记录请求日志，方便调试
- ✅ **CORS支持**：默认启用跨域请求支持
- ✅ **错误处理**：完善的错误处理和错误信息返回

## 快速开始

### 1. 安装依赖

```bash
pip install flask flask-cors
```

或者使用项目自带的依赖管理：

```bash
# 如果使用uv
uv sync

# 如果使用pip
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python main.py
```

服务默认启动在 `http://localhost:8011`

## 配置文件说明

配置文件为 `config.json`，采用JSON格式。配置文件包含以下主要部分：

### 配置文件结构

```json
{
  "server": {
    "host": "0.0.0.0",      // 服务器监听地址
    "port": 8011,           // 服务器端口
    "debug": true           // 是否开启调试模式
  },
  "endpoints": [            // 接口定义数组
    {
      "path": "/api/example",
      "methods": ["GET", "POST"],
      "description": "接口描述",
      "response": {
        "status_code": 200,
        "template": {
          // 响应数据模板
        }
      },
      "request_validation": {
        // 请求验证配置
      },
      "log_request": true   // 是否记录请求日志
    }
  ],
  "global_settings": {
    "enable_cors": true,                    // 是否启用CORS
    "default_error_status": 500,             // 默认错误状态码
    "default_error_message": "服务器内部错误"  // 默认错误消息
  }
}
```

### 接口配置详解

每个接口配置包含以下字段：

#### 必需字段

- **path** (string): 接口路径，如 `/api/example`
- **methods** (array): 支持的HTTP方法，如 `["GET", "POST"]`
- **response** (object): 响应配置
  - **status_code** (number): HTTP状态码，如 `200`
  - **template** (object): 响应数据模板

#### 可选字段

- **description** (string): 接口描述，用于文档和日志
- **request_validation** (object): 请求验证配置
  - **required_headers** (array): 必需的请求头列表，如 `["Authorization", "Content-Type"]`
  - **required_params** (array): 必需的查询参数列表，如 `["id", "name"]`
  - **required_body_fields** (array): 必需的请求体字段列表，如 `["username", "password"]`
- **log_request** (boolean): 是否记录请求日志，默认 `false`

### 响应模板变量

在响应模板中，可以使用以下模板变量，系统会自动替换为实际值：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `{{timestamp}}` | 当前时间戳 | `2024-01-01 12:00:00` |
| `{{request_method}}` | HTTP请求方法 | `GET`, `POST` |
| `{{request_headers}}` | 请求头信息（字典） | `{"Content-Type": "application/json"}` |
| `{{request_data}}` | 请求体数据 | `{"key": "value"}` |
| `{{request_args}}` | URL查询参数（字典） | `{"id": "123"}` |
| `{{request_url}}` | 完整请求URL | `http://localhost:8011/api/example?id=123` |
| `{{request_path}}` | 请求路径 | `/api/example` |
| `{{request_remote_addr}}` | 客户端IP地址 | `127.0.0.1` |
| `{{server_port}}` | 服务器端口 | `8011` |
| `{{endpoints_info}}` | 所有接口信息（字典） | `{"/api/example": "接口描述"}` |

### 配置示例

#### 示例1：简单的GET接口

```json
{
  "path": "/api/user/info",
  "methods": ["GET"],
  "description": "获取用户信息",
  "response": {
    "status_code": 200,
    "template": {
      "code": 0,
      "message": "success",
      "data": {
        "userId": "12345",
        "username": "testuser",
        "email": "test@example.com"
      },
      "timestamp": "{{timestamp}}"
    }
  },
  "log_request": false
}
```

#### 示例2：带请求验证的POST接口

```json
{
  "path": "/api/user/login",
  "methods": ["POST"],
  "description": "用户登录接口",
  "response": {
    "status_code": 200,
    "template": {
      "code": 0,
      "message": "登录成功",
      "data": {
        "token": "mock_token_12345",
        "userInfo": {
          "username": "{{request_data.username}}",
          "loginTime": "{{timestamp}}"
        }
      }
    }
  },
  "request_validation": {
    "required_headers": ["Content-Type"],
    "required_body_fields": ["username", "password"]
  },
  "log_request": true
}
```

#### 示例3：返回请求信息的Mock接口

```json
{
  "path": "/api/debug/request",
  "methods": ["GET", "POST", "PUT", "DELETE"],
  "description": "调试接口，返回请求信息",
  "response": {
    "status_code": 200,
    "template": {
      "status": 200,
      "message": "Mock服务响应成功",
      "timestamp": "{{timestamp}}",
      "request_method": "{{request_method}}",
      "request_headers": "{{request_headers}}",
      "request_data": "{{request_data}}",
      "request_args": "{{request_args}}",
      "request_url": "{{request_url}}",
      "request_path": "{{request_path}}",
      "request_remote_addr": "{{request_remote_addr}}"
    }
  },
  "log_request": true
}
```

#### 示例4：带查询参数验证的接口

```json
{
  "path": "/api/product/detail",
  "methods": ["GET"],
  "description": "获取产品详情",
  "response": {
    "status_code": 200,
    "template": {
      "code": 0,
      "message": "success",
      "data": {
        "productId": "{{request_args.id}}",
        "productName": "示例产品",
        "price": 99.99
      }
    }
  },
  "request_validation": {
    "required_params": ["id"]
  },
  "log_request": false
}
```

## 使用方法

### 1. 修改配置

编辑 `config.json` 文件，添加或修改接口配置。

### 2. 重启服务

修改配置后，如果开启了 `debug` 模式，服务会自动重启。否则需要手动重启服务。

### 3. 测试接口

使用curl、Postman或其他HTTP客户端测试接口：

```bash
# GET请求示例
curl http://localhost:8011/api/user/info

# POST请求示例
curl -X POST http://localhost:8011/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "123456"}'

# 带查询参数的GET请求
curl "http://localhost:8011/api/product/detail?id=12345"
```

## 请求验证

当配置了 `request_validation` 时，系统会在处理请求前进行验证：

- **验证失败**：返回400状态码和错误信息
- **验证成功**：正常处理请求并返回配置的响应

验证错误响应示例：

```json
{
  "status": 400,
  "message": "缺少必需的请求头: Authorization",
  "timestamp": "2024-01-01 12:00:00"
}
```

## 错误处理

当接口处理过程中发生错误时，系统会返回错误响应：

```json
{
  "status": 500,
  "message": "服务器内部错误: 具体错误信息",
  "timestamp": "2024-01-01 12:00:00"
}
```

错误状态码和消息可以在 `global_settings` 中配置。

## 日志输出

当接口配置了 `log_request: true` 时，控制台会输出详细的请求信息：

```
[2024-01-01 12:00:00] POST /api/user/login
请求头: {
  "Content-Type": "application/json",
  "User-Agent": "curl/7.68.0"
}
请求体: {
  "username": "testuser",
  "password": "123456"
}
查询参数: {}
--------------------------------------------------------------------------------
```

## 项目结构

```
LocalServer/
├── main.py              # 主程序文件
├── config.json          # 配置文件
├── ReadMe.md           # 本文档
├── pyproject.toml      # 项目配置
└── requirements.txt    # Python依赖（可选）
```

## 注意事项

1. **配置文件格式**：确保 `config.json` 是有效的JSON格式，否则服务无法启动
2. **路径冲突**：避免配置重复的接口路径，后注册的会覆盖先注册的
3. **模板变量**：模板变量必须完全匹配（包括双花括号），大小写敏感
4. **请求验证**：验证失败会直接返回错误，不会执行响应模板构建
5. **调试模式**：生产环境建议将 `debug` 设置为 `false`

## 扩展开发

### 添加新的模板变量

在 `ResponseBuilder._replace_template_variables` 方法中添加新的变量处理逻辑。

### 添加新的验证规则

在 `RequestValidator.validate` 方法中添加新的验证逻辑。

### 自定义响应处理

修改 `create_endpoint_handler` 函数，添加自定义的响应处理逻辑。

## 常见问题

**Q: 修改配置后接口没有更新？**  
A: 检查是否开启了 `debug` 模式，如果没有，需要手动重启服务。

**Q: 接口返回404？**  
A: 检查配置文件中的 `path` 是否正确，以及HTTP方法是否匹配。

**Q: 模板变量没有被替换？**  
A: 确保模板变量格式正确，使用双花括号 `{{variable_name}}`，且变量名完全匹配。

**Q: 请求验证总是失败？**  
A: 检查请求头、查询参数或请求体字段名称是否与配置中的完全一致（大小写敏感）。

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本
- 支持配置文件驱动的接口定义
- 支持模板变量替换
- 支持请求验证
- 支持请求日志记录
