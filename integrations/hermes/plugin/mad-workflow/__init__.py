"""MAD Workflow plugin for Hermes.

Provides a `hermes mad` CLI command. The plugin is deliberately thin: it
uses existing Hermes Kanban/profile/worktree primitives instead of replacing
or forking them.
"""


def register(ctx):
    from . import cli

    ctx.register_cli_command(
        name="mad",
        help="Multi-Agent Delivery workflow helpers",
        setup_fn=cli.setup_cli,
        handler_fn=cli.mad_command,
        description=(
            "Hermes-native MAD workflow helpers: validate task contracts, "
            "create Kanban tasks from contracts, initialize boards/profiles, "
            "and check git diffs against allowed/forbidden scope."
        ),
    )

