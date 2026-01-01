## Star分类检查工具

这是一个用于检查您已加星（Star）但尚未分类到任何列表（List）中的 GitHub 项目的工具。

### 工作原理

项目内置了一个 GitHub Action 工作流 (`.github/workflows/check_stars.yml`)，该工作流会执行以下操作：

1.  **定期运行**: 默认情况下，此工作流每天在 UTC 时间午夜 0 点自动运行。
2.  **手动触发**: 您也可以随时在您仓库的 "Actions" 标签页中手动触发此工作流。
3.  **执行脚本**: 工作流会运行 Python 脚本 `check_stars.py`。
4.  **生成报告**: 脚本会获取您所有的 Star 项目和所有的 List，进行比对，并生成一个名为 `uncategorized_stars.md` 的 Markdown 文件，其中包含了所有未分类的项目。
5.  **自动提交**: 如果 `uncategorized_stars.md` 文件有变动，工作流会自动将其提交到您的仓库中。

### 如何使用

默认情况下，此工具通过 GitHub Actions 自动运行，无需额外配置。它使用 GitHub Actions 自带的 `GITHUB_TOKEN` 进行身份验证。

您只需要查看仓库根目录下的 `uncategorized_stars.md` 文件即可找到未分类的 Star 项目。

### 本地运行

如果您希望在本地计算机上运行此脚本，我们提供了 `test_local.sh` 脚本来简化流程。

**1. 准备工作:**

*   **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

*   **设置环境变量**:
    为了让脚本能够访问您的 GitHub 数据，您需要设置环境变量。脚本会优先从 `.env` 文件中读取配置。

    首先，创建一个名为 `.env` 的文件，内容如下：
    ```
    # .env
    GITHUB_TOKEN="your_personal_access_token"
    GITHUB_REPOSITORY_OWNER="your_github_username"
    ```

    您需要替换以下值：
    *   `your_github_username`: 您的 GitHub 用户名。
    *   `your_personal_access_token`: 您的 GitHub Personal Access Token (PAT)。您可以在 GitHub 的开发者设置中创建。此 Token 需要以下权限：

    **Classic Personal Access Token 权限要求:**
    *   `repo`: 用于读取您所有 Starred 项目（包括私有项目）。
    *   `read:user`: 用于读取您的 GitHub Lists。

    **Fine-grained Personal Access Token (推荐) 权限要求:**
    1.  **Repository access (仓库访问权限)**:
        *   选择 **"All repositories" (所有仓库)**。
    2.  **Permissions (权限设置)**:
        *   **Repository permissions (仓库权限)**:
            *   `Metadata`: 设置为 `Read-only`。
        *   **Account permissions (账户权限)**:
            *   `Profile`: 设置为 `Read-only`。

    > **注意**: `.env` 文件已被添加到 `.gitignore` 中，以防止您的敏感信息被意外提交。

**2. 运行本地测试脚本:**

完成上述配置后，直接运行 `test_local.sh` 脚本即可。
```bash
./test_local.sh
```
脚本将自动安装依赖（如果尚未安装）、检查 `.env` 文件，然后运行 `check_stars.py` 并生成或更新 `uncategorized_stars.md` 文件。