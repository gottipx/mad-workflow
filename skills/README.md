# Skill Metadata Convention

Each skill includes `agents/openai.yaml` because it is the required ChatGPT skill UI metadata file.

The `interface.display_name` and `interface.short_description` fields are intentionally written in a portable style for Hermes Agent, OpenCode, and similar coding-agent runtimes:

- short operational title
- complete one-sentence description
- explicit trigger area
- no marketing language
- no long background explanation
- no model- or vendor-specific instructions

Each skill package also includes `agents/runtime.yaml` as optional neutral metadata for runtimes that prefer a generic manifest.
