import requests
import os
import sys
import time

# 从 GitHub Actions 的环境变量中读取
TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER")

if not TOKEN or not USERNAME:
    print("错误: GITHUB_TOKEN 和 GITHUB_REPOSITORY_OWNER 环境变量未设置。")
    print("请确保在 GitHub Actions 环境中运行此脚本，并已设置正确的环境变量。")
    sys.exit(1)

def get_graphql_data(query, variables):
    """通用GraphQL请求函数"""
    headers = {"Authorization": f"bearer {TOKEN}"}
    for attempt in range(3): # 重试3次
        try:
            response = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=headers, timeout=30)
            response.raise_for_status() # 如果状态码不是2xx，则引发HTTPError
            data = response.json()
            if "errors" in data:
                print(f"GraphQL 查询出错: {data['errors']}")
                # 根据错误类型决定是否重试
                if any("RATE_LIMITED" in e.get('type', '') for e in data['errors']):
                    print("触发速率限制，等待60秒后重试...")
                    time.sleep(60)
                    continue
            return data
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败 (尝试 {attempt + 1}/3): {e}")
            time.sleep(5) # 等待5秒后重试
    raise Exception("多次尝试后 GraphQL 查询仍然失败。")


# --- 查询语句 ---

# 查询单个 List 的所有项目（包含分页）
list_items_query = """
query($listName: String!, $user: String!, $itemCursor: String) {
  user(login: $user) {
    lists(query: $listName, first: 1) {
      nodes {
        repositories(first: 100, after: $itemCursor) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            nameWithOwner
          }
        }
      }
    }
  }
}
"""

# 查询所有 Lists 的名称（包含分页）
lists_query = """
query($user: String!, $cursor: String) {
  user(login: $user) {
    lists(first: 100, after: $cursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
      }
    }
  }
}
"""

# 查询所有 Stars (包含分页参数)
stars_query = """
query($user: String!, $cursor: String) {
  user(login: $user) {
    starredRepositories(first: 100, after: $cursor, orderBy: {field: STARRED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        nameWithOwner
        url
        description
      }
    }
  }
}
"""

def fetch_all_listed_repos():
    """获取所有 List 中的所有项目"""
    print("正在获取所有 List...")
    list_names = []
    has_next_list = True
    list_cursor = None
    
    # 1. 获取所有 List 的名称
    while has_next_list:
        list_data = get_graphql_data(lists_query, {"user": USERNAME, "cursor": list_cursor})
        lists = list_data.get('data', {}).get('user', {}).get('lists', {})
        
        for lst in lists.get('nodes', []):
            list_names.append(lst['name'])
            
        has_next_list = lists.get('pageInfo', {}).get('hasNextPage', False)
        list_cursor = lists.get('pageInfo', {}).get('endCursor')
        print(f".", end="", flush=True)
    print(f"\n共找到 {len(list_names)} 个 List。")

    # 2. 遍历每个 List 获取其中的所有项目
    listed_repos = set()
    total_items = 0
    for i, name in enumerate(list_names):
        print(f"\n正在处理 List '{name}' ({i+1}/{len(list_names)})...")
        has_next_item = True
        item_cursor = None
        while has_next_item:
            item_data = get_graphql_data(list_items_query, {"user": USERNAME, "listName": name, "itemCursor": item_cursor})
            
            lists_nodes = item_data.get('data', {}).get('user', {}).get('lists', {}).get('nodes', [])
            items_node = {}
            if lists_nodes:
                items_node = lists_nodes[0].get('repositories', {})
            if not items_node:
                print(f"警告: 无法获取 List '{name}' 的项目，可能为空或API问题。")
                break # 跳出当前 list 的循环

            for item in items_node.get('nodes', []):
                if item and 'nameWithOwner' in item:
                    listed_repos.add(item['nameWithOwner'])
                    total_items += 1
            
            has_next_item = items_node.get('pageInfo', {}).get('hasNextPage', False)
            item_cursor = items_node.get('pageInfo', {}).get('endCursor')
            print(f".", end="", flush=True)

    print(f"\n已从所有 List 中记录 {len(listed_repos)} 个独立的项目。")
    return listed_repos


def fetch_all_stars():
    """获取用户所有 Star 的项目"""
    print("\n正在获取所有 Star 项目 (这可能需要一点时间)...")
    all_stars = []
    has_next = True
    cursor = None
    page_count = 0

    while has_next:
        page_count += 1
        print(f".", end="", flush=True)
        if page_count % 50 == 0: # 每50页换行
             print("")

        data = get_graphql_data(stars_query, {"user": USERNAME, "cursor": cursor})
        stars_data = data.get('data', {}).get('user', {}).get('starredRepositories', {})

        if not stars_data:
            print("警告: 无法获取 Star 数据。")
            break

        all_stars.extend(stars_data.get('nodes', []))
        
        has_next = stars_data.get('pageInfo', {}).get('hasNextPage', False)
        cursor = stars_data.get('pageInfo', {}).get('endCursor')

    print(f"\n共获取到 {len(all_stars)} 个 Star 项目。")
    return all_stars


def generate_markdown(uncategorized):
    """生成 Markdown 格式的报告"""
    filename = "uncategorized_stars.md"
    try:
        # 使用 'date -u' 获取 UTC 时间，更符合国际标准
        date_str = os.popen('date -u').read().strip()
    except:
        date_str = "无法获取时间"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 未分类 Stars 清单\n\n")
        f.write(f"> 生成于 UTC 时间: {date_str} | 总计: **{len(uncategorized)}** 个未分类项目\n\n")
        
        if not uncategorized:
            f.write("🎉 恭喜！所有 Star 的项目都已分类。\n")
        else:
            f.write("| 项目 (Repository) | 描述 (Description) | 操作 (Action) |\n")
            f.write("| --- | --- | --- |\n")
            for repo in sorted(uncategorized, key=lambda x: x['nameWithOwner'].lower()): # 按字母排序
                # 防御性地获取字段
                name = repo.get('nameWithOwner', '未知项目')
                url = repo.get('url', '#')
                desc = repo.get('description', '暂无描述')
                
                # 清理描述中的特殊字符
                if desc:
                    desc = desc.replace("\n", " ").replace("\r", " ").replace("|", "/")
                    if len(desc) > 80: desc = desc[:77] + "..."
                
                f.write(f"| [{name}]({url}) | {desc} | [在 GitHub 上查看]({url}) |\n")
    
    print(f"\n报告已生成: {filename}")

def main():
    """主程序"""
    try:
        listed_repos = fetch_all_listed_repos()
        all_stars = fetch_all_stars()
        
        uncategorized = [repo for repo in all_stars if repo.get('nameWithOwner') and repo['nameWithOwner'] not in listed_repos]

        generate_markdown(uncategorized)
        print("\n✅ 任务成功完成！")

    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        # 在 GitHub Actions 环境中，将错误写入 GITHUB_STEP_SUMMARY
        if "GITHUB_STEP_SUMMARY" in os.environ:
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
                f.write("## 脚本运行失败\n\n")
                f.write(f"错误详情: `{e}`\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
