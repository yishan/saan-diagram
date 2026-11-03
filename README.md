# Saan Kits

**English** | [简体中文](README.zh-CN.md)

An expanding collection of agent skills for turning requirements into diagrams, documents, and prototypes. Install the skills you need, or select the whole collection.

**Available today: `saan-diagram`.** Mermaid, PRD writing, and prototyping skills are planned and are not yet included.

The GitHub repository is [`yishan/saankits`](https://github.com/yishan/saankits), renamed from `yishan/saan-diagram`. Use the new source in installation commands. The existing `saan-diagram` skill and plugin identifiers are unchanged.

## Available skills

| Skill | Use it for | Outputs | Documentation |
|---|---|---|---|
| [`saan-diagram`](skills/saan-diagram/SKILL.md) | Business architecture, process flows, role handoffs, data relationships, and milestones in English or Chinese | Editable YAML/JSON specs, HTML, SVG, PNG, and Feishu/Lark whiteboard DSL | [Guide](docs/saan-diagram/README.md) · [中文指南](docs/saan-diagram/README.zh-CN.md) · [Gallery](https://saan-diagram.vercel.app/) |

Each skill has its own `SKILL.md` and carries the resources needed for its core workflow. Installing one skill does not require installing the whole collection.

## Installation

### skills CLI

Use a Node.js version supported by the [skills CLI](https://github.com/vercel-labs/skills).

```bash
# List available skills without installing
npx skills add yishan/saankits --list

# Select skills and target agents interactively
npx skills add yishan/saankits

# Install just Saan Diagram
npx skills add yishan/saankits --skill saan-diagram

# Install all currently available skills to Codex
npx skills add yishan/saankits --skill '*' -a codex
```

Installation is project-level by default; add `-g` for user-level installation. The whole-collection command currently selects only `saan-diagram`. Skills added later require a subsequent installation; this is not a subscription to future skills.

Runtime dependencies belong to each skill. See [Saan Diagram dependencies](docs/saan-diagram/README.md#dependencies) for Python, PNG export, and optional whiteboard publishing requirements.

### Claude Code plugin

```text
/plugin marketplace add yishan/saankits
/plugin install saan-diagram@saan-diagram
```

The plugin display name is **Saan Kits**. The plugin and marketplace identifiers remain `saan-diagram` for compatibility with existing installations. Plugin installation includes the bundled skills; use the skills CLI for individual selection.

For manual installation, copy the complete `skills/<skill-name>/` directory into the target agent's skills directory. See the [Saan Diagram guide](docs/saan-diagram/README.md#installation) for Claude Code and Claude.ai instructions.

## Planned skills

These are planned scopes, not installable entries. Names and boundaries may change during development.

| Planned skill | Intended scope |
|---|---|
| `saan-mermaid` | Mermaid source for diagrams maintained in Markdown and technical documentation |
| `saan-prd-writing` | Requirements, business rules, acceptance criteria, and unresolved questions in a PRD |
| `saan-prototype` | Runnable interface prototypes with key interactions and states |

A shared workflow skill can be added when a repeatable workflow across these skills has been validated. Each skill should first be useful on its own.

## Repository structure

```text
skills/                  Installable skill packages
  saan-diagram/          Existing diagram skill and runtime resources
docs/                    User documentation and preview images
  saan-diagram/          English and Chinese diagram guides
scripts/                 Repository maintenance and validation helpers
tests/                   Existing Saan Diagram regression tests
page/                    Existing Saan Diagram introduction and gallery
.claude-plugin/          Collection packaging; legacy identifiers retained
```

Agent instructions live in `skills/<skill-name>/SKILL.md`. Root READMEs provide the collection catalog; detailed user guides live in `docs/<skill-name>/`. The existing gallery continues to describe Saan Diagram.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for skill boundaries, packaging, documentation, and validation requirements. Add a skill directory only when it contains a usable implementation; record future ideas in the planned-skills table instead of discoverable placeholders.

The existing renderer, examples, and tests remain in place. See [Saan Diagram development and validation](docs/saan-diagram/README.md#development-and-validation) for its checks and [page maintenance](page/README.md) for gallery synchronization.

Skill instructions use English as the canonical entry point. Follow the user's explicitly requested output language; otherwise use the language of the request. Each skill documents any output-language limitations.

## License

[MIT](LICENSE) © 2026 Yishan. Skill-specific acknowledgments are included in their documentation.
