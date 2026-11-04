# Saan Kits

**English** | [简体中文](README.zh-CN.md)

[Explore Saan Kits](https://kits.yishan.app/)

An expanding collection of agent skills for turning requirements into diagrams, documents, and prototypes. Install the skills you need, or select the whole collection.

**Available today: `saan-diagram`, `saan-mermaid`, `saan-discovery`, and `saan-prd-writing`.** Prototyping is planned and is not yet included.

The GitHub repository is [`yishan/saankits`](https://github.com/yishan/saankits), renamed from `yishan/saan-diagram`. Use the new source in installation commands. The existing `saan-diagram` skill and plugin identifiers are unchanged.

## Available skills

| Skill | Use it for | Outputs | Documentation |
|---|---|---|---|
| [`saan-diagram`](skills/saan-diagram/SKILL.md) | Business architecture, process flows, role handoffs, data relationships, and milestones in English or Chinese | Editable YAML/JSON specs, HTML, SVG, PNG, and Feishu/Lark whiteboard DSL | [Guide](docs/saan-diagram/README.md) · [中文指南](docs/saan-diagram/README.zh-CN.md) · [Gallery](https://kits.yishan.app/diagram/) |
| [`saan-mermaid`](skills/saan-mermaid/SKILL.md) | Diagrams kept in Markdown and design documents, sequence, state, and Gantt charts, and process reviews against a control list | Mermaid source, an optional rendered image, and review findings | [Guide](docs/saan-mermaid/README.md) · [中文指南](docs/saan-mermaid/README.zh-CN.md) · [Introduction](https://kits.yishan.app/mermaid/) |
| [`saan-discovery`](skills/saan-discovery/SKILL.md) | Interactive consumer, enterprise, public-sector, and mixed discovery, interview preparation, and product-fit assessment | Topic-based research briefs, interview guides, gap queues, and fit assessments | [Guide](docs/saan-discovery/README.md) · [中文指南](docs/saan-discovery/README.zh-CN.md) · [Introduction](https://kits.yishan.app/discovery/) · [中文介绍](https://kits.yishan.app/discovery/zh/) |
| [`saan-prd-writing`](skills/saan-prd-writing/SKILL.md) | Full PRDs, requirements specifications, scoped feature changes, and document revisions | Concrete rules, business fields, state effects, acceptance scenarios, and open decisions | [Guide](docs/saan-prd-writing/README.md) · [中文指南](docs/saan-prd-writing/README.zh-CN.md) · [Introduction](https://kits.yishan.app/prd-writing/) |

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

# Install just Saan Mermaid
npx skills add yishan/saankits --skill saan-mermaid

# Install just Saan Discovery
npx skills add yishan/saankits --skill saan-discovery

# Install just Saan PRD Writing
npx skills add yishan/saankits --skill saan-prd-writing

# Install all currently available skills to Codex
npx skills add yishan/saankits --skill '*' -a codex
```

Installation is project-level by default; add `-g` for user-level installation. The whole-collection command currently selects all four skills listed above. Skills added later require a subsequent installation; this is not a subscription to future skills.

Saan Discovery and Saan PRD Writing are text-only and need no external runtime or service for its core workflow. Accessing source files may require additional tools. Runtime dependencies belong to each skill. See [Saan Diagram dependencies](docs/saan-diagram/README.md#dependencies) and [Saan Mermaid dependencies](docs/saan-mermaid/README.md#dependencies).

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
| `saan-prototype` | Runnable interface prototypes with key interactions and states |

A shared workflow skill can be added when a repeatable workflow across these skills has been validated. Each skill should first be useful on its own.

## Repository structure

```text
skills/                  Installable skill packages
  saan-diagram/          Existing diagram skill and runtime resources
  saan-mermaid/          Mermaid drawing and process review skill
  saan-discovery/        Business discovery and internal interview methods
  saan-prd-writing/      Requirements writing, templates, and a worked example
docs/                    User documentation and preview images
  saan-diagram/          English and Chinese diagram guides
  saan-mermaid/          English and Chinese Mermaid guides
  saan-discovery/        English and Chinese Discovery guides and validation records
  saan-prd-writing/      English and Chinese PRD guides and validation records
scripts/                 Repository maintenance and validation helpers
tests/                   Saan Diagram regression tests; saan-mermaid/ holds Mermaid tests
page/                    Collection overview, with one second-level page per skill
.claude-plugin/          Collection packaging; legacy identifiers retained
```

Agent instructions live in `skills/<skill-name>/SKILL.md`. Root READMEs provide the collection catalog; detailed user guides live in `docs/<skill-name>/`. The site overview is at `/`, with `/diagram/`, `/mermaid/`, `/discovery/`, and `/prd-writing/` below it. Discovery and PRD Writing introductions initially follow the browser language; language and appearance controls are at the top right.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for skill boundaries, packaging, documentation, and validation requirements. Add a skill directory only when it contains a usable implementation; record future ideas in the planned-skills table instead of discoverable placeholders.

The existing renderer, examples, and tests remain in place. See [Saan Diagram development and validation](docs/saan-diagram/README.md#development-and-validation) for its checks and [page maintenance](page/README.md) for gallery synchronization.

Skill instructions use English as the canonical entry point. Follow the user's explicitly requested output language; otherwise use the language of the request. Each skill documents any output-language limitations.

## License

[MIT](LICENSE) © 2026 Yishan. Skill-specific acknowledgments are included in their documentation.
