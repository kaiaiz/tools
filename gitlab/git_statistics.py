# git_statistics.py
import datetime
import os
from collections import defaultdict

import requests
import json
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

"""
GitLab 实例的基础 URL（不包含具体的仓库路径）
例如：http://git.tyjfwy.com 或 https://gitlab.com
注意：不要包含仓库路径，如 /root/finance_backend.git
从环境变量 GITLAB_ROOT_URL 读取，如果不存在则使用默认值
"""
root_url = os.getenv("GITLAB_ROOT_URL", "https://gitlab.***.com")

"""
在 GitLab 上设置的 Personal Access Token
从环境变量 GITLAB_TOKEN 读取
获取方法请查看 README.md
"""
token = os.getenv("GITLAB_TOKEN", "")
if not token:
    raise ValueError(
        "GITLAB_TOKEN 未设置！请在 .env 文件中设置 GITLAB_TOKEN，或参考 .env.example 文件"
    )

"""统计的开始日期，从环境变量 START_DAY 读取"""
start_day = os.getenv("START_DAY", "2022-01-01")

"""统计的结束日期，从环境变量 END_DAY 读取"""
end_day = os.getenv("END_DAY", "2025-01-01")
"""统计的时间区间-开始日期，datetime对象"""
start_date = datetime.datetime.strptime(start_day, '%Y-%m-%d')
"""统计的时间区间-结束日期，datetime对象"""
end_date = datetime.datetime.strptime(end_day, '%Y-%m-%d')

"""
指定要统计的仓库列表（可选）
从环境变量 GITLAB_PROJECTS 读取，多个仓库用逗号分隔
支持仓库名称（name）或完整路径（path_with_namespace，如：root/finance_backend）
支持为每个仓库指定分支，格式：仓库路径:分支名
如果为空或未设置，则统计所有仓库

配置示例：
- GITLAB_PROJECTS=root/finance_backend  # 使用默认分支
- GITLAB_PROJECTS=root/finance_backend:dev  # 仅使用dev分支
- GITLAB_PROJECTS=root/finance_backend,root/finance_backend:dev  # 使用默认分支和dev分支
- GITLAB_PROJECTS=root/finance_backend,root/backend-api:main  # 不同仓库不同分支
"""
specified_projects_str = os.getenv("GITLAB_PROJECTS", "").strip()
specified_projects_raw = [p.strip() for p in specified_projects_str.split(",") if p.strip()] if specified_projects_str else []

# 解析仓库和分支的映射关系
# 格式：{仓库路径: {"branches": [分支列表], "include_default": bool}}
# include_default 为 True 表示需要统计默认分支，False 表示不统计默认分支
# 例如：
# - {"root/finance_backend": {"branches": [], "include_default": True}} 表示只使用默认分支
# - {"root/finance_backend": {"branches": ["dev"], "include_default": False}} 表示只使用dev分支
# - {"root/finance_backend": {"branches": ["dev"], "include_default": True}} 表示使用默认分支和dev分支
project_branch_map = {}
specified_projects = []

for item in specified_projects_raw:
    if ":" in item:
        # 格式：仓库路径:分支名
        parts = item.split(":", 1)  # 只分割第一个冒号，支持分支名中包含冒号的情况
        project_path = parts[0].strip()
        branch_name = parts[1].strip()
        
        if project_path:
            if project_path not in project_branch_map:
                project_branch_map[project_path] = {"branches": [], "include_default": False}
                specified_projects.append(project_path)
            if branch_name:
                # 避免重复添加相同的分支
                if branch_name not in project_branch_map[project_path]["branches"]:
                    project_branch_map[project_path]["branches"].append(branch_name)
    else:
        # 格式：仓库路径（使用默认分支）
        project_path = item.strip()
        if project_path:
            if project_path not in project_branch_map:
                project_branch_map[project_path] = {"branches": [], "include_default": True}
                specified_projects.append(project_path)
            else:
                # 如果之前已经存在（可能是通过 :分支名 添加的），现在标记为包含默认分支
                project_branch_map[project_path]["include_default"] = True

