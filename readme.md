## Star分类检查工具

这是一个用于检查您已加星（Star）但尚未分类到任何列表（List）中的 GitHub 项目的工具。

### 工作原理

项目内置了一个 GitHub Action 工作流 (`.github/workflows/check_stars.yml`)，该工作流会执行以下操作：

1.  **定期运行**: 默认情况下，此工作流每天在 UTC 时间午夜 0 点自动运行。
2.  **手动触发**: 您也可以随时在您仓库的 "Actions" 标签页中手动触发此工作流。
3.  **执行脚本**: 工作流会运行位于 `star_checker/` 目录下的 Python 脚本。
4.  **生成报告**: 脚本会获取您所有的 Star 项目和所有的 List，进行比对，并生成一个名为 `uncategorized_stars.md` 的 Markdown 文件，其中包含了所有未分类的项目。
5.  **自动提交**: 如果 `uncategorized_stars.md` 文件有变动，工作流会自动将其提交到您的仓库中。

### 如何使用

此工具无需额外配置。它使用 GitHub Actions 自带的 `GITHUB_TOKEN` 进行身份验证。

您只需要查看仓库根目录下的 `uncategorized_stars.md` 文件即可找到未分类的 Star 项目。
