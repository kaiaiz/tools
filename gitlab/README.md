# GitLab 代码统计工具

## 功能说明

本工具用于统计 GitLab 仓库中指定时间范围内的代码提交情况，包括：
- 每个用户的提交次数和代码行数统计
- 每个项目的提交统计
- 生成 CSV 格式的统计报告

## 配置说明

### 1. 获取 GitLab Token

#### 方法一：Personal Access Token（推荐）

1. **登录 GitLab**
   - 打开你的 GitLab 实例（如：`http://git.tyjfwy.com`）
   - 使用你的账号登录

2. **进入用户设置**
   - 点击右上角的用户头像
   - 选择 **Settings**（设置）或 **Preferences**（偏好设置）

3. **创建 Access Token**
   - 在左侧菜单中找到 **Access Tokens**（访问令牌）
   - 或者直接访问：`http://git.tyjfwy.com/-/user_settings/personal_access_tokens`

4. **配置 Token**
   - **Token name**（令牌名称）：输入一个描述性的名称，如 "代码统计工具"
   - **Expiration date**（过期日期）：选择 token 的有效期（可选）
   - **Select scopes**（选择权限范围）：至少勾选以下权限：
     - ✅ `read_api` - 允许通过 API 读取数据（必需）
     - ✅ `read_repository` - 允许读取仓库内容（必需）
   - 点击 **Create personal access token**（创建个人访问令牌）

5. **复制 Token**
   - ⚠️ **重要**：Token 只会显示一次，请立即复制保存
   - 如果丢失，需要重新创建

#### 方法二：Project Access Token（项目级别）

如果只需要访问特定项目：

1. **进入项目设置**
   - 打开需要统计的项目
   - 进入 **Settings** → **Access Tokens**

2. **创建项目 Token**
   - 输入 Token 名称
   - 选择权限：`read_api` 和 `read_repository`
   - 点击创建并复制 Token

### 2. 配置环境变量

**重要**：为了安全起见，所有敏感配置都通过 `.env` 文件管理，不会提交到代码仓库。

#### 步骤 1：创建 .env 文件

1. 复制示例文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填写你的实际配置：
   ```env
   # GitLab 实例的基础 URL（不包含具体的仓库路径）
   # 例如：http://git.tyjfwy.com 或 https://gitlab.com
   GITLAB_ROOT_URL=http://git.tyjfwy.com
   
   # GitLab Personal Access Token（从步骤 1 获取）
   GITLAB_TOKEN=your_token_here
   
   # 统计的开始日期（格式：YYYY-MM-DD）
   START_DAY=2022-01-01
   
   # 统计的结束日期（格式：YYYY-MM-DD）
   END_DAY=2025-01-01
   
   # 指定要统计的仓库列表（可选，留空则统计所有仓库）
   # 多个仓库用逗号分隔，支持仓库名称或完整路径（path_with_namespace）
   # 例如：GITLAB_PROJECTS=finance_backend,backend-api,root/frontend
   # 如果为空或未设置，则统计所有仓库
   GITLAB_PROJECTS=
   ```

**重要提示**：
- `.env` 文件已添加到 `.gitignore`，不会被提交到代码仓库
- `GITLAB_ROOT_URL` 应该是 GitLab 实例的基础 URL，例如：`http://git.tyjfwy.com` 或 `https://gitlab.com`
- 不要包含具体的仓库路径（如 `/root/finance_backend.git`）
- Token 具有访问权限，请妥善保管，不要泄露

#### 步骤 2：指定要统计的仓库（可选）

**方式一：统计所有仓库**
- 将 `GITLAB_PROJECTS` 留空或删除该配置项
- 程序会自动获取所有你有权限访问的仓库