"""
指定要统计的分支列表（可选，向后兼容）
从环境变量 GITLAB_BRANCHES 读取，多个分支用逗号分隔
如果为空或未设置，则使用仓库的默认分支
例如：GITLAB_BRANCHES=dev,main,feature/xxx
注意：如果指定了多个分支，会统计所有分支的提交（可能重复统计同一个提交）

注意：如果 GITLAB_PROJECTS 中已经为仓库指定了分支，则优先使用 GITLAB_PROJECTS 中的配置
此配置仅在没有在 GITLAB_PROJECTS 中指定分支时生效
"""
specified_branches_str = os.getenv("GITLAB_BRANCHES", "").strip()
specified_branches = [b.strip() for b in specified_branches_str.split(",") if b.strip()] if specified_branches_str else []

"""查询仓库列表 url"""
query_repository_list_url = f"{root_url}/api/v4/projects?private_token={token}&per_page=1000"

"""
根据full_path过滤的仓库（可选）
从环境变量 EXCLUDE_PATHS 读取，多个路径用逗号分隔
例如：EXCLUDE_PATHS=root/test,root/demo
"""
exclude_paths_str = os.getenv("EXCLUDE_PATHS", "").strip()
exclude_paths = tuple(p.strip() for p in exclude_paths_str.split(",") if p.strip()) if exclude_paths_str else ()

"""
哪些仓库路径前缀要排除（可选）
从环境变量 EXCLUDE_PREFIX 读取，多个前缀用逗号分隔
例如：EXCLUDE_PREFIX=test-,demo-,temp-
"""
exclude_prefix_str = os.getenv("EXCLUDE_PREFIX", "").strip()
exclude_prefix = tuple(p.strip() for p in exclude_prefix_str.split(",") if p.strip()) if exclude_prefix_str else ()

"""
哪些项目要排除（可选）
从环境变量 EXCLUDE_PROJECT 读取，多个项目名用逗号分隔
例如：EXCLUDE_PROJECT=仓库1,仓库2,仓库3
"""
exclude_project_str = os.getenv("EXCLUDE_PROJECT", "").strip()
exclude_project = tuple(p.strip() for p in exclude_project_str.split(",") if p.strip()) if exclude_project_str else ()

datetime_format = "%Y-%m-%dT%H:%M:%S.%fZ"


def parse_gitlab_datetime(datetime_str):
    """
    解析 GitLab API 返回的时间字符串
    支持多种格式：
    - 2025-11-12T17:42:47.459+08:00 (带时区)
    - 2025-11-12T17:42:47.459Z (UTC)
    - 2025-11-12T17:42:47+08:00 (无毫秒，带时区)
    - 2025-11-12T17:42:47Z (无毫秒，UTC)
    
    Args:
        datetime_str: GitLab API 返回的时间字符串
    
    Returns:
        datetime.datetime 对象
    """
    # 尝试多种格式
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # 带毫秒和时区，如：2025-11-12T17:42:47.459+08:00
        "%Y-%m-%dT%H:%M:%S.%fZ",   # 带毫秒UTC，如：2025-11-12T17:42:47.459Z
        "%Y-%m-%dT%H:%M:%S%z",     # 无毫秒带时区，如：2025-11-12T17:42:47+08:00
        "%Y-%m-%dT%H:%M:%SZ",      # 无毫秒UTC，如：2025-11-12T17:42:47Z
    ]
    
    import re
    for fmt in formats:
        try:
            # 处理时区格式（+08:00 需要转换为 +0800，因为 Python 的 %z 格式要求 +0800 而不是 +08:00）
            if fmt.endswith('%z'):
                # 使用正则表达式将 +08:00 或 -08:00 格式转换为 +0800 或 -0800
                timezone_pattern = r'([+-])(\d{2}):(\d{2})$'
                datetime_str_fixed = re.sub(timezone_pattern, r'\1\2\3', datetime_str)
                return datetime.datetime.strptime(datetime_str_fixed, fmt)
            else:
                return datetime.datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    # 如果所有格式都失败，抛出异常
    raise ValueError(f"无法解析时间格式: {datetime_str}")


