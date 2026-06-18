#!/usr/bin/env python3
"""
Knowledge Work Plugins → 多平台迁移转换器

将 Claude Code 的 SKILL.md 文件转换为 Codex、Trae、Hermes 三种目标格式。

用法:
    python migrate_skills.py --target codex   --input ./sales --output ./codex-plugins/sales
    python migrate_skills.py --target trae    --input ./sales --output ./trae-rules/sales
    python migrate_skills.py --target hermes  --input ./sales --output ./hermes-plugins/sales
    python migrate_skills.py --target all     --input ./sales --output ./migrated/sales
"""

import argparse
import json
import os
import re
import sys
import yaml  # type: ignore
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────────────────────
# YAML Frontmatter 解析
# ──────────────────────────────────────────────────────────────

def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """解析 SKILL.md 的 YAML frontmatter，返回 (metadata, body)"""
    content = content.strip()
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    body = parts[2].strip()
    return meta, body


# ──────────────────────────────────────────────────────────────
# 格式转换器
# ──────────────────────────────────────────────────────────────

def convert_to_codex(meta: dict, body: str, plugin_name: str) -> str:
    """转换为 Codex 技能格式。

    Codex 技能格式与 Claude 最接近，Markdown + YAML frontmatter 几乎可以直接复用。
    主要差异：Codex 使用 `$skill-name` 调用语法，description 字段是触发条件。
    """
    name = meta.get("name", "unknown")
    desc = meta.get("description", f"Skill from {plugin_name} plugin")

    # Codex 的 frontmatter 结构
    codex_meta = {
        "name": name,
        "description": desc,
    }
    if meta.get("argument-hint"):
        codex_meta["argument-hint"] = meta["argument-hint"]

    # 处理 body 中的占位符：替换 ~~category 为通用描述
    body = _replace_placeholders(body)

    return _format_skill_md(codex_meta, body)


def convert_to_trae(meta: dict, body: str, plugin_name: str) -> str:
    """转换为 Trae Rules 格式。

    Trae 使用 .trae/rules/*.md 文件，支持 alwaysApply / description / globs 属性。
    技能内容转换为项目规则。"""
    name = meta.get("name", "unknown")
    desc = meta.get("description", "")

    # Trae 的 rules frontmatter
    trae_meta = {
        "description": f"[{plugin_name}] {desc[:200]}",
        "alwaysApply": False,
        "enabled": True,
    }

    # 内容重写：强调这是 AI 应当遵循的规则和工作流
    body = _replace_placeholders(body)
    body = _add_rule_header(body, plugin_name, name)

    return _format_skill_md(trae_meta, body)


def convert_to_hermes(meta: dict, body: str, plugin_name: str) -> str:
    """转换为 Hermes 技能格式。

    Hermes 支持通过 ctx.register_skill(name, path) 注册技能。
    技能文件是纯 Markdown，通过 skill_view() 加载。"""
    name = meta.get("name", "unknown")
    desc = meta.get("description", "")

    # Hermes 技能格式：纯 Markdown，无 frontmatter
    # 但需要有明确的标题和描述
    body = _replace_placeholders(body)
    return body


def _replace_placeholders(text: str) -> str:
    """将 ~~category 占位符替换为通用描述"""
    placeholder_map = {
        "~~CRM": "your CRM system",
        "~~chat": "your chat platform",
        "~~email": "your email",
        "~~calendar": "your calendar",
        "~~project tracker": "your project tracker",
        "~~knowledge base": "your knowledge base",
        "~~source control": "your source control",
        "~~data warehouse": "your data warehouse",
        "~~competitive intelligence": "competitive intelligence tools",
        "~~data enrichment": "data enrichment tools",
        "~~conversation intelligence": "conversation intelligence tools",
        "~~sales engagement": "your sales engagement platform",
        "~~design": "your design tools",
    }
    for pattern, replacement in placeholder_map.items():
        text = text.replace(pattern, replacement)
    return text


def _add_rule_header(body: str, plugin_name: str, skill_name: str) -> str:
    """为 Trae rules 添加规则头部说明"""
    header = (
        f"# Trae Rule: {plugin_name}/{skill_name}\n\n"
        f"> 此规则由 Claude Code 插件 '{plugin_name}' 的技能 '{skill_name}' 迁移而来。\n"
        f"> 规则类型：智能生效（根据对话上下文自动判断是否应用）\n\n"
        "---\n\n"
    )
    return header + body