**方式二：只统计指定的仓库**
- 在 `GITLAB_PROJECTS` 中指定要统计的仓库，多个仓库用逗号分隔
- 支持两种格式：
  - **完整路径（推荐）**：`root/finance_backend`（匹配仓库的 path_with_namespace 字段）
    - 从 Git 地址获取：`http://git.tyjfwy.com/root/finance_backend.git` → 完整路径是 `root/finance_backend`
  - **仓库名称**：`finance_backend`（程序会通过搜索 API 自动查找，如果找到多个匹配项会使用第一个）

**方式三：为每个仓库指定分支（推荐）**
- 在 `GITLAB_PROJECTS` 中可以使用 `仓库路径:分支名` 格式为每个仓库指定分支
- 支持同一仓库配置多次，每次可以指定不同的分支
- 如果只写 `仓库路径`，则使用该仓库的默认分支
- 如果写 `仓库路径:分支名`，则使用指定的分支
  
**示例**：
```env
# 只统计三个指定的仓库（推荐使用完整路径）
GITLAB_PROJECTS=root/finance_backend,root/backend-api,frontend-team/frontend

# 或者使用仓库名称（程序会自动搜索，但可能不够准确）
GITLAB_PROJECTS=finance_backend,backend-api,frontend

# 为仓库指定分支（推荐方式，可精准控制每个仓库的分支）
# 获取 root/finance_backend 的默认分支
GITLAB_PROJECTS=root/finance_backend

# 仅获取 root/finance_backend 的 dev 分支
GITLAB_PROJECTS=root/finance_backend:dev

# 获取 root/finance_backend 的默认分支和 dev 分支
GITLAB_PROJECTS=root/finance_backend,root/finance_backend:dev

# 不同仓库指定不同分支
GITLAB_PROJECTS=root/finance_backend:dev,root/backend-api:main,frontend-team/frontend

# 混合使用：部分仓库使用默认分支，部分仓库指定分支
GITLAB_PROJECTS=root/finance_backend,root/backend-api:dev,root/frontend:main
```

**如何获取完整路径**：
1. 从 Git 地址获取：
   - Git 地址：`http://git.tyjfwy.com/root/finance_backend.git`
   - 完整路径：`root/finance_backend`（去掉 `.git` 后缀，保留 `namespace/project_name`）
2. 从 GitLab 网页获取：
   - 打开项目页面，URL 通常是：`http://git.tyjfwy.com/root/finance_backend`
   - 完整路径就是 URL 中域名后的部分：`root/finance_backend`

**注意**：
- ✅ **强烈推荐使用完整路径**（`namespace/project_name`），更准确、更快速
- ⚠️ 使用仓库名称时，如果存在同名项目，可能匹配到错误的项目
- ⚠️ 如果指定的仓库不存在或无法访问，程序会跳过并显示错误信息
- ⚠️ 如果所有指定的仓库都无法获取，程序会退出

#### 步骤 3：指定要统计的分支（可选）

**推荐方式：在 GITLAB_PROJECTS 中指定分支（精准控制）**
- 在 `GITLAB_PROJECTS` 中使用 `仓库路径:分支名` 格式为每个仓库指定分支
- 这样可以避免在配置多个仓库时无法精准定位分支的问题
- 详见步骤 2 中的"方式三"

**方式一：使用默认分支（默认行为）**
- 将 `GITLAB_BRANCHES` 留空或删除该配置项
- 如果 `GITLAB_PROJECTS` 中也没有指定分支，程序会使用各仓库的默认分支（通常是 `main` 或 `master`）

**方式二：使用全局分支配置（向后兼容）**
- 在 `GITLAB_BRANCHES` 中指定要统计的分支，多个分支用逗号分隔
- 此配置会应用到所有仓库（如果 `GITLAB_PROJECTS` 中没有为仓库指定分支）
- 程序会统计所有指定分支的提交（如果多个分支有相同的提交，会自动去重）

**示例**：
```env
# 只统计 dev 分支（适用于所有仓库）
GITLAB_BRANCHES=dev

# 统计多个分支（适用于所有仓库）
GITLAB_BRANCHES=dev,main,feature/xxx

# 使用默认分支（留空）
GITLAB_BRANCHES=
```