def safe_json_response(response, url, error_context=""):
    """
    安全地解析 JSON 响应，包含错误处理
    
    Args:
        response: requests.Response 对象
        url: 请求的 URL（用于错误信息）
        error_context: 错误上下文描述（用于错误信息）
    
    Returns:
        dict 或 list: 解析后的 JSON 数据
    
    Raises:
        Exception: 当响应状态码不是 200 或无法解析 JSON 时抛出异常
    """
    # 检查响应状态码
    if response.status_code != 200:
        error_msg = f"API 请求失败 {error_context}\nURL: {url}\n状态码: {response.status_code}\n响应内容: {response.text[:500]}"
        print(error_msg)
        raise Exception(error_msg)
    
    # 检查响应内容是否为空
    if not response.text or not response.text.strip():
        error_msg = f"API 返回空响应 {error_context}\nURL: {url}\n状态码: {response.status_code}"
        print(error_msg)
        raise Exception(error_msg)
    
    # 尝试解析 JSON
    try:
        return response.json()
    except json.JSONDecodeError as e:
        error_msg = f"JSON 解析失败 {error_context}\nURL: {url}\n状态码: {response.status_code}\n响应内容前500字符: {response.text[:500]}\n错误详情: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)


def get_all_commits(repository, branch_name=None):
    """
    获取该仓库指定时间内，指定分支的所有提交
    
    Args:
        repository: Repository 对象
        branch_name: 分支名称，如果为 None 则使用仓库的默认分支
    
    Returns:
        dict: 以用户邮箱为键，提交列表为值的字典
    """
    # 确定要统计的分支
    if branch_name is None:
        branch_name = repository.default_branch or "main"
    
    since_date = start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    until_date = end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    url = f"{root_url}/api/v4/projects/{repository.id}/repository/commits?page=1&per_page=10000&ref_name={branch_name}&since={since_date}&until={until_date}&private_token={token}"
    
    try:
        response = requests.get(url)
        commits = safe_json_response(response, url, f"获取仓库 {repository.name} 分支 {branch_name} 的提交记录")
    except Exception as e:
        print(f"⚠ 获取仓库 {repository.name} 分支 {branch_name} 的提交记录失败: {str(e)}")
        return None
    
    if len(commits) == 0:
        print(f"  ℹ 仓库 {repository.name} 分支 {branch_name} 在指定时间范围内没有提交")
        return None
    
    print(f"  ✓ 仓库 {repository.name} 分支 {branch_name}: 找到 {len(commits)} 个提交")
    
    # 根据提交用户分组
    user_dict = defaultdict(list)
    for commit_record in commits:
        commit = Commit()
        commit.id = commit_record['id']
        commit.repository_name = repository.name
        commit.committer_name = commit_record['committer_name']
        commit.committer_email = commit_record['committer_email']
        user_dict[commit.committer_email].append(commit)

    return user_dict


def get_commit_stats(repository_id, commit_id):
    """获取每个提交的明细"""
    url = f"{root_url}/api/v4/projects/{repository_id}/repository/commits/{commit_id}?private_token={token}"
    try:
        response = requests.get(url)
        detail = safe_json_response(response, url, f"获取提交 {commit_id} 的统计信息")
    except Exception as e:
        print(f"获取提交 {commit_id} 的统计信息失败: {str(e)}")
        # 返回空的统计信息，避免中断整个流程
        stats = CommitStats()
        stats.total = 0
        stats.deletions = 0
        stats.additions = 0
        return stats
    
    stats = CommitStats()
    stats.total = detail.get('stats', {}).get('total', 0)
    stats.deletions = detail.get('stats', {}).get('deletions', 0)
    stats.additions = detail.get('stats', {}).get('additions', 0)
    return stats


