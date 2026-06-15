# Knowledge Work Plugins — Code Wiki

> **项目名称**: Knowledge Work Plugins  
> **维护者**: Anthropic  
> **许可证**: Apache 2.0  
> **仓库**: [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)  
> **文档生成日期**: 2026-06-15

---

## 目录

1. [项目概述](#1-项目概述)
2. [整体架构](#2-整体架构)
3. [目录结构](#3-目录结构)
4. [插件体系结构](#4-插件体系结构)
5. [核心市场注册表](#5-核心市场注册表)
6. [内置插件（Vendored Plugins）详解](#6-内置插件vendored-plugins详解)
7. [合作伙伴插件（Partner-built Plugins）详解](#7-合作伙伴插件partner-built-plugins详解)
8. [Skill 技能系统](#8-skill-技能系统)
9. [Command 命令系统](#9-command-命令系统)
10. [MCP 连接器体系](#10-mcp-连接器体系)
11. [CI/CD 工作流](#11-cicd-工作流)
12. [安全审查策略](#12-安全审查策略)
13. [依赖关系](#13-依赖关系)
14. [项目运行方式](#14-项目运行方式)
15. [关键文件索引](#15-关键文件索引)

---

## 1. 项目概述

### 1.1 项目定位

**Knowledge Work Plugins** 是一个面向 Claude（Anthropic 的 AI 助手）的插件市场，旨在将 Claude 转变为不同角色的专业领域助手。该项目同时兼容 [Claude Cowork](https://claude.com/product/cowork)（Anthropic 的桌面端智能代理应用）和 [Claude Code](https://claude.com/product/claude-code)（命令行 AI 编程助手）。

### 1.2 核心设计理念

- **文件驱动**: 所有插件均为纯 Markdown + JSON 文件，无代码、无基础设施、无构建步骤
- **工具无关**: 插件使用占位符（如 `~~CRM`、`~~chat`）描述工作流，而非绑定特定产品
- **渐进增强**: 每个插件独立运行即可工作，连接外部工具后获得"超能力"
- **可定制化**: 用户可替换连接器、添加公司上下文、调整工作流、构建新插件

### 1.3 技术栈

| 层级 | 技术 |
|------|------|
| 插件定义 | Markdown (SKILL.md) + YAML Frontmatter |
| 配置清单 | JSON (plugin.json, .mcp.json, marketplace.json) |
| 连接协议 | MCP (Model Context Protocol) |
| 脚本扩展 | Python (部分插件含 scripts/) |
| CI/CD | GitHub Actions |
| 安全审查 | Claude API（自动策略扫描） |

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Claude Cowork / Claude Code                   │
│                          （AI 助手运行时）                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     Marketplace Registry                       │   │
│  │               (.claude-plugin/marketplace.json)                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │   │
│  │  │  Vendored    │  │  Partner-    │  │  External         │    │   │
│  │  │  Plugins     │  │  built       │  │  (URL + SHA)      │    │   │
│  │  │  (./path)    │  │  Plugins     │  │                   │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      Plugin Structure                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │   │
│  │  │ plugin.json │  │  .mcp.json │  │  commands/ │              │   │
│  │  │  (Manifest) │  │ (Connectors)│  │  (Slash    │              │   │
│  │  │             │  │            │  │  Commands) │              │   │
│  │  └────────────┘  └────────────┘  └────────────┘              │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐              │   │
│  │  │  skills/    │  │  agents/   │  │ settings/  │              │   │
│  │  │  (Domain    │  │  (Sub-     │  │  (Local    │              │   │
│  │  │  Knowledge) │  │  Agents)   │  │  Config)   │              │   │
│  │  └────────────┘  └────────────┘  └────────────┘              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    External MCP Servers                        │   │
│  │  Slack │ HubSpot │ Notion │ Jira │ Snowflake │ GitHub │ ...   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       CI/CD Pipeline (GitHub Actions)                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  scan-plugins    │  │  bump-plugin-    │  │  check-mcp-urls   │   │
│  │  (安全策略审查)    │  │  shas (SHA 更新)  │  │  (MCP 存活检查)   │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│  ┌──────────────────┐                                                │
│  │  revert-failed-  │                                                │
│  │  bumps (回滚失败)  │                                                │
│  └──────────────────┘                                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. 目录结构

```
knowledge-work-plugins/
│
├── .claude-plugin/
│   └── marketplace.json              # 中心市场注册表（所有插件索引）
│
├── .github/
│   ├── policy/
│   │   ├── prompt.md                 # 安全审查策略提示词
│   │   └── schema.json               # 策略审查结果 JSON Schema
│   └── workflows/
│       ├── scan-plugins.yml          # 插件安全策略扫描
│       ├── bump-plugin-shas.yml      # 外部插件 SHA 自动更新
│       ├── check-mcp-urls.yml        # MCP 服务 URL 存活检查
│       └── revert-failed-bumps.yml   # 回滚失败的 SHA 更新
│
├── productivity/                     # 内置插件：生产力
├── sales/                            # 内置插件：销售
├── customer-support/                 # 内置插件：客户支持
├── product-management/               # 内置插件：产品管理
├── marketing/                        # 内置插件：市场营销
├── legal/                            # 内置插件：法务
├── finance/                          # 内置插件：财务
├── data/                             # 内置插件：数据
├── enterprise-search/                # 内置插件：企业搜索
├── engineering/                      # 内置插件：工程
├── human-resources/                  # 内置插件：人力资源
├── design/                           # 内置插件：设计
├── operations/                       # 内置插件：运营
├── bio-research/                     # 内置插件：生物研究
├── cowork-plugin-management/         # 内置插件：插件管理
├── small-business/                   # 内置插件：小企业
├── pdf-viewer/                       # 内置插件：PDF 查看器
│
├── partner-built/                    # 合作伙伴构建的插件
│   ├── apollo/                       # Apollo.io（销售智能）
│   ├── brand-voice/                  # Brand Voice（品牌声音，Tribe AI）
│   ├── common-room/                  # Common Room（GTM 智能）
│   ├── slack/                        # Slack（Salesforce 官方）
│   └── zoom-plugin/                  # Zoom（Zoom 官方）
│
├── LICENSE                           # Apache 2.0
└── README.md                         # 项目说明
```

---

## 4. 插件体系结构

### 4.1 标准插件目录结构

每个插件遵循统一的目录结构：

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json                   # 插件清单（必需）
├── .mcp.json                         # MCP 服务器连接配置（可选）
├── commands/                         # 斜杠命令（用户显式调用）
│   └── command-name.md
├── skills/                           # 技能（AI 自动激活）
│   └── skill-name/
│       ├── SKILL.md                  # 技能定义（必需）
│       ├── scripts/                  # Python 辅助脚本（可选）
│       │   └── *.py
│       └── references/               # 参考文档（可选）
│           └── *.md
├── agents/                           # 子代理定义（可选）
│   └── agent-name.md
├── settings/                         # 本地配置模板（可选）
│   └── settings.local.md.example
├── CONNECTORS.md                     # 连接器说明文档
├── README.md                         # 插件说明文档
└── LICENSE / LICENSE.txt             # 许可证
```

### 4.2 plugin.json 清单格式

```json
{
  "name": "plugin-name",           // 插件唯一标识符（必需）
  "version": "1.2.0",              // 语义化版本号（必需）
  "description": "...",            // 插件描述（必需）
  "author": {                      // 作者信息（必需）
    "name": "Anthropic"
  },
  "homepage": "https://...",       // 主页（可选）
  "repository": "https://...",     // 仓库地址（可选）
  "license": "MIT",                // 许可证（可选）
  "keywords": [...]                // 关键词（可选）
}
```

### 4.3 SKILL.md 技能定义格式

每个技能文件使用 YAML Frontmatter + Markdown 格式：

```markdown
---
name: skill-name                    # 技能唯一标识符
description: >-                     # 触发条件 + 功能描述
  Provide X when user does Y.
  Trigger with "keyword1", "keyword2", or "phrase3".
argument-hint: "<arg description>"  # 可选：参数提示
user-invocable: false               # 可选：是否允许用户手动调用
---

# Skill Title

## How It Works
...

## Execution Flow
...
```

### 4.4 .mcp.json 连接器配置格式

```json
{
  "mcpServers": {
    "server-name": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "oauth": {                          // 可选
        "clientId": "...",
        "callbackPort": 3118
      }
    }
  }
}
```

---

## 5. 核心市场注册表

### 5.1 marketplace.json

**文件路径**: [.claude-plugin/marketplace.json](file:///workspace/.claude-plugin/marketplace.json)

这是整个插件生态的中心注册表，定义了所有可用插件的元数据。

#### 结构

```json
{
  "name": "knowledge-work-plugins",
  "owner": { "name": "Anthropic" },
  "plugins": [
    {
      "name": "plugin-id",
      "displayName": "Display Name",
      "source": "./relative-path",        // 内置插件
      // 或
      "source": {                          // 外部插件
        "source": "url" | "git-subdir",
        "url": "https://github.com/...",
        "sha": "commit-hash",
        "path": "subdir/path",            // git-subdir 类型
        "ref": "main"                      // git-subdir 类型
      },
      "description": "...",
      "category": "category-name",         // 可选
      "author": { "name": "..." },         // 可选
      "homepage": "https://..."            // 可选
    }
  ]
}
```

#### 插件来源类型

| 来源类型 | source 字段 | 说明 |
|----------|------------|------|
| **内置（Vendored）** | `"./relative-path"` (字符串) | 插件文件直接在本仓库中维护 |
| **外部 URL** | `{"source": "url", "url": "...", "sha": "..."}` | 从外部 Git 仓库克隆整个仓库 |
| **外部 Git 子目录** | `{"source": "git-subdir", "url": "...", "path": "...", "ref": "...", "sha": "..."}` | 从外部仓库中提取特定子目录 |

#### 注册的插件统计

| 类别 | 数量 |
|------|------|
| 内置插件（Anthropic 维护） | 17 |
| 合作伙伴插件 | 5 |
| 外部第三方插件 | ~25 |
| **总计** | **~50** |

---

## 6. 内置插件（Vendored Plugins）详解

### 6.1 productivity — 生产力

[plugin.json](file:///workspace/productivity/.claude-plugin/plugin.json)

**描述**: 管理任务、规划日程、构建工作记忆上下文。与日历、邮件、聊天同步。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `task-management` | 基于 TASKS.md 文件的简单任务管理，支持增删改查 |
| `memory-management` | 工作记忆管理，保存和检索重要上下文 |
| `start` | 初始化生产力系统设置 |
| `update` | 更新工作记忆和任务状态 |

**MCP 连接器**: Slack, Notion, Asana, Linear, Jira, Monday, ClickUp, Microsoft 365

### 6.2 sales — 销售

[plugin.json](file:///workspace/sales/.claude-plugin/plugin.json)

**描述**: 潜在客户挖掘、外联撰写、交易策略。支持通话准备、管道管理和个性化消息。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `account-research` | 公司/联系人深度研究，包括新闻、融资、招聘信号、关键人物 |
| `call-prep` | 销售通话准备，包含客户背景、参会者研究、议程建议、提问清单 |
| `daily-briefing` | 每日销售简报，优先级排序 |
| `draft-outreach` | 研究驱动的个性化外联邮件和 LinkedIn 消息 |
| `competitive-intelligence` | 竞品情报，产品对比、差异化矩阵、销售话术 |
| `create-an-asset` | 销售资产生成（落地页、演示文稿、一页纸等），含 7 个阶段工作流 |

**命令列表**:

| 命令 | 描述 |
|------|------|
| `/call-summary` | 处理通话笔记/转录，提取行动项、草拟跟进邮件 |
| `/forecast` | 生成加权销售预测 |
| `/pipeline-review` | 管道健康分析，优先级排序，风险标记 |

**MCP 连接器**: Slack, HubSpot, Close, Clay, ZoomInfo, Apollo, Notion, Atlassian, Fireflies, Microsoft 365, Outlook, SimilarWeb

### 6.3 customer-support — 客户支持

[plugin.json](file:///workspace/customer-support/.claude-plugin/plugin.json)

**描述**: 工单分类、回复草拟、问题升级、知识库构建。研究客户上下文，将已解决问题转为自助服务内容。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `ticket-triage` | 工单分类和优先级排序 |
| `draft-response` | 客户回复草拟 |
| `customer-escalation` | 问题升级流程管理 |
| `customer-research` | 客户上下文研究 |
| `kb-article` | 知识库文章创建 |

**MCP 连接器**: Slack, Intercom, HubSpot, Guru, Jira, Notion, Microsoft 365

### 6.4 product-management — 产品管理

[plugin.json](file:///workspace/product-management/.claude-plugin/plugin.json)

**描述**: 撰写功能规格、规划路线图、综合用户研究。保持利益相关者更新，跟踪竞争格局。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `write-spec` | 编写功能规格/PRD，含问题陈述、目标、用户故事、需求分类、成功指标 |
| `roadmap-update` | 路线图更新 |
| `sprint-planning` | Sprint 规划 |
| `stakeholder-update` | 利益相关者更新 |
| `synthesize-research` | 用户研究综合 |
| `competitive-brief` | 竞品简报 |
| `metrics-review` | 指标回顾 |
| `product-brainstorming` | 产品头脑风暴 |

**命令列表**:

| 命令 | 描述 |
|------|------|
| `/brainstorm` | 产品头脑风暴 |

**MCP 连接器**: Slack, Linear, Asana, Monday, ClickUp, Jira, Notion, Figma, Amplitude, Pendo, Intercom, Fireflies

### 6.5 marketing — 市场营销

[plugin.json](file:///workspace/marketing/.claude-plugin/plugin.json)

**描述**: 内容创作、活动规划、跨渠道性能分析。维护品牌声音一致性，跟踪竞争对手，报告效果。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `content-creation` | 内容创作 |
| `draft-content` | 内容草拟 |
| `campaign-plan` | 活动策划 |
| `brand-review` | 品牌审查 |
| `competitive-brief` | 竞品简报 |
| `email-sequence` | 邮件序列 |
| `performance-report` | 性能报告 |
| `seo-audit` | SEO 审计 |

**MCP 连接器**: Slack, Canva, Figma, HubSpot, Amplitude, Notion, Ahrefs, SimilarWeb, Klaviyo

### 6.6 legal — 法务

[plugin.json](file:///workspace/legal/.claude-plugin/plugin.json)

**描述**: 加速合同审查、NDA 分类和合规工作流。起草法律简报，组织先例研究，管理机构知识。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `review-contract` | 合同审查 |
| `triage-nda` | NDA 分类处理 |
| `compliance-check` | 合规检查 |
| `legal-risk-assessment` | 法律风险评估 |
| `brief` | 法律简报 |
| `legal-response` | 法律回复 |
| `meeting-briefing` | 会议简报 |
| `signature-request` | 签名请求 |
| `vendor-check` | 供应商检查 |

**MCP 连接器**: Slack, Box, Egnyte, Jira, Microsoft 365

### 6.7 finance — 财务

[plugin.json](file:///workspace/finance/.claude-plugin/plugin.json)

**描述**: 简化财务和会计工作流，从日记账分录和对账到财务报表和差异分析。加速审计准备、月末关账和账簿管理。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `reconciliation` | 账户对账（GL-to-subledger、银行对账、公司间对账），含对账项目分类、账龄分析、升级阈值 |
| `journal-entry` | 日记账分录 |
| `journal-entry-prep` | 日记账分录准备 |
| `financial-statements` | 财务报表 |
| `variance-analysis` | 差异分析 |
| `close-management` | 关账管理 |
| `audit-support` | 审计支持 |
| `sox-testing` | SOX 测试 |

**MCP 连接器**: Snowflake, Databricks, BigQuery, Slack, Microsoft 365

### 6.8 data — 数据

[plugin.json](file:///workspace/data/.claude-plugin/plugin.json)

**描述**: 编写 SQL、探索数据集、生成洞察。构建可视化和仪表盘，将原始数据转化为清晰的故事。

**版本**: 1.1.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `sql-queries` | SQL 查询（含 Snowflake/BigQuery/Redshift/Databricks/PostgreSQL 方言参考） |
| `explore-data` | 数据集探索，含质量评估框架 |
| `build-dashboard` | 交互式 HTML 仪表盘构建（含完整模板和代码模式） |
| `create-viz` | 可视化创建 |
| `data-visualization` | 数据可视化 |
| `analyze` | 数据分析 |
| `statistical-analysis` | 统计分析 |
| `validate-data` | 数据验证 |
| `write-query` | 查询编写 |
| `data-context-extractor` | 数据上下文提取器（含领域模板、SQL 方言参考） |

**MCP 连接器**: Snowflake, Databricks, BigQuery, Hex, Amplitude, Atlassian, Definite

### 6.9 enterprise-search — 企业搜索

[plugin.json](file:///workspace/enterprise-search/.claude-plugin/plugin.json)

**描述**: 跨所有公司工具统一搜索。在邮件、聊天、文档和 Wiki 中查找任何内容，无需切换应用。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `search` | 跨工具搜索 |
| `search-strategy` | 搜索策略制定 |
| `digest` | 搜索摘要 |
| `knowledge-synthesis` | 知识综合 |
| `source-management` | 源管理 |

**MCP 连接器**: Slack, Notion, Guru, Jira, Asana, Microsoft 365

### 6.10 engineering — 工程

[plugin.json](file:///workspace/engineering/.claude-plugin/plugin.json)

**描述**: 简化工程工作流——站会、代码审查、架构决策、事件响应和技术文档。可与现有工具配合或独立使用。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `code-review` | 代码审查（安全、性能、正确性、可维护性），含 OWASP top 10 检查 |
| `architecture` | 架构设计 |
| `debug` | 调试 |
| `testing-strategy` | 测试策略 |
| `system-design` | 系统设计 |
| `documentation` | 文档编写 |
| `standup` | 站会 |
| `deploy-checklist` | 部署检查清单 |
| `incident-response` | 事件响应 |
| `tech-debt` | 技术债务管理 |

**MCP 连接器**: Slack, Linear, Asana, Atlassian, Notion, GitHub, PagerDuty, Datadog, Google Calendar, Gmail

### 6.11 human-resources — 人力资源

[plugin.json](file:///workspace/human-resources/.claude-plugin/plugin.json)

**描述**: 简化人员运营——招聘、入职、绩效评估、薪酬分析和政策指导。保持合规并确保团队高效运转。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `recruiting-pipeline` | 招聘管道管理 |
| `interview-prep` | 面试准备 |
| `draft-offer` | Offer 草拟 |
| `onboarding` | 入职管理 |
| `performance-review` | 绩效评估 |
| `comp-analysis` | 薪酬分析 |
| `org-planning` | 组织规划 |
| `people-report` | 人员报告 |
| `policy-lookup` | 政策查找 |

**MCP 连接器**: 多种 HR 工具

### 6.12 design — 设计

[plugin.json](file:///workspace/design/.claude-plugin/plugin.json)

**描述**: 加速设计工作流——设计评审、设计系统管理、UX 文案、无障碍审计、研究综合和开发交接。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `design-critique` | 设计评审 |
| `design-system` | 设计系统管理 |
| `design-handoff` | 设计交接 |
| `accessibility-review` | 无障碍审计 |
| `user-research` | 用户研究 |
| `research-synthesis` | 研究综合 |
| `ux-copy` | UX 文案 |

**MCP 连接器**: Figma 等设计工具

### 6.13 operations — 运营

[plugin.json](file:///workspace/operations/.claude-plugin/plugin.json)

**描述**: 优化业务运营——供应商管理、流程文档、变更管理、容量规划和合规跟踪。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `process-doc` | 流程文档 |
| `process-optimization` | 流程优化 |
| `change-request` | 变更请求 |
| `capacity-plan` | 容量规划 |
| `risk-assessment` | 风险评估 |
| `compliance-tracking` | 合规跟踪 |
| `vendor-review` | 供应商审查 |
| `status-report` | 状态报告 |
| `runbook` | Runbook 管理 |

**MCP 连接器**: 多种运营工具

### 6.14 bio-research — 生物研究

[plugin.json](file:///workspace/bio-research/.claude-plugin/plugin.json)

**描述**: 连接临床前研究工具和数据库，加速早期生命科学研发。

**版本**: 1.2.0

**技能列表**:

| 技能 | 描述 |
|------|------|
| `single-cell-rna-qc` | 单细胞 RNA 质量控制（含 Python 脚本：qc_core.py, qc_plotting.py, qc_analysis.py） |
| `scvi-tools` | scVI 工具套件（数据准备、模型训练、聚类、差异表达、标签转移等，含 8 个 Python 脚本） |
| `nextflow-development` | Nextflow 管道开发（含环境检查、数据类型检测、样本表生成等脚本） |
| `instrument-data-to-allotrope` | 仪器数据到 ASM 格式转换 |
| `scientific-problem-selection` | 科学问题选择框架（9 个参考文档，含直觉泵、风险评估、优化函数等） |

**MCP 连接器**: PubMed, BioRender, bioRxiv, ClinicalTrials.gov, ChEMBL, Synapse, Wiley, Owkin, Open Targets, Benchling

### 6.15 cowork-plugin-management — 插件管理

[plugin.json](file:///workspace/cowork-plugin-management/.claude-plugin/plugin.json)

**描述**: 创建、定制和管理插件，适配组织的工具和工作流。配置 MCP 服务器，调整插件行为，适配模板。

**版本**: 0.2.2

**技能列表**:

| 技能 | 描述 |
|------|------|
| `create-cowork-plugin` | 创建新插件（含组件模式参考和示例插件） |
| `cowork-plugin-customizer` | 定制现有插件（含 MCP 服务器参考和搜索策略） |

### 6.16 small-business — 小企业

[plugin.json](file:///workspace/small-business/.claude-plugin/plugin.json)

**描述**: 预构建的小企业工作流，使用 QuickBooks、PayPal、HubSpot、Docusign 等工具。涉及资金或客户的操作需用户逐项审批。

**版本**: 1.2.0

**技能列表**（部分）:

| 技能 | 描述 |
|------|------|
| `smb-router` | 小企业路由 |
| `smb-onboard` | 小企业入职 |
| `business-pulse` | 业务脉搏 |
| `cash-flow-snapshot` | 现金流快照 |
| `close-month` | 月末关账 |
| `monday-brief` / `friday-brief` | 周一/周五简报 |
| `plan-payroll` | 薪资规划 |
| `tax-prep` | 税务准备 |
| `contract-review` | 合同审查 |
| `job-post-builder` | 招聘发布构建器 |
| `run-campaign` | 活动运营 |
| 及其他 20+ 个技能 |

### 6.17 pdf-viewer — PDF 查看器

[plugin.json](file:///workspace/pdf-viewer/.claude-plugin/plugin.json)

**描述**: 在实时交互式查看器中查看、注释和签署 PDF。标记合同、填写表单、盖章批准、放置签名——然后下载注释副本。

**版本**: 0.2.0

**命令列表**:

| 命令 | 描述 |
|------|------|
| `/open` | 打开 PDF |
| `/annotate` | 注释 |
| `/fill-form` | 填写表单 |
| `/sign` | 签署 |

**技能列表**: `view-pdf`

---

## 7. 合作伙伴插件（Partner-built Plugins）详解

### 7.1 apollo — Apollo.io

[plugin.json](file:///workspace/partner-built/apollo/.claude-plugin/plugin.json)

**提供方**: Apollo.io  
**描述**: 3 个预构建技能，将多个 Apollo API 链接为完整销售工作流。通过姓名、邮箱或 LinkedIn URL 丰富联系人；用自然语言描述 ICP 获取排序线索；一站式查找、丰富并加载联系人到序列中。

**技能列表**:

| 技能 | 描述 |
|------|------|
| `enrich-lead` | 线索丰富 |
| `prospect` | 潜在客户挖掘 |
| `sequence-load` | 序列加载 |

### 7.2 brand-voice — 品牌声音

[plugin.json](file:///workspace/partner-built/brand-voice/.claude-plugin/plugin.json)

**提供方**: Tribe AI  
**描述**: 将散落的品牌材料自动转化为可执行的 AI 护栏。在 Notion、Google Drive、Confluence、Gong、Slack 和会议转录中搜索，提炼品牌信号，应用到所有 AI 生成内容中。

**技能列表**:

| 技能 | 描述 |
|------|------|
| `brand-voice-enforcement` | 品牌声音强制执行 |
| `discover-brand` | 品牌发现 |
| `guideline-generation` | 指南生成 |

**子代理**: content-generation, conversation-analysis, discover-brand, document-analysis, quality-assurance

### 7.3 common-room — Common Room

[plugin.json](file:///workspace/partner-built/common-room/.claude-plugin/plugin.json)

**提供方**: Common Room  
**描述**: 将 Common Room 变为 GTM 副驾驶。研究客户和联系人，准备通话，撰写个性化外联。

**技能列表**: `account-research`, `call-prep`, `compose-outreach`, `contact-research`, `prospect`, `weekly-prep-brief`

**命令**: `/generate-account-plan`, `/weekly-brief`

### 7.4 slack — Slack

[plugin.json](file:///workspace/partner-built/slack/.claude-plugin/plugin.json)

**提供方**: Salesforce  
**描述**: 官方 Slack MCP 服务器，用于交互和协作工作流。在 Slack 中展示洞察、草拟消息、与团队互动。

**技能列表**: `slack-messaging`, `slack-search`

**命令**: `/channel-digest`, `/draft-announcement`, `/find-discussions`, `/standup`, `/summarize-channel`

### 7.5 zoom-plugin — Zoom

[plugin.json](file:///workspace/partner-built/zoom-plugin/.claude-plugin/plugin.json)

**提供方**: Zoom  
**描述**: 规划、构建和调试 Zoom 集成，涵盖 REST API、Meeting SDK、Video SDK、Webhooks、Bots 和 MCP 工作流。

**版本**: 1.1.0

**技能列表**（30+ 个技能）:

| 类别 | 技能 |
|------|------|
| **规划** | `plan-zoom-integration`, `plan-zoom-product`, `choose-zoom-approach`, `design-mcp-workflow` |
| **SDK 开发** | `meeting-sdk`（含 android/ios/macos/windows/linux/web/electron/react-native/unreal 子技能）、`video-sdk`、`zoom-apps-sdk` |
| **API** | `rest-api`, `webhooks`, `websockets` |
| **OAuth** | `oauth`（含概念、示例、故障排除）、`setup-zoom-oauth` |
| **其他** | `build-zoom-bot`, `build-zoom-meeting-app`, `cobrowse-sdk`, `phone`, `team-chat`, `ui-toolkit`, `virtual-agent`, `probe-sdk`, `rivet-sdk`, `rtms`, `scribe`, `contact-center` |
| **调试** | `debug-zoom`, `debug-zoom-integration` |
| **MCP** | `setup-zoom-mcp`, `zoom-mcp` |

---

## 8. Skill 技能系统

### 8.1 技能定义规范

技能是插件的核心组件，定义了 AI 助手在特定领域中自动激活的专业知识和工作流。

#### 触发机制

- **自动触发**: 当用户输入匹配技能 `description` 字段中的触发词时，AI 自动加载对应技能
- **手动调用**: 通过斜杠命令调用（如 `/sales:call-prep`）
- **上下文触发**: 当 AI 判断当前对话上下文需要特定领域知识时自动激活

#### 技能文件结构

```
skills/skill-name/
├── SKILL.md              # 技能定义（必需）
├── scripts/              # 辅助脚本（可选）
│   └── *.py
└── references/           # 参考文档（可选）
    └── *.md
```

### 8.2 SKILL.md 规范

#### Frontmatter 字段

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | 是 | 技能唯一标识符 |
| `description` | 是 | 技能描述 + 触发关键词 |
| `argument-hint` | 否 | 参数提示文本 |
| `user-invocable` | 否 | 是否允许用户手动调用（默认 true） |

#### 内容结构

1. **标题**: 一级标题，技能名称
2. **工作原理**: 说明 Standalone vs Supercharged 模式
3. **执行流程**: 分步骤的执行逻辑
4. **输出格式**: 标准化的输出模板
5. **连接器**: 可选的外部工具集成说明
6. **最佳实践**: 使用建议和技巧

### 8.3 技能设计模式

#### 模式一：Standalone + Supercharged

```markdown
## How It Works

┌─────────────────────────────────────────┐
│  ALWAYS (works standalone)              │
│  ✓ Basic capability via web search      │
│  ✓ User input drives the workflow       │
├─────────────────────────────────────────┤
│  SUPERCHARGED (when tools connected)    │
│  + CRM: additional context             │
│  + Email: related communication        │
└─────────────────────────────────────────┘
```

#### 模式二：分步骤执行流程

```markdown
## Execution Flow

### Step 1: Gather Context
### Step 2: Research Supplement
### Step 3: Synthesize & Generate
```

#### 模式三：分类输出格式

```markdown
## Output Format

```markdown
# [Output Title]
## Section 1
## Section 2
```
```

### 8.4 含 Python 脚本的技能

部分技能（特别是 bio-research 插件）包含 Python 脚本用于数据处理：

| 技能 | 脚本 | 功能 |
|------|------|------|
| single-cell-rna-qc | `qc_core.py`, `qc_plotting.py`, `qc_analysis.py` | 单细胞 RNA 质量控制 |
| scvi-tools | `prepare_data.py`, `train_model.py`, `cluster_embed.py`, `differential_expression.py`, `transfer_labels.py`, `integrate_datasets.py`, `model_utils.py`, `validate_adata.py` | scVI 工具套件 |
| nextflow-development | `check_environment.py`, `detect_data_type.py`, `generate_samplesheet.py`, `manage_genomes.py`, `sra_geo_fetch.py` | Nextflow 管道开发 |
| instrument-data-to-allotrope | `convert_to_asm.py`, `export_parser.py`, `flatten_asm.py`, `validate_asm.py` | 仪器数据转换 |
| data-context-extractor | `package_data_skill.py` | 数据上下文打包 |

---

## 9. Command 命令系统

### 9.1 命令定义规范

命令是用户通过斜杠显式调用的操作，定义在 `commands/` 目录下。

#### 命令文件结构

```markdown
# /command-name

> Connector reference note

Brief description of what the command does.

## Usage

```
/command-name <arguments>
```

## How It Works

...

## Output

...
```

### 9.2 命令与技能的关系

| 特性 | 命令 (Commands) | 技能 (Skills) |
|------|----------------|---------------|
| 触发方式 | 用户显式斜杠调用 | AI 自动判断触发 |
| 定义位置 | `commands/*.md` | `skills/*/SKILL.md` |
| 适用场景 | 具体操作（如生成报告） | 领域知识和工作流 |
| 示例 | `/sales:call-summary` | `call-prep` 自动触发 |

### 9.3 内置命令汇总

| 插件 | 命令 | 功能 |
|------|------|------|
| sales | `/call-summary` | 处理通话笔记 |
| sales | `/forecast` | 销售预测 |
| sales | `/pipeline-review` | 管道审查 |
| product-management | `/brainstorm` | 产品头脑风暴 |
| pdf-viewer | `/open` | 打开 PDF |
| pdf-viewer | `/annotate` | 注释 PDF |
| pdf-viewer | `/fill-form` | 填写表单 |
| pdf-viewer | `/sign` | 签署 PDF |
| slack | `/channel-digest` | 频道摘要 |
| slack | `/draft-announcement` | 草拟公告 |
| slack | `/find-discussions` | 查找讨论 |
| slack | `/standup` | 站会 |
| slack | `/summarize-channel` | 频道总结 |
| common-room | `/generate-account-plan` | 生成客户计划 |
| common-room | `/weekly-brief` | 周报 |
| brand-voice | `/discover-brand` | 发现品牌 |
| brand-voice | `/enforce-voice` | 强制执行声音 |
| brand-voice | `/generate-guidelines` | 生成指南 |

---

## 10. MCP 连接器体系

### 10.1 MCP 协议

所有插件通过 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 与外部工具连接。MCP 是一个开放协议，标准化了 AI 应用与外部数据源之间的通信。

### 10.2 连接器配置 (.mcp.json)

每个插件根目录下的 `.mcp.json` 文件定义了可用的 MCP 服务器连接：

```json
{
  "mcpServers": {
    "server-name": {
      "type": "http",              // 或 "sse"
      "url": "https://mcp.example.com/mcp",
      "oauth": {                   // 可选 OAuth 配置
        "clientId": "...",
        "callbackPort": 3118
      }
    }
  }
}
```

### 10.3 占位符系统

插件使用 `~~category` 占位符实现工具无关性，`CONNECTORS.md` 文件定义了占位符到具体工具的映射：

```
~~CRM          → Salesforce, HubSpot, Close, Pipedrive
~~chat         → Slack, Microsoft Teams
~~email        → Gmail, Microsoft 365
~~calendar     → Google Calendar, Microsoft 365
~~project tracker → Jira, Linear, Asana, Monday
```

### 10.4 跨插件 MCP 服务器矩阵

| MCP 服务器 | 使用该服务器的插件 |
|------------|-------------------|
| Slack | productivity, sales, marketing, customer-support, engineering, operations, enterprise-search, product-management, finance, human-resources, legal |
| Notion | productivity, sales, customer-support, marketing, engineering, enterprise-search, product-management |
| Atlassian (Jira/Confluence) | sales, data, engineering, customer-support, product-management, legal, operations |
| Microsoft 365 | productivity, sales, customer-support, finance, legal, enterprise-search |
| HubSpot | sales, customer-support, marketing |
| Snowflake | finance, data |
| BigQuery | finance, data |
| Databricks | finance, data |
| Linear | productivity, engineering, product-management |
| Asana | productivity, engineering, enterprise-search, product-management |
| Figma | marketing, product-management, design |
| Amplitude | data, marketing, product-management |
| PagerDuty | engineering |
| Datadog | engineering |
| GitHub | engineering |
| Apollo | sales |
| ZoomInfo | sales |
| Fireflies | sales, product-management |

---

## 11. CI/CD 工作流

### 11.1 工作流总览

```
┌──────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline                             │
│                                                               │
│  ┌─────────────────┐                                         │
│  │  On PR / Daily   │                                         │
│  │  scan-plugins    │──→ 安全策略审查（含缓存）                  │
│  └────────┬────────┘                                         │
│           │ failure (bump branch only)                        │
│           ▼                                                   │
│  ┌─────────────────┐                                         │
│  │  revert-failed-  │──→ 回滚失败 SHA，重新触发扫描             │
│  │  bumps           │                                         │
│  └─────────────────┘                                         │
│                                                               │
│  ┌─────────────────┐                                         │
│  │  Daily 07:23 UTC │                                         │
│  │  bump-plugin-    │──→ 更新外部插件 SHA，自动验证              │
│  │  shas            │                                         │
│  └────────┬────────┘                                         │
│           │ dispatch scan                                     │
│           ▼                                                   │
│  ┌─────────────────┐                                         │
│  │  scan-plugins    │──→ 策略审查变更的插件                     │
│  └─────────────────┘                                         │
│                                                               │
│  ┌─────────────────┐                                         │
│  │  Daily 06:00 UTC │                                         │
│  │  check-mcp-urls  │──→ 验证内置插件 MCP URL 可达性            │
│  └─────────────────┘                                         │
└──────────────────────────────────────────────────────────────┘
```

### 11.2 scan-plugins.yml — 安全策略扫描

**文件**: [.github/workflows/scan-plugins.yml](file:///workspace/.github/workflows/scan-plugins.yml)

**触发条件**: 每个 PR 和 `workflow_dispatch`

**核心流程**:

1. **变更检测**: 对比 PR 与 base 分支的 `marketplace.json` 差异
2. **缓存命中**: 已扫描过的 (plugin, SHA) 对直接使用缓存结果
3. **AI 扫描**: 对未缓存的条目使用 Claude API 进行安全审查
4. **结果合并**: 缓存结果 + 新扫描结果合并为最终判决
5. **门禁**: 任何策略失败都阻止 PR 合并

**关键参数**:

| 参数 | 说明 |
|------|------|
| `cache-dir` | `.scan-cache/`，缓存 TTL 30 天 |
| `timeout` | 360 分钟 |
| `concurrency` | 按 PR/reference 串行化 |

**安全措施**:
- 使用 Workload Identity Federation 认证（非长期 API Key）
- 扫描结果中的 `sk-ant-` 密钥模式自动脱敏
- 模型输出文本包裹在 code span 中防止注入

### 11.3 bump-plugin-shas.yml — SHA 自动更新

**文件**: [.github/workflows/bump-plugin-shas.yml](file:///workspace/.github/workflows/bump-plugin-shas.yml)

**触发条件**: 每日 07:23 UTC，手动触发

**核心流程**:

1. 对每个外部插件，检查上游 HEAD 是否已超过已 pin 的 SHA
2. 在新 SHA 处执行 `claude plugin validate` 验证
3. 创建/更新 `bump/plugin-shas` 分支上的 PR
4. 自动 dispatch 策略扫描

**关键参数**:

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max-bumps` | 130 | 每次运行最大更新数量 |
| `timeout` | 60 分钟 | 全流程超时 |

### 11.4 check-mcp-urls.yml — MCP URL 存活检查

**文件**: [.github/workflows/check-mcp-urls.yml](file:///workspace/.github/workflows/check-mcp-urls.yml)

**触发条件**: PR（相关文件变更）、每日 06:00 UTC

**核心流程**:

1. 扫描内置插件的 `.mcp.json` 和 `plugin.json` 中的 MCP URL
2. 对每个 URL 发起 HEAD 请求（失败则尝试 POST JSON-RPC）
3. 仅 404/410 和连接失败视为失败；401/403/405/5xx 视为通过
4. 相同 URL 去重，每个 URL 仅探测一次

**排除规则**:
- 外部插件（字符串 source 的 marketplace 条目除外）
- 模板占位符 URL（含 `${` 或 `{{`）

### 11.5 revert-failed-bumps.yml — 回滚失败更新

**文件**: [.github/workflows/revert-failed-bumps.yml](file:///workspace/.github/workflows/revert-failed-bumps.yml)

**触发条件**: scan-plugins workflow_run 在 `bump/plugin-shas` 分支上失败

**核心流程**:

1. 下载扫描工件（verdicts JSON）
2. 定位 bump PR
3. 检查回滚预算（每夜最多 3 次）
4. 将失败插件的 `source.sha` 回滚到 main 分支的值
5. 创建签名提交，重新 dispatch 扫描

**安全护栏**:
- 仅作用于 `bump/plugin-shas` 分支
- 仅回滚 `source.sha`，其他字段差异则拒绝
- 使用 `createCommitOnBranch`（GitHub 签名，CAS 比较）
- 回滚预算耗尽后暂停并通知

---

## 12. 安全审查策略

### 12.1 策略文件

| 文件 | 用途 |
|------|------|
| [.github/policy/prompt.md](file:///workspace/.github/policy/prompt.md) | 安全审查提示词，指导 Claude 审查插件 |
| [.github/policy/schema.json](file:///workspace/.github/policy/schema.json) | 审查结果 JSON Schema |

### 12.2 审查维度

#### Part 1 — 基线安全
- 恶意代码或恶意软件
- 侵犯用户隐私的代码
- 欺骗性或误导性功能
- 规避安全措施的行为
- 未授权的数据收集或外泄
- 注入到技能/代理文本中的 prompt-injection 载荷

#### Part 2 — Hook 范围与披露
- 列举所有注册的 Hook
- 检查每个 Hook 的运行范围（项目相关 vs 无条件）
- 检查出站网络调用
- 检查是否读取用户数据超出声明范围

#### Part 3 — 网络与软件标志
- `may_make_external_network_calls`: 是否发起外部网络调用
- `may_download_additional_software`: 是否安装额外软件包

### 12.3 审查失败条件

满足以下任一条件则 `passes=false`:
- Part 1 发现恶意/欺骗/外泄/规避行为
- `has_broad_scope_hooks` 为 true
- `has_undisclosed_telemetry` 为 true
- `description_matches_behavior` 为 false（涉及 Hook/遥测/数据访问时）

### 12.4 审查结果 Schema

```json
{
  "passes": "boolean",
  "summary": "string",
  "violations": "string",
  "may_make_external_network_calls": "boolean",
  "may_download_additional_software": "boolean",
  "hooks": ["string array"],
  "has_broad_scope_hooks": "boolean",
  "has_undisclosed_telemetry": "boolean",
  "description_matches_behavior": "boolean"
}
```

---

## 13. 依赖关系

### 13.1 外部依赖

| 依赖 | 类型 | 用途 |
|------|------|------|
| Claude API | 运行时 | 策略审查扫描（scan-plugins workflow） |
| GitHub Actions | CI/CD | 所有自动化工作流 |
| anthropics/claude-plugins-community | GitHub Action | 共享的 scan-plugins 和 bump-plugin-shas actions |
| MCP Servers | 运行时 | 插件的外部工具连接 |

### 13.2 插件间关系

插件之间是**独立平行**的，不存在代码级依赖。一个插件的技能可以引用另一个插件的技能：

```
sales/call-prep → sales/account-research (同插件内引用)
sales/call-prep → sales/call-follow-up (同插件内引用)
```

插件间通过 `plugin-name:skill-name` 格式交叉引用。

### 13.3 市场依赖图

```
marketplace.json
├── 内置插件（17 个）
│   └── 各自独立，通过 marketplace.json 注册
├── 合作伙伴插件（5 个）
│   └── 各自独立，通过 marketplace.json 注册
└── 外部插件（~25 个）
    └── 通过 URL + SHA 引用，独立维护
```

---

## 14. 项目运行方式

### 14.1 安装

#### Claude Cowork

从 [claude.com/plugins](https://claude.com/plugins/) 安装插件。

#### Claude Code

```bash
# 添加市场
claude plugin marketplace add anthropics/knowledge-work-plugins

# 安装特定插件
claude plugin install sales@knowledge-work-plugins
```

### 14.2 使用方法

安装后插件自动激活：
- **技能**: 当对话上下文匹配时自动触发
- **命令**: 通过斜杠命令显式调用，如 `/sales:call-prep`、`/data:write-query`

### 14.3 定制化

用户可通过以下方式定制插件：

1. **替换连接器**: 编辑 `.mcp.json` 指向自己的工具栈
2. **添加公司上下文**: 在技能文件中添加组织术语、结构和流程
3. **调整工作流**: 修改技能指令以匹配团队实际工作方式
4. **构建设置文件**: 创建 `settings.local.json` 个性化配置

### 14.4 贡献流程

1. Fork 仓库
2. 创建/修改插件文件（Markdown + JSON）
3. 提交 PR
4. CI 自动运行安全审查和 MCP URL 检查
5. 审查通过后合并

### 14.5 本地开发

```bash
# 克隆仓库
git clone https://github.com/anthropics/knowledge-work-plugins.git

# 插件是纯文本文件，无需构建步骤
# 直接用编辑器修改 Markdown/JSON 文件即可

# 验证插件结构
claude plugin validate ./path/to/plugin
```

---

## 15. 关键文件索引

### 15.1 项目根级

| 文件 | 路径 | 说明 |
|------|------|------|
| README | [README.md](file:///workspace/README.md) | 项目总览和快速开始 |
| LICENSE | [LICENSE](file:///workspace/LICENSE) | Apache 2.0 |
| 市场注册表 | [.claude-plugin/marketplace.json](file:///workspace/.claude-plugin/marketplace.json) | 所有插件索引 |

### 15.2 CI/CD 配置

| 文件 | 路径 | 说明 |
|------|------|------|
| 策略审查 | [.github/workflows/scan-plugins.yml](file:///workspace/.github/workflows/scan-plugins.yml) | 安全策略自动扫描 |
| SHA 更新 | [.github/workflows/bump-plugin-shas.yml](file:///workspace/.github/workflows/bump-plugin-shas.yml) | 外部插件版本更新 |
| URL 检查 | [.github/workflows/check-mcp-urls.yml](file:///workspace/.github/workflows/check-mcp-urls.yml) | MCP 服务可用性检查 |
| 失败回滚 | [.github/workflows/revert-failed-bumps.yml](file:///workspace/.github/workflows/revert-failed-bumps.yml) | 策略失败回滚 |
| 审查提示词 | [.github/policy/prompt.md](file:///workspace/.github/policy/prompt.md) | 安全审查 Prompt |
| 审查 Schema | [.github/policy/schema.json](file:///workspace/.github/policy/schema.json) | 审查结果 Schema |

### 15.3 内置插件清单

| 插件 | plugin.json | 技能数 | 命令数 |
|------|------------|--------|--------|
| productivity | [plugin.json](file:///workspace/productivity/.claude-plugin/plugin.json) | 4 | 0 |
| sales | [plugin.json](file:///workspace/sales/.claude-plugin/plugin.json) | 6 | 3 |
| customer-support | [plugin.json](file:///workspace/customer-support/.claude-plugin/plugin.json) | 5 | 0 |
| product-management | [plugin.json](file:///workspace/product-management/.claude-plugin/plugin.json) | 8 | 1 |
| marketing | [plugin.json](file:///workspace/marketing/.claude-plugin/plugin.json) | 8 | 0 |
| legal | [plugin.json](file:///workspace/legal/.claude-plugin/plugin.json) | 9 | 0 |
| finance | [plugin.json](file:///workspace/finance/.claude-plugin/plugin.json) | 8 | 0 |
| data | [plugin.json](file:///workspace/data/.claude-plugin/plugin.json) | 10 | 0 |
| enterprise-search | [plugin.json](file:///workspace/enterprise-search/.claude-plugin/plugin.json) | 5 | 0 |
| engineering | [plugin.json](file:///workspace/engineering/.claude-plugin/plugin.json) | 10 | 0 |
| human-resources | [plugin.json](file:///workspace/human-resources/.claude-plugin/plugin.json) | 9 | 0 |
| design | [plugin.json](file:///workspace/design/.claude-plugin/plugin.json) | 7 | 0 |
| operations | [plugin.json](file:///workspace/operations/.claude-plugin/plugin.json) | 9 | 0 |
| bio-research | [plugin.json](file:///workspace/bio-research/.claude-plugin/plugin.json) | 5 | 0 |
| cowork-plugin-management | [plugin.json](file:///workspace/cowork-plugin-management/.claude-plugin/plugin.json) | 2 | 0 |
| small-business | [plugin.json](file:///workspace/small-business/.claude-plugin/plugin.json) | 30+ | 0 |
| pdf-viewer | [plugin.json](file:///workspace/pdf-viewer/.claude-plugin/plugin.json) | 1 | 4 |

### 15.4 合作伙伴插件清单

| 插件 | plugin.json | 提供方 |
|------|------------|--------|
| apollo | [plugin.json](file:///workspace/partner-built/apollo/.claude-plugin/plugin.json) | Apollo.io |
| brand-voice | [plugin.json](file:///workspace/partner-built/brand-voice/.claude-plugin/plugin.json) | Tribe AI |
| common-room | [plugin.json](file:///workspace/partner-built/common-room/.claude-plugin/plugin.json) | Common Room |
| slack | [plugin.json](file:///workspace/partner-built/slack/.claude-plugin/plugin.json) | Salesforce |
| zoom-plugin | [plugin.json](file:///workspace/partner-built/zoom-plugin/.claude-plugin/plugin.json) | Zoom |

---

> **文档结束** | 本 Code Wiki 基于仓库代码自动生成，反映了项目在 2026-06-15 时的状态。