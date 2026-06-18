# Knowledge Work Plugins → 多平台迁移指南

> 将 Anthropic Knowledge Work Plugins 中的 17 个内置插件迁移到 Codex、Hermes、Trae Work、Qoder 四个平台。

---

## 目录

1. [迁移总览](#1-迁移总览)
2. [平台兼容性矩阵](#2-平台兼容性矩阵)
3. [第一步：Qoder 迁移（最优先）](#3-第一步qoder-迁移最优先)
4. [第二步：Codex 迁移](#4-第二步codex-迁移)
5. [第三步：Trae Work 迁移](#5-第三步trae-work-迁移)
6. [第四步：Hermes 迁移](#6-第四步hermes-迁移)
7. [自动化迁移脚本](#7-自动化迁移脚本)
8. [迁移后验证清单](#8-迁移后验证清单)
9. [注意事项与限制](#9-注意事项与限制)

---

## 1. 迁移总览

### 1.1 核心资产与可迁移性

| 资产 | 格式 | Codex | Trae | Hermes | Qoder | 迁移难度 |
|------|------|-------|------|--------|-------|---------|
| **SKILL.md** (技能定义) | Markdown + YAML Frontmatter | ✅ 直接复用 | ✅ 转为 Rules | ✅ 直接复用 | ✅ 直接复用 | 低 |
| **plugin.json** (插件清单) | JSON | ✅ 直接复用 | ❌ 无需 | ✅ 转为 YAML | ✅ 直接复用（仅目录名不同） | 低 |
| **.mcp.json** (MCP 配置) | JSON | ✅ 直接复用 | ⚠️ 需微调 | ✅ 直接复用 | ✅ 直接复用 | 低 |
| **commands/*.md** (斜杠命令) | Markdown | ✅ 直接复用 | ❌ 不支持 | ⚠️ 需 Python 包装 | ✅ 直接复用 | 低 |
| **scripts/*.py** (Python 脚本) | Python | ✅ 直接复用 | ❌ 不支持 | ✅ 直接复用 | ✅ 直接复用 | 低 |
| **agents/*.md** (子代理) | Markdown | ⚠️ 待支持 | ❌ 不支持 | ❌ 不支持 | ✅ 直接复用 | 低 |
| **references/*.md** (参考文档) | Markdown | ✅ 直接复用 | ✅ 直接复用 | ✅ 直接复用 | ✅ 直接复用 | 低 |

### 1.2 迁移决策树

```
你要迁移的是？
├── 技能的知识内容（SKILL.md 的正文）
│   ├── → Qoder: 几乎零改动，直接放 skills/ 目录
│   ├── → Codex: 几乎零改动，直接放 skills/ 目录
│   ├── → Trae: 转为 .trae/rules/{name}.md，设智能生效模式
│   └── → Hermes: 直接放 skills/ 目录，通过 register_skill() 注册
│
├── MCP 工具连接配置（.mcp.json）
│   ├── → Qoder: 直接复制，格式完全兼容
│   ├── → Codex: 直接复制，格式完全兼容
│   ├── → Trae: 转为 .trae/mcp.json，URL 类型相同
│   └── → Hermes: 直接复制，格式兼容
│
├── 斜杠命令（commands/）
│   ├── → Qoder: 直接复制，格式兼容
│   ├── → Codex: 直接复制，格式兼容
│   ├── → Trae: 不支持斜杠命令，转为 Rules 中的触发词
│   └── → Hermes: 通过 ctx.register_command() 注册
│
└── Python 脚本（scripts/）
    ├── → Codex: 直接复制
    ├── → Trae: 不支持，可忽略
    └── → Hermes: 直接复制到工具模块
```

---

## 2. 平台兼容性矩阵

### 2.1 四平台架构对比

| 特性 | Claude Code | Qoder | Codex | Trae Work | Hermes |
|------|-------------|-------|-------|-----------|--------|
| **插件清单** | `.claude-plugin/plugin.json` | `.qoder-plugin/plugin.json` | `.codex-plugin/plugin.json` | 无 | `plugin.yaml` |
| **技能/规则** | `skills/*/SKILL.md` | `skills/*/SKILL.md` | `skills/*/SKILL.md` | `.trae/rules/*.md` | `skills/*/SKILL.md` |
| **MCP 配置** | `.mcp.json` | `.mcp.json` | `.mcp.json` | `.trae/mcp.json` | `mcp.json` |
| **斜杠命令** | `commands/*.md` | `commands/*.md` | `commands/*.md` | 不支持 | `ctx.register_command()` |
| **子代理** | `agents/*.md` | `agents/*.md` | 开发中 | 不支持 | 不支持 |
| **触发机制** | 自动 + 手动 | 自动 + 手动 | `$skill-name` 语法 | 智能生效/手动 `#Rule` | `skill_view()` |
| **插件安装** | `claude plugin install` | `qoder plugin install` | 目录安装 / 市场 | 手动复制到项目 | `~/.hermes/plugins/` |
| **兼容度** | — | ✨ 99% | 98% | 70% | 60% |

### 2.2 迁移优先级建议

| 优先级 | 平台 | 理由 |
|--------|------|------|
| P0（最优先） | **Qoder** | 架构与 Claude Code 几乎完全一致，仅需将 `.claude-plugin` 改名为 `.qoder-plugin` |
| P1 | **Codex** | 架构高度相似，几乎 1:1 映射，仅需极小调整 |
| P2 | **Trae Work** | 格式简单，需将 SKILL.md 转为 Rules 格式 |
| P3 | **Hermes** | 需要额外编写 Python 包装代码，但技能内容可直接复用 |

---

## 3. 第一步：Qoder 迁移（最优先）

### 3.1 为什么 Qoder 最容易

Qoder 的插件系统与 Claude Code **几乎完全一致**。根据 Qoder 官方文档，插件结构如下：

| 组件 | Claude Code | Qoder |
|------|-------------|-------|
| 插件清单 | `.claude-plugin/plugin.json` | `.qoder-plugin/plugin.json` |
| 技能 | `skills/*/SKILL.md` | `skills/*/SKILL.md` |
| 命令 | `commands/*.md` | `commands/*.md` |
| 子代理 | `agents/*.md` | `agents/*.md` |
| MCP 配置 | `.mcp.json` | `.mcp.json` |

**唯一的差异：** 清单目录名从 `.claude-plugin` 改为 `.qoder-plugin`。

### 3.2 架构对应关系

```
Claude Code 插件                    Qoder 插件
─────────────────────────────────────────────────────
.claude-plugin/plugin.json    ←→   .qoder-plugin/plugin.json
skills/call-prep/SKILL.md     ←→   skills/call-prep/SKILL.md
skills/call-prep/scripts/     ←→   skills/call-prep/scripts/
skills/call-prep/references/  ←→   skills/call-prep/references/
commands/call-summary.md      ←→   commands/call-summary.md
agents/agent-name.md          ←→   agents/agent-name.md
.mcp.json                     ←→   .mcp.json
CONNECTORS.md                 ←→   CONNECTORS.md
```

### 3.3 手动迁移步骤

```bash
# 1. 创建 Qoder 插件目录
mkdir -p ~/.qoder/plugins/sales

# 2. 复制并重命名清单目录（唯一需要改的地方）
cp -r sales/.claude-plugin sales/.qoder-plugin
cp -r sales/.qoder-plugin ~/.qoder/plugins/sales/.qoder-plugin

# 3. 技能、命令、代理、MCP 配置全部直接复制（无需修改）
cp -r sales/skills ~/.qoder/plugins/sales/
cp -r sales/commands ~/.qoder/plugins/sales/
cp -r sales/agents ~/.qoder/plugins/sales/   # 如有
cp sales/.mcp.json ~/.qoder/plugins/sales/

# 4. 复制其他文件
cp sales/CONNECTORS.md sales/README.md ~/.qoder/plugins/sales/
```

### 3.4 插件安装

```bash
# 安装插件
qoder plugin install ~/.qoder/plugins/sales

# 或从 Git 仓库安装
qoder plugin install your-org/qoder-knowledge-plugins

# 使用技能（自动触发，支持插件限定名）
# sales:call-prep 或直接 call-prep
```

### 3.5 唯一需要手动调整的地方

占位符 `~~category` 需要替换为实际的 MCP 服务器名称（迁移脚本已自动处理为通用描述）：

```markdown
# 原始
Check your ~~CRM for account history

# 迁移后
Check your CRM system for account history
# 或手动改为具体工具
Check your HubSpot for account history
```

---

## 4. 第二步：Codex 迁移

### 4.1 架构对应关系

```
Claude Code 插件                    Codex 插件
─────────────────────────────────────────────────────
.claude-plugin/plugin.json    ←→   .codex-plugin/plugin.json
skills/call-prep/SKILL.md     ←→   skills/call-prep/SKILL.md
skills/call-prep/scripts/     ←→   skills/call-prep/scripts/
skills/call-prep/references/  ←→   skills/call-prep/references/
commands/call-summary.md      ←→   commands/call-summary.md
.mcp.json                     ←→   .mcp.json
CONNECTORS.md                 ←→   CONNECTORS.md
```

### 4.2 手动迁移步骤

```bash
# 1. 创建 Codex 插件目录
mkdir -p ~/.codex/plugins/sales

# 2. 复制并调整插件清单
cp sales/.claude-plugin/plugin.json ~/.codex/plugins/sales/.codex-plugin/plugin.json

# 3. 复制技能文件（无需修改）
cp -r sales/skills ~/.codex/plugins/sales/

# 4. 复制命令文件
cp -r sales/commands ~/.codex/plugins/sales/

# 5. 复制 MCP 配置
cp sales/.mcp.json ~/.codex/plugins/sales/

# 6. 复制其他文件
cp sales/CONNECTORS.md sales/README.md ~/.codex/plugins/sales/
```

### 4.3 需要手动调整的地方

1. **SKILL.md 中的占位符**: 将 `~~CRM`、`~~chat` 等替换为实际的 MCP 服务器名称
2. **触发词**: Codex 使用 `$skill-name` 语法，在 description 中添加 `Trigger with "$call-prep"`
3. **子代理**: 如果原插件有 `agents/`，暂时保留等待 Codex 支持

### 4.4 插件安装

```bash
# 方式一：本地目录安装
codex plugin install ~/.codex/plugins/sales

# 方式二：从 Git 仓库安装
codex plugin install your-org/codex-knowledge-plugins

# 使用技能
$call-prep Acme Corp
```

---

## 5. 第三步：Trae Work 迁移

### 5.1 架构对应关系

```
Claude Code 插件                    Trae Work 配置
─────────────────────────────────────────────────────
skills/call-prep/SKILL.md     ←→   .trae/rules/sales-call-prep.md
.mcp.json                     ←→   .trae/mcp.json
plugin.json                   ←→   （无对应，metadata 写入 rule 描述）
commands/*.md                 ←→   （转为 Rules 中的触发词说明）
```

### 5.2 手动迁移步骤

```bash
# 1. 在项目中创建 Trae 配置目录
mkdir -p your-project/.trae/rules

# 2. 转换技能文件为 Rules 格式
#    每个 SKILL.md 转换为一个 .trae/rules/{plugin}-{skill}.md 文件
#    关键：在 frontmatter 中设置 description 字段用于智能生效

# 3. 转换 MCP 配置
#    将 .mcp.json 复制为 .trae/mcp.json，格式微调
```

### 5.3 SKILL.md → Trae Rule 转换规则

**原始 SKILL.md frontmatter**:
```yaml
---
name: call-prep
description: Prepare for a sales call...
argument-hint: "<company>"
---
```

**转换后的 Trae Rule frontmatter**:
```yaml
---
description: "[sales] Prepare for a sales call with account context..."
alwaysApply: false
enabled: true
---
```

**关键转换规则**:
- `name` → 不保留（Trae 用文件名识别）
- `description` → 保留，前面加 `[plugin-name]` 前缀，用于智能生效匹配
- `alwaysApply: false` → 智能生效模式（推荐）
- 正文内容 → 保留，但开头的 `# Skill Name` 标题替换为 `# Trae Rule: {plugin}/{skill}`

### 5.4 .mcp.json → Trae MCP 配置转换

**原始格式**:
```json
{
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "https://mcp.slack.com/mcp",
      "oauth": { "clientId": "...", "callbackPort": 3118 }
    }
  }
}
```

**Trae 格式**:
```json
{
  "mcpServers": [
    {
      "name": "slack",
      "url": "https://mcp.slack.com/mcp",
      "type": "http"
    }
  ]
}
```

### 5.5 部署到 Trae IDE

```bash
# 1. 将 Rules 文件复制到项目
cp -r .trae/rules/* your-project/.trae/rules/

# 2. 将 MCP 配置复制到项目
cp .trae/mcp.json your-project/.trae/

# 3. 在 Trae IDE 中打开项目
#    Rules 会自动加载，description 字段用于智能匹配
#    也可通过 #Rule 手动触发
```

---

## 6. 第四步：Hermes 迁移

### 6.1 架构对应关系

```
Claude Code 插件                    Hermes 插件
─────────────────────────────────────────────────────
.claude-plugin/plugin.json    ←→   plugin.yaml
skills/call-prep/SKILL.md     ←→   skills/call-prep/SKILL.md
skills/call-prep/scripts/     ←→   skills/call-prep/scripts/
.mcp.json                     ←→   mcp.json
（无对应）                      ←→   __init__.py（注册入口）
（无对应）                      ←→   schemas.py（工具模式）
（无对应）                      ←→   tools.py（工具处理）
```

### 5.2 手动迁移步骤

```bash
# 1. 创建 Hermes 插件目录
mkdir -p ~/.hermes/plugins/sales

# 2. 创建 plugin.yaml 清单
cat > ~/.hermes/plugins/sales/plugin.yaml << 'EOF'
name: sales
version: "1.2.0"
description: Prospect, craft outreach, and build deal strategy faster.
kind: general
EOF

# 3. 复制技能文件
cp -r skills ~/.hermes/plugins/sales/

# 4. 复制 MCP 配置
cp .mcp.json ~/.hermes/plugins/sales/mcp.json

# 5. 创建 Python 注册入口
```

### 6.3 创建 Python 注册入口

**`__init__.py`** — 核心注册文件:

```python
"""Auto-generated Hermes plugin: sales

Migrated from Anthropic Knowledge Work Plugins.
"""

from pathlib import Path

def register(ctx):
    """Register skills from the sales plugin."""
    base = Path(__file__).parent

    ctx.register_skill("call-prep", "skills/call-prep/SKILL.md")
    ctx.register_skill("account-research", "skills/account-research/SKILL.md")
    ctx.register_skill("daily-briefing", "skills/daily-briefing/SKILL.md")
    ctx.register_skill("draft-outreach", "skills/draft-outreach/SKILL.md")
    ctx.register_skill("competitive-intelligence", "skills/competitive-intelligence/SKILL.md")
    ctx.register_skill("create-an-asset", "skills/create-an-asset/SKILL.md")
```

**`schemas.py`** — 工具模式定义（按需扩展）:

```python
"""Tool schemas for the sales plugin."""

# 如需添加自定义工具，在此定义 schema
```

**`tools.py`** — 工具处理函数（按需扩展）:

```python
"""Tool handlers for the sales plugin."""

# 如需添加自定义工具，在此实现处理函数
```

### 6.4 启用插件

```bash
# 启用插件
hermes plugins enable sales

# 或通过交互式面板
hermes plugins

# 验证技能已加载
# 在 Hermes 对话中，技能会自动通过 skill_view("sales:call-prep") 加载
```

---

## 7. 自动化迁移脚本

项目根目录提供了 `migrate_skills.py` 脚本，可一键完成所有迁移。

### 7.1 安装依赖

```bash
pip install pyyaml
```

### 7.2 基本用法

```bash
# 迁移单个插件到 Codex
python migrate_skills.py --target codex --input ./sales --output ./migrated/sales

# 迁移单个插件到 Trae
python migrate_skills.py --target trae --input ./sales --output ./migrated/sales

# 迁移单个插件到 Hermes
python migrate_skills.py --target hermes --input ./sales --output ./migrated/sales

# 同时迁移到三个平台
python migrate_skills.py --target all --input ./sales --output ./migrated/sales

# 迁移所有 17 个内置插件
python migrate_skills.py --target all --all-plugins --output ./migrated

# 迁移单个 SKILL.md 文件
python migrate_skills.py --target trae \
  --skill ./skills/call-prep/SKILL.md \
  --plugin-name sales \
  --output ./rules/call-prep.md
```

### 7.3 脚本输出结构

迁移后，输出目录结构如下：

```
migrated/
├── codex/
│   └── sales/
│       ├── .codex-plugin/plugin.json
│       ├── .mcp.json
│       ├── skills/
│       │   ├── call-prep/SKILL.md
│       │   └── ...
│       ├── commands/
│       └── README.md
│
├── trae/
│   └── sales/
│       ├── .trae/
│       │   ├── mcp.json
│       │   └── rules/
│       │       ├── sales-call-prep.md
│       │       └── ...
│       └── README.md
│
└── hermes/
    └── sales/
        ├── plugin.yaml
        ├── mcp.json
        ├── __init__.py
        ├── schemas.py
        ├── tools.py
        ├── skills/
        │   ├── call-prep/SKILL.md
        │   └── ...
        └── README.md
```

---

## 8. 迁移后验证清单

### 8.1 Qoder 验证

- [ ] `.qoder-plugin/plugin.json` 格式正确，能被 Qoder 识别
- [ ] 技能文件在对话中能自动触发
- [ ] MCP 服务器连接正常
- [ ] 斜杠命令 `/command` 可正常调用
- [ ] 子代理 `agents/` 可正常加载
- [ ] 占位符 `~~category` 已替换为实际工具名

### 8.2 Codex 验证

- [ ] `plugin.json` 格式正确，能被 Codex 识别
- [ ] 技能文件在 `$skill-name` 调用时能正确加载
- [ ] MCP 服务器连接正常
- [ ] 斜杠命令 `/command` 可正常调用
- [ ] 占位符 `~~category` 已替换为实际工具名

### 8.3 Trae Work 验证

- [ ] `.trae/rules/*.md` 文件格式正确
- [ ] `description` 字段能触发智能生效
- [ ] `.trae/mcp.json` MCP 配置正确
- [ ] 在 Trae IDE 中打开项目后 Rules 被加载
- [ ] 通过 `#Rule` 手动触发时内容正确

### 8.4 Hermes 验证

- [ ] `plugin.yaml` 格式正确
- [ ] `hermes plugins list` 能看到插件
- [ ] `hermes plugins enable sales` 生效
- [ ] 技能通过 `skill_view("sales:call-prep")` 可加载
- [ ] Python 脚本（如有）能正常执行

---

## 9. 注意事项与限制

### 9.1 通用限制

| 限制 | 说明 | 解决方案 |
|------|------|---------|
| 占位符 `~~category` | 四个平台都不支持这种 Claude 特有的占位符 | 脚本已自动替换为通用描述；实际使用时需手动改为具体工具名 |
| 子代理 `agents/` | 只有 Claude Code 支持子代理，Codex 开发中 | 暂不迁移，保留原文件等待支持 |
| 插件间交叉引用 | 原插件中 `sales/call-prep → sales/account-research` 的引用关系 | 迁移后需手动检查路径引用 |

### 9.2 Qoder 特定限制

- Qoder 暂不支持通过 `qoder plugin marketplace` 添加外部市场 URL
- 插件需手动复制到 `~/.qoder/plugins/` 目录，或通过 `qoder plugin install` 安装
- 子代理功能与 Claude Code 兼容，但部分高级特性可能不同

### 9.3 Codex 特定限制

- Codex 技能使用 `$skill-name` 语法触发，与 Claude 的自动触发不同
- 建议在 `description` 字段中明确写出触发词
- 子代理功能仍在开发中，`agents/` 目录暂不可用

### 9.4 Trae Work 特定限制

- Trae 不支持插件清单概念，`plugin.json` 元数据写入 `description` 字段
- 不支持斜杠命令，命令内容转为 Rule 中的触发词说明
- 不支持 Python 脚本执行
- MCP 配置格式为数组而非对象，需转换

### 9.5 Hermes 特定限制

- 需要编写 Python 插件包装代码（`__init__.py` 等）
- 技能通过 `skill_view()` 加载，触发方式与 Claude 不同
- 不支持子代理概念
- 插件需手动启用（`hermes plugins enable`）

---

## 附录：快速命令参考

```bash
# ─── 全量迁移 ───
python migrate_skills.py --target all --all-plugins --output ./migrated

# ─── 单插件迁移 ───
python migrate_skills.py --target qoder  --input ./sales --output ./migrated/sales
python migrate_skills.py --target codex  --input ./sales --output ./migrated/sales
python migrate_skills.py --target trae   --input ./sales --output ./migrated/sales
python migrate_skills.py --target hermes --input ./sales --output ./migrated/sales

# ─── 单文件迁移 ───
python migrate_skills.py --target trae --skill ./skills/call-prep/SKILL.md \
  --plugin-name sales --output ./rules/call-prep.md

# ─── 部署到各平台 ───
# Qoder
cp -r migrated/qoder/sales ~/.qoder/plugins/

# Codex
cp -r migrated/codex/sales ~/.codex/plugins/

# Trae
cp -r migrated/trae/sales/.trae ~/your-project/

# Hermes
cp -r migrated/hermes/sales ~/.hermes/plugins/
hermes plugins enable sales
```