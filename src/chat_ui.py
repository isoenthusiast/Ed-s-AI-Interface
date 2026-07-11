"""
Beautiful CLI chat interface using Rich.
"""

import sys
from datetime import datetime
from typing import Generator

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

from src.agent import AIAgent


console = Console()


def print_welcome(agent: AIAgent):
    """Display the welcome screen."""
    console.clear()
    title = Text()
    title.append("🧠 ", style="bold")
    title.append(agent.config["agent_name"], style="bold cyan")
    title.append("\n" + "─" * 50)

    welcome = Panel(
        Markdown(
            f"Welcome to **{agent.config['agent_name']}**!\n\n"
            f"• **Model**: `{agent.config['model']}`\n"
            f"• **Provider**: `{agent.config['provider']}`\n"
            f"• **Session**: `{agent.session_id}`\n\n"
            "Type your messages below. Use **`/help`** for commands."
        ),
        title="🚀 Ready",
        border_style="green",
        box=box.ROUNDED,
    )

    console.print(title)
    console.print(welcome)
    console.print()


def print_help():
    """Display the help panel."""
    help_table = Table(
        title="🤖 Available Commands",
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
    )
    help_table.add_column("Command", style="yellow")
    help_table.add_column("Description", style="white")

    help_table.add_row("/help", "Show this help message")
    help_table.add_row("/exit", "Exit the program")
    help_table.add_row("/new", "Start a new conversation session")
    help_table.add_row("/sessions", "List all previous sessions")
    help_table.add_row("/switch <id>", "Switch to a different session")
    help_table.add_row("/delete <id>", "Delete a session")
    help_table.add_row("/facts", "Show what I know about you")
    help_table.add_row("/note <title> | <content>", "Save a note for me to remember")
    help_table.add_row("/notes", "Show all your notes")
    help_table.add_row("/forget", "Clear all facts about you")
    help_table.add_row("/clear", "Clear the screen")

    console.print(help_table)
    console.print()


def print_facts(agent: AIAgent):
    """Display stored facts."""
    facts = agent.context.get_facts()
    if not facts:
        console.print("[yellow]I don't have any facts stored about you yet.[/yellow]")
        console.print("Tell me about yourself and I'll remember!")
        return

    table = Table(title="📌 What I Know About You", box=box.ROUNDED)
    table.add_column("Category", style="cyan")
    table.add_column("Fact", style="white")
    table.add_column("When", style="dim")

    for f in facts[-20:]:
        when = f["timestamp"][:16].replace("T", " ")
        table.add_row(f["category"], f["fact"], when)

    console.print(table)


def print_notes(agent: AIAgent):
    """Display stored notes."""
    notes = agent.context.get_notes()
    if not notes:
        console.print("[yellow]You haven't saved any notes yet.[/yellow]")
        console.print("Use [bold]/note <title> | <content>[/bold] to add one.")
        return

    table = Table(title="📝 Your Notes", box=box.ROUNDED)
    table.add_column("Title", style="cyan")
    table.add_column("Content", style="white")
    table.add_column("Date", style="dim")

    for n in notes[-10:]:
        when = n["timestamp"][:16].replace("T", " ")
        table.add_row(n["title"], n["content"][:100], when)

    console.print(table)


def print_sessions(agent: AIAgent):
    """Display all sessions."""
    sessions = agent.list_sessions()
    if not sessions:
        console.print("[yellow]No previous sessions found.[/yellow]")
        return

    table = Table(title="💬 Conversation Sessions", box=box.ROUNDED)
    table.add_column("Session ID", style="cyan")
    table.add_column("Messages", style="white", justify="right")
    table.add_column("Last Active", style="dim")
    table.add_column("Preview", style="italic")

    for s in sessions:
        when = s["last_active"][:16].replace("T", " ")
        table.add_row(s["id"], str(s["count"]), when, s["preview"])

    console.print(table)


def handle_command(cmd: str, agent: AIAgent) -> bool:
    """
    Process a command. Returns False if the program should exit.
    """
    cmd = cmd.strip().lower()

    if cmd in ("/exit", "/quit"):
        console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]")
        return False

    if cmd == "/help":
        print_help()
        return True

    if cmd == "/new":
        agent.new_session()
        console.print(f"[green]Started new session:[/green] [bold]{agent.session_id}[/bold]")
        return True

    if cmd == "/sessions":
        print_sessions(agent)
        return True

    if cmd.startswith("/switch "):
        sid = cmd[8:].strip()
        agent.switch_session(sid)
        console.print(f"[green]Switched to session:[/green] [bold]{sid}[/bold]")
        return True

    if cmd.startswith("/delete "):
        sid = cmd[8:].strip()
        if agent.delete_session(sid):
            console.print(f"[green]Deleted session:[/green] [bold]{sid}[/bold]")
        else:
            console.print(f"[red]Session not found:[/red] {sid}")
        return True

    if cmd == "/facts":
        print_facts(agent)
        return True

    if cmd.startswith("/note "):
        rest = cmd[6:].strip()
        if "|" in rest:
            title, content = rest.split("|", 1)
            agent.context.add_note(title.strip(), content.strip())
            console.print(f"[green]Note saved:[/green] [bold]{title.strip()}[/bold]")
        else:
            console.print("[red]Usage:[/red] /note <title> | <content>")
        return True

    if cmd == "/notes":
        print_notes(agent)
        return True

    if cmd == "/forget":
        if Confirm.ask("[yellow]Clear all stored facts about you?[/yellow]"):
            agent.context.clear_facts()
            console.print("[green]Facts cleared![/green]")
        return True

    if cmd == "/clear":
        console.clear()
        return True

    # Unknown command
    console.print(f"[red]Unknown command:[/red] {cmd}")
    console.print("Type [bold]/help[/bold] for available commands.")
    return True


def chat_loop(agent: AIAgent):
    """Main chat loop with streaming responses."""
    print_welcome(agent)

    while True:
        try:
            # Get user input
            prompt_text = Text.assemble(
                ("🧑 You", "bold green"),
                ("  > ", "dim"),
            )
            user_input = Prompt.ask(prompt_text)

            if not user_input.strip():
                continue

            # Handle commands
            if user_input.startswith("/"):
                if not handle_command(user_input, agent):
                    break
                continue

            # Get AI response (streaming)
            console.print()
            response_stream = agent.chat(user_input)
            response_text = ""

            with Live(console=console, refresh_per_second=15) as live:
                for chunk in response_stream:
                    response_text += chunk
                    md = Markdown(response_text)
                    panel = Panel(
                        md,
                        title=f"[bold cyan]🧠 {agent.config['agent_name']}[/bold cyan]",
                        border_style="cyan",
                        box=box.ROUNDED,
                    )
                    live.update(panel)

            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type /exit to quit.[/yellow]")
            continue
        except Exception as e:
            console.print(f"\n[red]Unexpected error:[/red] {e}")
            continue


def main():
    """Entry point for the chat UI."""
    try:
        agent = AIAgent()
        chat_loop(agent)
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]")
    except Exception as e:
        console.print(f"\n[red]Fatal error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