def _format_skill_md(meta: dict, body: str) -> str:
    """将元数据和 body 格式化为完整的 Markdown 文件"""
    yaml_str = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{yaml_str}\n---\n\n{body}\n"


# ──────────────────────────────────────────────────────────────
# MCP 配置转换
# ──────────────────────────────────────────────────────────────

def convert_mcp_config(source_path: Path, target: str) -> dict | None:
    """转换 .mcp.json 配置为目标平台格式"""
    mcp_file = source_path / ".mcp.json"
    if not mcp_file.exists():
        return None

    with open(mcp_file) as f:
        config = json.load(f)

    if target == "codex":
        # Codex 使用相同的 MCP 格式
        return config
    elif target == "trae":
        # Trae 使用 mcpServers 数组格式
        servers = config.get("mcpServers", {})
        trae_servers = []
        for name, cfg in servers.items():
            if isinstance(cfg, dict):
                entry = {"name": name}
                if "url" in cfg and cfg["url"]:
                    entry["url"] = cfg["url"]
                    entry["type"] = cfg.get("type", "http")
                trae_servers.append(entry)
        return {"mcpServers": trae_servers}
    elif target == "hermes":
        # Hermes 使用自己的 MCP 配置格式
        return config
    return config


# ──────────────────────────────────────────────────────────────
# 插件清单转换
# ──────────────────────────────────────────────────────────────

def convert_plugin_manifest(source_path: Path, target: str) -> dict | None:
    """转换 plugin.json 为目标平台清单"""
    manifest_file = source_path / ".claude-plugin" / "plugin.json"
    if not manifest_file.exists():
        return None

    with open(manifest_file) as f:
        manifest = json.load(f)

    if target == "codex":
        return {
            "name": manifest.get("name", ""),
            "version": manifest.get("version", "1.0.0"),
            "description": manifest.get("description", ""),
            "author": manifest.get("author", {}),
        }
    elif target == "hermes":
        return {
            "name": manifest.get("name", ""),
            "version": manifest.get("version", "1.0.0"),
            "description": manifest.get("description", ""),
            "kind": "general",
        }
    elif target == "trae":
        # Trae 没有插件清单，返回 None
        return None
    return manifest


# ──────────────────────────────────────────────────────────────
# Hermes Python 插件骨架生成
# ──────────────────────────────────────────────────────────────

def generate_hermes_plugin_init(plugin_name: str, skills: list[dict]) -> str:
    """生成 Hermes 插件的 __init__.py"""
    skill_registrations = []
    for s in skills:
        skill_registrations.append(
            f'    ctx.register_skill("{s["name"]}", "{s["rel_path"]}")\n'
        )

    return f'''"""Auto-generated Hermes plugin: {plugin_name}

Migrated from Anthropic Knowledge Work Plugins.
"""

from pathlib import Path


def register(ctx):
    """Register skills from the {plugin_name} plugin."""

    base = Path(__file__).parent

    # Register skills (loaded as "{plugin_name}:skill_name")
{chr(10).join(skill_registrations)}
'''


def generate_hermes_schemas_py() -> str:
    """生成 Hermes 插件的 schemas.py 骨架"""
    return '''"""Tool schemas for the plugin."""

# Add tool schemas here as Python dicts.
# Each schema describes what the LLM sees:
#
# SCHEMA_EXAMPLE = {
#     "name": "tool_name",
#     "description": "What this tool does",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "param": {"type": "string", "description": "..."}
#         },
#         "required": ["param"],
#     },
# }
'''


def generate_hermes_tools_py() -> str:
    """生成 Hermes 插件的 tools.py 骨架"""
    return '''"""Tool handlers for the plugin."""

# Add tool handler functions here.
# Each handler receives params and returns a result:
#
# def handle_example(params, **kwargs):
#     return json.dumps({"success": True, "result": "..."})
'''


# ──────────────────────────────────────────────────────────────
# 主迁移逻辑
# ──────────────────────────────────────────────────────────────