**配置优先级**：
1. **最高优先级**：`GITLAB_PROJECTS` 中为仓库指定的分支（如 `root/finance_backend:dev`）
2. **次优先级**：`GITLAB_BRANCHES` 全局分支配置
3. **默认行为**：使用仓库的默认分支

**重要提示**：
- ✅ **强烈推荐在 `GITLAB_PROJECTS` 中为每个仓库指定分支**，这样可以精准控制每个仓库的分支
- ⚠️ 如果仓库的默认分支是 `main`，但主要代码在 `dev` 分支，需要指定分支
- ⚠️ 如果指定了多个分支，会统计所有分支的提交（相同提交会自动去重）
- ⚠️ 如果指定的分支不存在，程序会跳过该分支并显示警告信息
- ⚠️ 如果同时在 `GITLAB_PROJECTS` 和 `GITLAB_BRANCHES` 中配置，`GITLAB_PROJECTS` 中的配置优先

#### 步骤 4：配置排除规则（可选）

如果需要排除某些仓库不进行统计，可以在 `.env` 文件中配置：

```env
# 排除指定路径的仓库（多个路径用逗号分隔）
# 例如：排除 root/test 和 root/demo 这两个仓库
EXCLUDE_PATHS=root/test,root/demo

# 排除以指定前缀开头的仓库名（多个前缀用逗号分隔）
# 例如：排除所有以 "test-"、"demo-"、"temp-" 开头的仓库
EXCLUDE_PREFIX=test-,demo-,temp-

# 排除指定名称的项目（多个项目名用逗号分隔，完全匹配项目名称）
# 例如：排除名为 "仓库1"、"仓库2"、"仓库3" 的项目
EXCLUDE_PROJECT=仓库1,仓库2,仓库3
```

**注意**：
- 所有排除配置都是可选的，留空表示不排除任何仓库
- `EXCLUDE_PATHS`：使用完整路径（`namespace/project_name`）匹配
- `EXCLUDE_PREFIX`：匹配仓库名称的前缀
- `EXCLUDE_PROJECT`：完全匹配仓库名称

### 3. 完整配置示例

以下是一个完整的 `.env` 文件配置示例：

```env
# GitLab 实例的基础 URL
GITLAB_ROOT_URL=http://git.tyjfwy.com

# GitLab Personal Access Token
GITLAB_TOKEN=your_token_here

# 统计的时间范围
START_DAY=2022-01-01
END_DAY=2025-01-01

# 指定要统计的仓库（可选）
# 方式1：使用默认分支
GITLAB_PROJECTS=root/finance_backend,root/backend-api

# 方式2：为每个仓库指定分支（推荐）
GITLAB_PROJECTS=root/finance_backend:dev,root/backend-api:main

# 方式3：混合使用（部分使用默认分支，部分指定分支）
GITLAB_PROJECTS=root/finance_backend,root/backend-api:dev

# 指定要统计的分支（可选，向后兼容，适用于所有仓库）
# 如果 GITLAB_PROJECTS 中已为仓库指定分支，则优先使用 GITLAB_PROJECTS 中的配置
GITLAB_BRANCHES=dev,main

# 排除配置（可选）
EXCLUDE_PATHS=root/test,root/demo
EXCLUDE_PREFIX=test-,temp-
EXCLUDE_PROJECT=仓库1,仓库2
```

### 4. 过滤配置（已迁移到 .env 文件）

**注意**：所有个性化配置已迁移到 `.env` 文件中，不再需要在代码中修改。如果需要在代码中查看历史配置，可以参考以下说明：

- `EXCLUDE_PATHS`：排除指定完整路径的仓库
- `EXCLUDE_PREFIX`：排除以指定前缀开头的仓库名
- `EXCLUDE_PROJECT`：排除指定名称的项目（完全匹配）

## 使用方法

### 运行统计

```bash
# 使用 uv 运行
uv run main.py

# 或直接使用 Python
python main.py
```