def get_project_by_path(project_path):
    """
    根据项目路径获取项目信息
    支持通过 path_with_namespace（如：root/finance_backend）或项目 ID 获取
    如果直接获取失败，会尝试通过搜索 API 查找项目
    
    Args:
        project_path: 项目路径、项目名称或项目 ID（字符串）
    
    Returns:
        Repository 对象，如果获取失败或不符合时间范围返回 None
    """
    import urllib.parse
    
    # 首先尝试直接通过路径获取（支持完整路径或项目 ID）
    encoded_path = urllib.parse.quote(project_path, safe='')
    url = f"{root_url}/api/v4/projects/{encoded_path}?private_token={token}"
    try:
        response = requests.get(url)
        e = safe_json_response(response, url, f"获取项目 {project_path}")
        
        # 检查时间范围
        last_active_time = parse_gitlab_datetime(e['last_activity_at'])
        # 转换为本地时间进行比较（去掉时区信息）
        if last_active_time.tzinfo:
            last_active_time = last_active_time.replace(tzinfo=None)
        if last_active_time < start_date:
            print(f"⚠ 仓库 {project_path} 的最后活动时间 {e['last_activity_at']} 早于开始日期 {start_day}，跳过")
            return None
        
        repository = Repository()
        repository.id = e['id']
        repository.name = e['name']
        repository.path = e['path_with_namespace']
        repository.web_url = e['web_url']
        repository.full_path = e['namespace']['full_path']
        repository.default_branch = e['default_branch']
        return repository
    except Exception as e:
        # 如果直接获取失败，且路径中不包含 '/'，尝试通过搜索 API 查找
        if '/' not in project_path:
            print(f"⚠ 直接获取项目 {project_path} 失败，尝试通过搜索查找...")
            return get_project_by_search(project_path)
        else:
            print(f"获取项目 {project_path} 失败: {str(e)}")
            print(f"提示：请确认项目路径格式正确，应该使用完整路径（如：root/finance_backend）")
            return None


def get_project_by_search(project_name):
    """
    通过搜索 API 根据项目名称查找项目
    如果找到多个匹配项，返回第一个匹配的项目
    
    Args:
        project_name: 项目名称（字符串）
    
    Returns:
        Repository 对象，如果未找到或不符合时间范围返回 None
    """
    import urllib.parse
    encoded_name = urllib.parse.quote(project_name, safe='')
    # 使用搜索 API，搜索项目名称
    url = f"{root_url}/api/v4/projects?search={encoded_name}&private_token={token}&per_page=100"
    try:
        response = requests.get(url)
        projects = safe_json_response(response, url, f"搜索项目 {project_name}")
        
        # 查找完全匹配的项目名称
        matched_projects = [p for p in projects if p.get('name') == project_name or p.get('path') == project_name]
        
        if not matched_projects:
            # 如果没有完全匹配，使用第一个结果
            if projects:
                matched_projects = [projects[0]]
                print(f"⚠ 未找到完全匹配的项目 '{project_name}'，使用最相似的项目：{projects[0].get('path_with_namespace')}")
            else:
                print(f"✗ 未找到项目：{project_name}")
                print(f"提示：请使用完整路径（如：root/{project_name}）或确认项目名称正确")
                return None
        
        # 使用第一个匹配的项目
        e = matched_projects[0]
        
        # 检查时间范围
        last_active_time = parse_gitlab_datetime(e['last_activity_at'])
        # 转换为本地时间进行比较（去掉时区信息）
        if last_active_time.tzinfo:
            last_active_time = last_active_time.replace(tzinfo=None)
        if last_active_time < start_date:
            print(f"⚠ 仓库 {e['path_with_namespace']} 的最后活动时间 {e['last_activity_at']} 早于开始日期 {start_day}，跳过")
            return None
        
        repository = Repository()
        repository.id = e['id']
        repository.name = e['name']
        repository.path = e['path_with_namespace']
        repository.web_url = e['web_url']
        repository.full_path = e['namespace']['full_path']
        repository.default_branch = e['default_branch']
        print(f"✓ 通过搜索找到项目：{repository.path}")
        return repository
    except Exception as e:
        print(f"搜索项目 {project_name} 失败: {str(e)}")
        print(f"提示：请使用完整路径（如：root/{project_name}）或确认项目名称正确")
        return None