def migrate_plugin(source_dir: Path, output_dir: Path, target: str):
    """将单个插件迁移到目标平台"""
    plugin_name = source_dir.name
    print(f"  Migrating plugin: {plugin_name} → {target}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 转换插件清单
    manifest = convert_plugin_manifest(source_dir, target)
    if manifest:
        if target == "hermes":
            # Hermes 使用 plugin.yaml
            with open(output_dir / "plugin.yaml", "w") as f:
                yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True)
        elif target == "codex":
            os.makedirs(output_dir / ".codex-plugin", exist_ok=True)
            with open(output_dir / ".codex-plugin" / "plugin.json", "w") as f:
                json.dump(manifest, f, indent=2)

    # 2. 转换 MCP 配置
    mcp_config = convert_mcp_config(source_dir, target)
    if mcp_config:
        if target == "trae":
            trae_dir = output_dir / ".trae"
            trae_dir.mkdir(parents=True, exist_ok=True)
            with open(trae_dir / "mcp.json", "w") as f:
                json.dump(mcp_config, f, indent=2)
        elif target == "hermes":
            with open(output_dir / "mcp.json", "w") as f:
                json.dump(mcp_config, f, indent=2)
        else:
            with open(output_dir / ".mcp.json", "w") as f:
                json.dump(mcp_config, f, indent=2)

    # 3. 转换技能文件
    skills_dir = source_dir / "skills"
    if not skills_dir.exists():
        return

    skills_meta = []

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        with open(skill_md) as f:
            content = f.read()

        meta, body = parse_frontmatter(content)
        skill_name = meta.get("name", skill_dir.name)

        if target == "codex":
            # Codex: 保持相同目录结构 skills/skill-name/SKILL.md
            codex_skill_dir = output_dir / "skills" / skill_name
            codex_skill_dir.mkdir(parents=True, exist_ok=True)
            output = convert_to_codex(meta, body, plugin_name)
            with open(codex_skill_dir / "SKILL.md", "w") as f:
                f.write(output)

            # 复制 scripts 和 references
            _copy_supporting_files(skill_dir, codex_skill_dir)

        elif target == "trae":
            # Trae: 输出到 .trae/rules/{plugin_name}-{skill_name}.md
            trae_rules_dir = output_dir / ".trae" / "rules"
            trae_rules_dir.mkdir(parents=True, exist_ok=True)
            output = convert_to_trae(meta, body, plugin_name)
            rule_filename = f"{plugin_name}-{skill_name}.md"
            with open(trae_rules_dir / rule_filename, "w") as f:
                f.write(output)

        elif target == "hermes":
            # Hermes: 技能放在 skills/ 目录下
            hermes_skills_dir = output_dir / "skills" / skill_name
            hermes_skills_dir.mkdir(parents=True, exist_ok=True)
            output = convert_to_hermes(meta, body, plugin_name)
            with open(hermes_skills_dir / "SKILL.md", "w") as f:
                f.write(output)

            skills_meta.append({
                "name": skill_name,
                "rel_path": f"skills/{skill_name}/SKILL.md",
            })

            # 复制 scripts 和 references
            _copy_supporting_files(skill_dir, hermes_skills_dir)

    # 4. 为 Hermes 生成 Python 插件骨架
    if target == "hermes" and skills_meta:
        init_code = generate_hermes_plugin_init(plugin_name, skills_meta)
        with open(output_dir / "__init__.py", "w") as f:
            f.write(init_code)
        with open(output_dir / "schemas.py", "w") as f:
            f.write(generate_hermes_schemas_py())
        with open(output_dir / "tools.py", "w") as f:
            f.write(generate_hermes_tools_py())

    # 5. 转换命令
    commands_dir = source_dir / "commands"
    if commands_dir.exists() and target in ("codex",):
        codex_cmd_dir = output_dir / "commands"
        codex_cmd_dir.mkdir(parents=True, exist_ok=True)
        _copy_dir(commands_dir, codex_cmd_dir)

    # 6. 复制 CONNECTORS.md 和 README.md
    for fname in ["CONNECTORS.md", "README.md", "LICENSE", "LICENSE.txt"]:
        src = source_dir / fname
        if src.exists():
            dst = output_dir / fname
            if not dst.exists():
                with open(src) as f_in, open(dst, "w") as f_out:
                    f_out.write(f_in.read())


