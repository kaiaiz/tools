# 手机验证码发送工具

用于发送手机验证码的Python工具，支持单个和批量发送功能。

## 功能特性

- ✅ 单个手机号验证码发送
- ✅ 批量手机号验证码发送
- ✅ 参数自动加密（nonceStr + sign）
- ✅ 支持开发/生产环境切换
- ✅ 环境变量配置管理

## 安装依赖

```bash
pip install requests python-dotenv
```

或者使用requirements.txt：

```bash
pip install -r requirements.txt
```

## 配置说明

### 1. 创建环境变量文件

复制 `.env.example` 文件为 `.env`：

**Windows:**
```bash
copy .env.example .env
```

**Linux/Mac:**
```bash
cp .env.example .env
```

**注意：** 如果文件中文显示乱码，请使用支持UTF-8编码的编辑器（如VS Code、Notepad++等）打开文件，确保文件以UTF-8编码保存。

### 2. 配置环境变量

编辑 `.env` 文件，配置以下参数：

```env
# 环境配置
# 设置为 true 使用生产环境，false 使用开发环境
IS_PRO=true

# 开发环境配置
DEV_URL=https://appwx.tyjfwy.com/api/Weixinlogin/sendCodeNoVerify
DEV_TOKEN=your_dev_token_here

# 生产环境配置
PRO_URL=https://appwx.mkxxpt.com/api/Weixinlogin/sendCodeNoVerify
PRO_TOKEN=your_pro_token_here
```

### 配置参数说明

| 参数名 | 说明 | 必填 | 默认值 |
|--------|------|------|--------|
| `IS_PRO` | 是否使用生产环境（true/false） | 否 | true |
| `DEV_URL` | 开发环境API地址 | 是 | - |
| `DEV_TOKEN` | 开发环境Token | 是 | - |
| `PRO_URL` | 生产环境API地址 | 是 | - |
| `PRO_TOKEN` | 生产环境Token | 是 | - |

## 使用方法

### 单个发送

```python
from main import send_verification_code

# 发送验证码
result = send_verification_code("13800138000")
print(result)
```

### 批量发送

```python
from main import send_verification_code_batch

# 方式1：使用逗号分隔的字符串
phones = "13800138000,13900139000,13700137000"
results = send_verification_code_batch(phones)

# 方式2：使用列表
phones = ["13800138000", "13900139000", "13700137000"]
results = send_verification_code_batch(phones)

# 查看结果
for phone, result in results.items():
    print(f"{phone}: {result}")
```

### 命令行使用

```bash
python main.py
```

运行后会提示输入手机号，输入后即可发送验证码。

## 加密规则

工具会自动对请求参数进行加密：

1. 生成 `nonceStr`：5个随机字符 + 当前时间戳（毫秒）
2. 参数处理：去除空值，过滤对象类型，按字典序排序
3. 生成签名：将参数格式化为查询字符串，添加 `&key=coalmsg_token`，进行MD5加密并转大写

## 手机号段说明

### 移动号段
- 号段：134-139、147、150-152、157-159、182-184、187、188、198
- 示例：19812345678

### 联通号段
- 号段：130-132、145、155、156、166、171、175、176、185、186
- 示例：18600001111

### 电信号段
- 号段：133、149、153、173、177、180、181、189、199
- 示例：17755556666

## 注意事项

1. ⚠️ **不要将 `.env` 文件提交到版本控制系统**，已通过 `.gitignore` 忽略
2. ⚠️ 批量发送时，每个请求之间会有1秒延迟，避免请求过快
3. ⚠️ 确保Token配置正确，否则API调用会失败
4. ⚠️ 测试号码需要在对应平台完成绑定或授权

## 错误处理

- 如果环境变量未配置，会使用代码中的默认值
- 批量发送时，单个号码发送失败不会影响其他号码
- 所有错误信息都会在返回结果中记录

## 项目结构

```
send_phone/
├── main.py              # 主程序文件
├── .env                 # 环境变量配置（不提交到Git）
├── .env.example         # 环境变量配置模板
├── .gitignore           # Git忽略文件配置
├── README.md            # 本说明文档
├── requirements.txt     # Python依赖列表
└── verify_encoding.py   # 编码验证脚本（可选）
```

## 故障排除

### 中文乱码问题

如果 `.env` 或 `.env.example` 文件中的中文显示乱码：

1. **使用正确的编辑器打开**：使用支持UTF-8编码的编辑器（如VS Code、Notepad++、Sublime Text等）
2. **检查文件编码**：确保文件以UTF-8编码保存（无BOM）
3. **验证编码**：运行验证脚本：
   ```bash
   python verify_encoding.py
   ```
4. **手动创建**：如果问题持续，可以手动创建文件：
   - 复制 `.env.example` 为 `.env`
   - 在编辑器中打开 `.env`
   - 替换 `your_dev_token_here` 和 `your_pro_token_here` 为实际值
   - 确保以UTF-8编码保存

## 更新日志

### v1.1.0
- ✨ 支持环境变量配置
- ✨ 添加 `.env.example` 配置模板
- ✨ 添加 `.gitignore` 忽略敏感文件
- 📝 完善README文档

### v1.0.0
- 🎉 初始版本
- ✅ 单个和批量发送功能
- ✅ 参数加密功能

