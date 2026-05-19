"""CLI entry point — `acc` command group."""

import click
from acc_core.config import ensure_dirs
from acc_core.utils.logging import setup as setup_logging


@click.group()
@click.version_option(package_name="android-claude-controller")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, verbose):
    """Android Claude Controller — control Android devices via natural language."""
    setup_logging(verbose)
    ensure_dirs()
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


from cli.goal import goal_cmd
from cli.chat import chat_cmd
from cli.device_cmd import device_group
from cli.config_cmd import config_group
from cli.screenshot import screenshot_cmd
from cli.ui_dump import ui_dump_cmd
from cli.web import web_group

cli.add_command(goal_cmd)
cli.add_command(chat_cmd)
cli.add_command(device_group)
cli.add_command(screenshot_cmd)
cli.add_command(ui_dump_cmd)
cli.add_command(config_group)
cli.add_command(web_group)