def _copy_supporting_files(src_dir: Path, dst_dir: Path):
    """复制 scripts 和 references 子目录"""
    for sub in ["scripts", "references"]:
        sub_src = src_dir / sub
        if sub_src.exists():
            sub_dst = dst_dir / sub
            _copy_dir(sub_src, sub_dst)


def _copy_dir(src: Path, dst: Path):
    """递归复制目录"""
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        item_dst = dst / item.name
        if item.is_dir():
            _copy_dir(item, item_dst)
        else:
            with open(item) as f_in, open(item_dst, "w") as f_out:
                f_out.write(f_in.read())


def migrate_all(source_root: Path, output_root: Path, target: str):
    """迁移所有内置插件"""
    # 内置插件列表
    vendored = [
        "productivity", "sales", "customer-support", "product-management",
        "marketing", "legal", "finance", "data", "enterprise-search",
        "engineering", "human-resources", "design", "operations",
        "bio-research", "cowork-plugin-management", "small-business",
        "pdf-viewer",
    ]

    for plugin_name in vendored:
        plugin_dir = source_root / plugin_name
        if not plugin_dir.exists():
            continue
        plugin_output = output_root / plugin_name
        migrate_plugin(plugin_dir, plugin_output, target)

    print(f"\nDone! Migrated {len(vendored)} plugins to {target} format.")


# ──────────────────────────────────────────────────────────────
# 单独迁移一个技能文件
# ──────────────────────────────────────────────────────────────

def migrate_single_skill(skill_path: Path, output_path: Path, target: str,
                         plugin_name: str = "unknown"):
    """迁移单个 SKILL.md 文件"""
    with open(skill_path) as f:
        content = f.read()

    meta, body = parse_frontmatter(content)

    if target == "codex":
        output = convert_to_codex(meta, body, plugin_name)
    elif target == "trae":
        output = convert_to_trae(meta, body, plugin_name)
    elif target == "hermes":
        output = convert_to_hermes(meta, body, plugin_name)
    else:
        raise ValueError(f"Unknown target: {target}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(output)
    print(f"  Converted: {skill_path} → {output_path}")


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="将 Claude Code 插件迁移到 Codex / Trae / Hermes 平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 迁移单个插件到 Codex
  python migrate_skills.py --target codex --input ./sales --output ./codex-plugins/sales

  # 迁移单个插件到 Trae
  python migrate_skills.py --target trae --input ./sales --output ./trae-rules/sales

  # 迁移单个插件到 Hermes
  python migrate_skills.py --target hermes --input ./sales --output ./hermes-plugins/sales

  # 迁移所有内置插件到指定平台
  python migrate_skills.py --target all --all-plugins --output ./migrated

  # 迁移单个 SKILL.md 文件
  python migrate_skills.py --target trae --skill ./skills/call-prep/SKILL.md --output ./rules/call-prep.md
        """,
    )
    parser.add_argument("--target", choices=["codex", "trae", "hermes", "all"],
                        default="all", help="目标平台")
    parser.add_argument("--input", type=Path, help="源插件目录")
    parser.add_argument("--output", type=Path, required=True, help="输出目录")
    parser.add_argument("--skill", type=Path, help="单个 SKILL.md 文件路径")
    parser.add_argument("--all-plugins", action="store_true",
                        help="迁移所有内置插件（需要 --input 指向仓库根目录）")
    parser.add_argument("--plugin-name", default="unknown",
                        help="插件名称（单文件迁移时使用）")

    args = parser.parse_args()

    targets = ["codex", "trae", "hermes"] if args.target == "all" else [args.target]

    if args.skill:
        # 单文件迁移
        for t in targets:
            out = args.output / t / args.skill.name if args.target == "all" else args.output
            migrate_single_skill(args.skill, out, t, args.plugin_name)
    elif args.all_plugins:
        # 全量迁移
        source_root = args.input or Path.cwd()
        for t in targets:
            out = args.output / t if args.target == "all" else args.output
            migrate_all(source_root, out, t)
    elif args.input:
        # 单插件迁移
        for t in targets:
            out = args.output / t if args.target == "all" else args.output
            migrate_plugin(args.input, out, t)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()