### 输出文件

程序运行完成后会生成两个 CSV 文件：

1. **user-output.csv** - 用户提交统计
   - 包含每个用户在每个项目中的提交情况
   - 包含汇总信息

2. **repository-output.csv** - 项目提交统计
   - 包含每个项目的总体提交统计

## 常见问题

### 1. 环境变量未设置

**错误信息**：`GITLAB_TOKEN 未设置！请在 .env 文件中设置 GITLAB_TOKEN`

**解决方法**：
- 确认已创建 `.env` 文件（复制自 `.env.example`）
- 确认 `.env` 文件中 `GITLAB_TOKEN` 已正确填写
- 确认 `.env` 文件与 `git_statistics.py` 在同一目录下

### 2. Token 权限不足

**错误信息**：`API 请求失败` 或 `401 Unauthorized`

**解决方法**：
- 检查 Token 是否包含 `read_api` 和 `read_repository` 权限
- 确认 Token 未过期
- 确认 Token 属于有权限访问目标仓库的账号

### 3. URL 配置错误

**错误信息**：`404 Not Found` 或 `无法获取仓库列表`

**解决方法**：
- 确认 `root_url` 是 GitLab 实例的基础 URL（不包含仓库路径）
- 确认 GitLab 实例地址可访问
- 检查网络连接

### 4. JSON 解析错误

**错误信息**：`JSONDecodeError: Expecting value`

**解决方法**：
- 检查 Token 是否正确
- 检查 URL 配置是否正确
- 查看错误信息中的详细响应内容

### 5. 仓库列表为空

**可能原因**：
- 时间范围设置不当，所有仓库的最后活动时间都在开始日期之前
- 所有仓库都被过滤规则排除了
- Token 权限不足，无法访问仓库列表

## 注意事项

1. **Token 安全**：
   - ✅ 使用 `.env` 文件管理敏感信息（已自动添加到 `.gitignore`）
   - ✅ `.env` 文件不会被提交到代码仓库
   - ⚠️ 不要将 `.env` 文件的内容分享给他人
   - ⚠️ Token 泄露后应立即撤销并重新创建

2. **API 限制**：
   - GitLab API 可能有请求频率限制
   - 如果仓库数量很多，程序运行时间可能较长

3. **数据准确性**：
   - 统计结果基于 GitLab API 返回的数据
   - 如果仓库已删除或不可访问，可能无法获取数据

## 代码结构

- `git_statistics.py` - 主要统计逻辑
- `main.py` - 程序入口
- `safe_json_response()` - 安全的 JSON 响应解析函数
- `get_all_commits()` - 获取仓库的所有提交
- `get_commit_stats()` - 获取单个提交的统计信息
- `start()` - 主统计流程

## 更新日志

### 2024-12-XX（最新）
- ✅ **新增功能**：支持在 `GITLAB_PROJECTS` 中为每个仓库指定分支，格式：`仓库路径:分支名`
- ✅ **精准控制**：可以同时为不同仓库配置不同分支，避免全局分支配置的限制
- ✅ **向后兼容**：保留原有的 `GITLAB_BRANCHES` 全局分支配置，优先级低于 `GITLAB_PROJECTS` 中的分支配置
- ✅ **灵活配置**：支持同一仓库配置多次，每次可以指定不同的分支（如：`root/finance_backend,root/finance_backend:dev`）

### 2024-12-XX
- ✅ 添加了指定仓库功能：可通过 `GITLAB_PROJECTS` 环境变量指定要统计的仓库，留空则统计所有仓库
- ✅ 将敏感配置迁移到 `.env` 文件，提高安全性
- ✅ 添加了 `.env.example` 示例文件
- ✅ 更新 `.gitignore` 忽略 `.env` 和输出文件
- ✅ 添加了完善的错误处理机制
- ✅ 修复了 JSON 解析错误问题
- ✅ 修复了过滤逻辑错误
- ✅ 添加了详细的错误信息输出

