# Paper Radar Bot 设计文档

## 目标

构建一个独立的小型 Python 项目：根据预设主题抓取最新 arXiv 论文，调用兼容 OpenAI 的模型生成中文总结，输出带日期的 Markdown 报告，并同时支持通过本地 `.bat` 文件运行和通过 GitHub Actions 自动运行。

## 范围

第一版有意保持精简，仅包含以下能力：

- 只从 arXiv API 抓取论文
- 按配置的检索关键词筛选论文
- 为每篇论文生成中文总结
- 每次运行输出一份 Markdown 报告到 `reports/`
- 提供 Windows `.bat` 一键运行入口
- 提供 GitHub Actions 定时运行与自动提交流程

第一版暂不包含以下内容：

- arXiv 以外的多源论文聚合
- 不同远程数据库之间的去重
- Web UI 或可视化面板
- 数据库存储
- 基于语义排序或引文关系的分析能力

## 用户体验

项目支持两种主要运行方式：

1. 在 Windows 本地通过 `run_paper_radar.bat` 运行
2. 将仓库推送到 GitHub 后，通过 Actions 定时运行

每次运行都会生成一份按日期命名的 Markdown 报告，例如 `reports/2026-06-21.md`。报告内容包括：

- 本次运行元信息
- 使用的检索主题
- 论文标题
- 作者
- 发布时间
- arXiv 链接
- 中文摘要
- 关键亮点
- 潜在应用方向

## 架构

代码库会拆分为职责清晰的小模块：

- `config.py`：加载环境变量并校验运行配置
- `models.py`：定义标准化论文记录和总结结果的数据结构
- `arxiv_client.py`：请求并解析 arXiv Atom 响应
- `summarizer.py`：调用兼容 OpenAI 的 Chat Completions API
- `renderer.py`：将标准化论文数据渲染为 Markdown
- `writer.py`：创建输出目录并保存报告
- `main.py`：总调度入口

这样可以把抓取、总结、渲染、写文件等关注点分离，后续如果需要替换某一部分，不必重写整条链路。

## 数据流

1. 从环境变量和可选的 `.env` 中加载配置
2. 使用配置的关键词和结果数量上限查询 arXiv
3. 将 API 响应标准化为内部论文记录
4. 为每篇论文生成结构化中文总结
5. 将所有论文记录渲染为一份按日期命名的 Markdown 报告
6. 将报告保存到 `reports/`

## 配置

第一版使用环境变量，并提供文档化的 `.env.example`。

必填项：

- `OPENAI_API_KEY`

可选项（带默认值）：

- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `ARXIV_QUERY`
- `ARXIV_MAX_RESULTS`
- `REPORT_TIMEZONE`
- `REPORT_LOCALE`

默认查询词会面向 AI 相关前沿主题，这样用户只要填入 API Key 就能直接运行。

## 错误处理

CLI 在配置缺失或无效时应尽早失败，并给出清晰提示。

- 缺少 API Key：直接退出，并输出可读错误信息
- arXiv 请求失败：退出，并输出状态码和简洁错误细节
- 单篇论文总结失败：保留论文信息，在总结部分标记失败，而不是让整次运行中断
- 文件写入失败：退出，并输出可读的文件系统错误信息

## 测试策略

第一版先覆盖稳定逻辑的单元测试：

- arXiv 响应解析为标准化记录
- 从标准化记录渲染 Markdown
- 输出路径生成与文件写入

外部 HTTP 调用在单元测试中不直接覆盖。第一版对这些集成路径以手动验证或 GitHub Actions 验证为主。

## 仓库结构

规划结构如下：

```text
paper_radar_bot/
  .github/workflows/
  docs/superpowers/specs/
  reports/
  src/paper_radar_bot/
  tests/
  .env.example
  README.md
  requirements.txt
  run_paper_radar.bat
```

## 方案权衡

### 方案 A：仅本地脚本

优点：

- 配置最简单
- 不需要维护 GitHub 工作流

缺点：

- 无法自动更新
- 没有现成的发布路径

### 方案 B：Python CLI + `.bat` + GitHub Actions

优点：

- 在 Windows 本地使用体验更好
- 方便做定时自动化
- 同一套 Python 入口同时服务本地运行和云端执行

缺点：

- 配置面稍微更大一些

推荐选择方案 B，因为它既保留了本地一键运行能力，也不牺牲 GitHub 上的自动更新能力。

### 方案 C：完整 Web 应用

优点：

- 浏览和交互体验更丰富

缺点：

- 范围明显更大
- 对第一阶段目标来说没有必要

## 验收标准

第一版在满足以下条件时视为成功：

- 用户可以填写 `.env`
- 用户可以运行 `run_paper_radar.bat`
- 脚本会在 `reports/` 下生成带日期的 Markdown 报告
- 报告中包含抓取到的论文元信息和中文总结
- 仓库中包含 GitHub Actions 工作流，用于定时执行和自动提交
- 解析、渲染、写文件这三类单元测试可在本地通过
