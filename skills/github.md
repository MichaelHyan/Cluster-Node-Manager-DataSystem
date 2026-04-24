---
name: github
description: "使用 gh 处理 GitHub 问题、PR 状态、CI/日志、评论、审查、发布和 API 查询。"
metadata:
  {
    "openclaw":
      {
        "emoji": "🐙",
        "requires": { "bins": ["gh"] },
        "install":
          [
            {
              "id": "brew",
              "kind": "brew",
              "formula": "gh",
              "bins": ["gh"],
              "label": "安装 GitHub CLI (brew)",
            },
            {
              "id": "apt",
              "kind": "apt",
              "package": "gh",
              "bins": ["gh"],
              "label": "安装 GitHub CLI (apt)",
            },
          ],
      },
  }
---

# GitHub 技能

使用 `gh` CLI 与 GitHub 仓库、问题和 PR 交互。

## 何时使用

✅ **在以下情况下使用此技能：**

- 检查 PR 状态、审查或合并准备情况
- 查看 CI/工作流运行状态和日志
- 创建、关闭或评论问题
- 创建或合并拉取请求
- 查询 GitHub API 以获取仓库数据
- 列出仓库、发布版本或协作者

## 何时不使用

❌ **在以下情况下不要使用此技能：**

- 本地 git 操作（提交、推送、拉取、分支）→ 直接使用 `git`
- 非 GitHub 仓库（GitLab、Bitbucket、自托管）→ 使用不同的 CLI
- 克隆仓库 → 使用 `git clone`
- 审查实际代码更改 → 使用 `coding-agent` 技能
- 复杂的多文件差异 → 使用 `coding-agent` 或直接读取文件

## 设置

```bash
# 身份验证（一次性）
gh auth login

# 验证
gh auth status
```

## 常用命令

### 拉取请求

```bash
# 列出 PR
gh pr list --repo owner/repo

# 检查 CI 状态
gh pr checks 55 --repo owner/repo

# 查看 PR 详情
gh pr view 55 --repo owner/repo

# 创建 PR
gh pr create --title "feat: 添加功能" --body "描述"

# 合并 PR
gh pr merge 55 --squash --repo owner/repo
```

### 问题

```bash
# 列出问题
gh issue list --repo owner/repo --state open

# 创建问题
gh issue create --title "Bug: 某些功能损坏" --body "详细信息..."

# 关闭问题
gh issue close 42 --repo owner/repo
```

### CI/工作流运行

```bash
# 列出最近的运行
gh run list --repo owner/repo --limit 10

# 查看特定运行
gh run view <run-id> --repo owner/repo

# 仅查看失败步骤的日志
gh run view <run-id> --repo owner/repo --log-failed

# 重新运行失败的作业
gh run rerun <run-id> --failed --repo owner/repo
```

### API 查询

```bash
# 获取具有特定字段的 PR
gh api repos/owner/repo/pulls/55 --jq '.title, .state, .user.login'

# 列出所有标签
gh api repos/owner/repo/labels --jq '.[].name'

# 获取仓库统计信息
gh api repos/owner/repo --jq '{stars: .stargazers_count, forks: .forks_count}'
```

## JSON 输出

大多数命令支持 `--json` 以使用 `--jq` 过滤进行结构化输出：

```bash
gh issue list --repo owner/repo --json number,title --jq '.[] | "\(.number): \(.title)"'
gh pr list --json number,title,state,mergeable --jq '.[] | select(.mergeable == "MERGEABLE")'
```

## 模板

### PR 审查摘要

```bash
# 获取 PR 概览以进行审查
PR=55 REPO=owner/repo
echo "## PR #$PR 摘要"
gh pr view $PR --repo $REPO --json title,body,author,additions,deletions,changedFiles \
  --jq '"**\(.title)** by @\(.author.login)\n\n\(.body)\n\n📊 +\(.additions) -\(.deletions) across \(.changedFiles) files"'
gh pr checks $PR --repo $REPO
```

### 问题分类

```bash
# 快速问题分类视图
gh issue list --repo owner/repo --state open --json number,title,labels,createdAt \
  --jq '.[] | "[\(.number)] \(.title) - \([.labels[].name] | join(", ")) (\(.createdAt[:10]))"'
```

## 注意事项

- 当不在 git 目录中时，始终指定 `--repo owner/repo`
- 直接使用 URL：`gh pr view https://github.com/owner/repo/pull/55`
- 适用速率限制；对重复查询使用 `gh api --cache 1h`