def start():
    """启动统计"""
    repositories = []
    
    # 如果指定了要统计的仓库，则只获取指定的仓库
    if specified_projects:
        print(f"指定了 {len(specified_projects)} 个仓库进行统计：{', '.join(specified_projects)}")
        for project_identifier in specified_projects:
            repository = get_project_by_path(project_identifier)
            if repository:
                repositories.append(repository)
                print(f"✓ 已添加仓库: {repository.path} ({repository.name})")
            else:
                print(f"✗ 无法获取仓库: {project_identifier}，请检查仓库路径或名称是否正确，或确认仓库的最后活动时间在指定时间范围内")
        
        if not repositories:
            print("错误：没有成功获取任何指定的仓库，请检查配置")
            return
    else:
        # 如果未指定仓库，则获取所有仓库
        print("未指定仓库，将统计所有仓库...")
        for i in range(1, 100):
            # 返回的每页的最大数量是有限制的，所以分页查询
            url = f"{query_repository_list_url}&page={i}"
            try:
                response = requests.get(url)
                res = safe_json_response(response, url, f"获取第 {i} 页仓库列表")
            except Exception as e:
                print(f"获取第 {i} 页仓库列表失败: {str(e)}")
                # 如果第一页就失败，说明可能是配置问题，直接退出
                if i == 1:
                    print("无法获取仓库列表，请检查配置（URL、Token等）是否正确")
                    return
                # 其他页失败，可能是已经到最后一页了，退出循环
                break
            
            # print(f"仓库总数量：{len(res)}")
            if len(res) <= 0:
                break
            # 先遍历所有的仓库
            for e in res:
                last_active_time = parse_gitlab_datetime(e['last_activity_at'])
                # 转换为本地时间进行比较（去掉时区信息）
                if last_active_time.tzinfo:
                    last_active_time = last_active_time.replace(tzinfo=None)
                if last_active_time < start_date:
                    continue
                repository = Repository()
                repository.id = e['id']
                repository.name = e['name']
                repository.path = e['path_with_namespace']
                repository.web_url = e['web_url']
                repository.full_path = e['namespace']['full_path']
                repository.default_branch = e['default_branch']

                # 如果仓库路径在排除列表中，则跳过
                if exclude_paths and repository.path in exclude_paths:
                    continue

                # 如果仓库名以排除的前缀开头，则跳过
                if exclude_prefix and any(repository.name.startswith(prefix) for prefix in exclude_prefix):
                    continue

                # 如果仓库名在排除列表中，则跳过
                if exclude_project and repository.name in exclude_project:
                    continue

                repositories.append(repository)
    print(f"本轮需要统计的仓库数量: {len(repositories)}")
    for r in repositories:
        # 显示每个仓库对应的分支配置
        if project_branch_map and r.path in project_branch_map:
            config = project_branch_map[r.path]
            branch_list = []
            if config["include_default"]:
                branch_list.append(f"默认分支({r.default_branch})")
            if config["branches"]:
                branch_list.extend(config["branches"])
            print(f"  - {r.name} (路径: {r.path}, 分支: {', '.join(branch_list)})")
        else:
            if specified_branches:
                print(f"  - {r.name} (路径: {r.path}, 分支: {', '.join(specified_branches)})")
            else:
                print(f"  - {r.name} (路径: {r.path}, 分支: 默认分支 {r.default_branch})")
    
    # 显示要统计的分支配置信息
    if project_branch_map:
        print(f"\n已为 {len(project_branch_map)} 个仓库配置了分支映射")
        for project_path, config in project_branch_map.items():
            branch_list = []
            if config["include_default"]:
                branch_list.append("默认分支")
            if config["branches"]:
                branch_list.extend(config["branches"])
            print(f"  - {project_path}: {', '.join(branch_list)}")
    elif specified_branches:
        print(f"\n指定了全局分支配置：{', '.join(specified_branches)}（适用于所有仓库）")
    else:
        print(f"\n未指定分支，将使用各仓库的默认分支")
    
    user_commit_statistics_list = []
    i = 0
    # 获取每个仓库的统计信息
    for repository in repositories:
        # 确定要统计的分支列表
        # 优先使用 project_branch_map 中的配置，如果没有则使用全局的 specified_branches
        if project_branch_map and repository.path in project_branch_map:
            config = project_branch_map[repository.path]
            branches_to_stat = []
            # 如果需要包含默认分支，添加 None（None 表示使用默认分支）
            if config["include_default"]:
                branches_to_stat.append(None)
            # 添加指定的分支
            branches_to_stat.extend(config["branches"])
            # 如果没有配置任何分支，使用默认分支
            if not branches_to_stat:
                branches_to_stat = [None]
        else:
            # 使用全局分支配置
            branches_to_stat = specified_branches if specified_branches else [None]  # None 表示使用默认分支
        
        # 遍历每个分支
        for branch_name in branches_to_stat:
            branch_display = branch_name if branch_name else repository.default_branch
            print(f"\n正在统计仓库 {repository.name} 的分支: {branch_display}")
            
            # 当前仓库，每个用户的所有提交记录
            user_commits_dict = get_all_commits(repository, branch_name)
            if user_commits_dict is None:
                continue
            # i += 1
            # if i > 2:
            #     break
            for email, commits in user_commits_dict.items():
                user = CommitRepositoryUser()
                user.email = email
                user.repository_name = repository.name
                exist = []
                for commit in commits:
                    # 避免重复（跨分支可能有相同的提交）
                    if commit.id in exist:
                        continue
                    exist.append(commit.id)
                    user.username = commit.committer_name
                    user.commit_total += 1
                    stats = get_commit_stats(repository.id, commit.id)
                    user.total += stats.total
                    user.additions += stats.additions
                    user.deletions += stats.deletions
                print(
                    f"    [{repository.name}] {user.username} ({user.email}): 提交数={user.commit_total}, 总行数={user.total}, 新增={user.additions}, 删除={user.deletions}")
                user_commit_statistics_list.append(user)
    print("\n✓ 用户统计完成")
    #
    # 计算每个用户的提交总数
    user_statistics_dict = defaultdict(list)
    # 每个项目的提交列表
    repository_statistics_dict = defaultdict(list)
    for ucs in user_commit_statistics_list:
        user_statistics_dict[ucs.email].append(ucs)
        repository_statistics_dict[ucs.repository_name].append(ucs)

    out_lines = []
    out_lines.append("姓名, 邮箱, 项目, 提交数, 总提交行数, 增加代码行数, 删除代码行数")
    for usl in user_statistics_dict.values():
        cru = CommitRepositoryUser()
        for us in usl:
            cru.email = us.email
            cru.username = us.username
            cru.total += us.total
            cru.additions += us.additions
            cru.deletions += us.deletions
            cru.commit_total += us.commit_total
            out_lines.append(
                f"{us.username}, {us.email}, {us.repository_name}, {us.commit_total}, {us.total}, {us.additions}, {us.deletions}")
        out_lines.append(
            f"{cru.username}, {cru.email}, , {cru.commit_total}, {cru.total}, {cru.additions}, {cru.deletions}")
        out_lines.append(f", , , , , , ")

    with open('user-output.csv', mode='w', newline='', encoding='utf-8-sig') as csvfile:
        for line in out_lines:
            csvfile.write(line + "\r\n")

    # 计算每个仓库的总提交数
    repository_out_lines = []
    repository_out_lines.append("项目, 提交次数, 提交代码行数, 新增代码行数, 删除代码行数")
    print("\n" + "="*80)
    print("仓库统计汇总：")
    print("="*80)
    for repository_name, usl in repository_statistics_dict.items():
        cru = CommitRepositoryUser()
        cru.repository_name = repository_name
        for us in usl:
            cru.total += us.total
            cru.additions += us.additions
            cru.deletions += us.deletions
            cru.commit_total += us.commit_total
        # 在控制台输出仓库统计
        print(f"仓库: {cru.repository_name}")
        print(f"  提交次数: {cru.commit_total}")
        print(f"  总代码行数: {cru.total}")
        print(f"  新增代码行数: {cru.additions}")
        print(f"  删除代码行数: {cru.deletions}")
        print("-"*80)
        repository_out_lines.append(f"{cru.repository_name}, {cru.commit_total}, {cru.total}, {cru.additions}, {cru.deletions}")

    with open('repository-output.csv', mode='w', newline='', encoding='utf-8-sig') as csvfile:
        for line in repository_out_lines:
            csvfile.write(line + "\r\n")
    print(f"\n✓ 仓库统计已保存到 repository-output.csv")
class Repository:
    """仓库信息，只定义关注的字段"""
    id = None
    name = None
    path = None
    default_branch = None
    web_url = None
    full_path = None


class Commit:
    """提交记录"""
    id = None
    committer_name = None
    committer_email = None
    repository_name = None


class CommitStats:
    """每个提交记录的提交统计"""
    additions = 0
    deletions = 0
    total = 0


class CommitUser:
    username = None
    email = None
    additions = 0
    deletions = 0
    total = 0
    commit_total = 0


class CommitRepositoryUser(CommitUser):
    repository_name = None
