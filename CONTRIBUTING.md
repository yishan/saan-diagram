# Contributing to Saan Kits

Saan Kits groups independently useful skills in one repository. The GitHub source is `yishan/saankits`, renamed from `yishan/saan-diagram`. Use the new repository URL while retaining existing skill and plugin identifiers for compatibility.

## Add a skill

1. Define a distinct user task, expected outputs, and validation criteria. Explain overlap with existing skills in the description where it affects selection.
2. Create `skills/saan-<name>/SKILL.md` with YAML frontmatter containing `name` and `description`. The name must match the directory. Use an English instruction entry point and follow the user's output-language choice, falling back to the request language.
3. Bundle runtime scripts, templates, and required references inside that skill directory. Add only directories the implementation uses. A user installing only this directory must have the resources needed for its core workflow; document external tools and optional integrations.
4. Add English and Chinese user guides under `docs/<skill-name>/`. Keep repository instructions and promotional copy outside the runtime skill entry point. Link guides from both root READMEs.
5. Validate the standalone package and its real workflow before listing it as available. Move its entry from the planned table into the available catalog in both languages.

Do not create placeholder `SKILL.md` files for planned skills. They can be discovered and installed before the implementation exists.

## Keep dependencies explicit

A skill may use another installed skill when the requested task benefits from it. Document whether that dependency is required or optional and what happens if it is absent. Do not assume installing one skill also installs its peers. Prefer optional composition when the core task can be completed independently.

Keep reusable source material maintainable, but include required runtime resources in each distributed package. Avoid runtime paths such as `../../shared/` that only work in a full repository checkout.

## Preserve Saan Diagram

`skills/saan-diagram/` remains the installable unit. Its scripts, guides, assets, and skill name stay together. Existing regression tests are under `tests/`; new skills can place their tests in `tests/<skill-name>/` and register the appropriate checks in CI without moving the existing suite just for symmetry.

`scripts/render_smoke.py` and `scripts/sync_page.py` currently serve Saan Diagram. `page/` remains its gallery. Update these only when the diagram examples or page change.

The Claude Code plugin display name is Saan Kits. Both `.claude-plugin` manifests retain `saan-diagram` identifiers, and the plugin entry points to the repository root so its `skills/` collection can grow. Keep manifest identities consistent with the documented install command. Preserve skill-specific versions separately when future skills are added.

## Check a change

- Validate each changed skill's frontmatter, referenced files, and standalone directory contents.
- Check relative documentation links, image paths, and English/Chinese navigation after moves.
- Use `npx skills add . --list` to inspect local discovery without installing. Planned skills must not appear.
- Run checks appropriate to the affected skill. Saan Diagram commands are in its [development guide](docs/saan-diagram/README.md#development-and-validation).
- Update CI when a new skill introduces an executable workflow. Document what was tested and any external integration that remains unverified.

Repository discovery, installation, rendering, external publishing, and skills.sh listing are separate outcomes. Report only the outcomes verified for the change.
