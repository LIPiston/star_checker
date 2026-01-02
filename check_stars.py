import requests
import os
import sys
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# 为本地开发加载 .env 文件中的环境变量
# 在 GitHub Actions 中，这将无害地失败或加载空内容，从而优先使用 Actions 自身设置的环境变量
load_dotenv()

# 从环境变量中读取 (可能是 Actions, .env, 或直接设置)
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

def fetch_all_listed_repos():
    """通过网页抓取获取所有公开 List 中的所有项目"""
    print("正在通过网页抓取获取所有公开 List...")
    listed_repos = set()
    
    # 1. 访问用户 Star 页面，找到所有 List 的链接
    stars_url = f"https://github.com/{USERNAME}?tab=stars"
    print(f"正在访问: {stars_url}")
    try:
        response = requests.get(stars_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找包含所有 List 链接的容器
        lists_container = soup.find('div', id='profile-lists-container')
        
        if not lists_container:
            print("警告: 在 Star 页面上没有找到 'profile-lists-container'。可能页面结构已更改。")
            return listed_repos

        # 从容器中找到所有指向 List 页面的链接
        list_links = lists_container.find_all('a', href=lambda href: href and href.startswith(f'/stars/{USERNAME}/lists/'))
        
        if not list_links:
            print("警告: 在 Star 页面上没有找到任何公开的 List。")
            return listed_repos

        list_urls = sorted(list(set(["https://github.com" + a['href'] for a in list_links])))
        print(f"共找到 {len(list_urls)} 个公开 List。")

        # 2. 遍历每个 List 页面，抓取项目
        for i, list_url in enumerate(list_urls):
            print(f"\n正在处理 List 页面 '{list_url.split('/')[-1]}' ({i+1}/{len(list_urls)})...")
            try:
                list_response = requests.get(list_url, timeout=30)
                list_response.raise_for_status()
                list_soup = BeautifulSoup(list_response.text, 'html.parser')

                # 修正选择器以匹配列表页面的HTML结构
                repo_tags = list_soup.select('div.col-12 h3 a')
                
                if not repo_tags:
                    print("警告: 在此 List 页面上没有找到任何项目。")
                    continue

                for tag in repo_tags:
                    repo_name = tag.get('href')
                    if repo_name and repo_name.startswith('/'):
                        repo_name = repo_name[1:] # 移除开头的 '/'
                        if len(repo_name.split('/')) == 2: # 确保是 'owner/repo' 格式
                            listed_repos.add(repo_name)
                            print(f".", end="", flush=True)

            except requests.exceptions.RequestException as e:
                print(f"抓取 List 页面 {list_url} 失败: {e}")

    except requests.exceptions.RequestException as e:
        print(f"访问 Star 主页面失败: {e}")
        raise # 如果主页都访问不了，直接抛出异常

    print(f"\n已从所有 List 中记录 {len(listed_repos)} 个独立的项目。")
    return listed_repos

# --- 查询语句 ---

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
            f.write("| 项目 (Repository) | 描述 (Description) |\n")
            f.write("| --- | --- |\n")
            for repo in sorted(uncategorized, key=lambda x: x['nameWithOwner'].lower()): # 按字母排序
                # 防御性地获取字段
                name = repo.get('nameWithOwner', '未知项目')
                url = repo.get('url', '#')
                desc = repo.get('description', '暂无描述')
                
                # 清理描述中的特殊字符
                if desc:
                    desc = desc.replace("\n", " ").replace("\r", " ").replace("|", "/")
                    if len(desc) > 80: desc = desc[:77] + "..."
                
                f.write(f"| [{name}]({url}) | {desc} |\n")
    
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
