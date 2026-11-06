"""CLI Entrypoint for Seed Synthesis Engine using Typer."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer
from rich.console import Console
from rich.table import Table

from src.config import load_config
from src.extraction.batch_extractor import BatchMetadataExtractor
from src.extraction.llm_client import LLMClient
from src.ingestion.scanner import IngestionScanner
from src.models import ArticleArchetype
from src.storage.db import init_db
from src.storage.repository import StorageRepository
from src.storage.retriever import SeedRetriever
from src.synthesis.synthesizer import ArticleSynthesizer

app = typer.Typer(
    name="seed-synthesis-engine",
    help="Lightweight Seed Synthesis Engine & Metadata Indexing Pipeline",
    add_completion=False,
)
console = Console(legacy_windows=False)


@app.command("init")
def cmd_init(
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
):
    """Initialize catalog.db and folder structure."""
    cfg = load_config(config_file)
    cfg.ensure_directories()
    init_db(cfg.paths.db_path)
    console.print(f"[green][OK] Database and runtime directories initialized at {cfg.paths.data_dir}[/green]")


@app.command("ingest")
def cmd_ingest(
    input_dir: Optional[Path] = typer.Option(None, "--input-dir", "-i", help="Inbox directory with raw files"),
    move_archive: bool = typer.Option(False, "--move-archive", help="Move processed files to archive instead of copy"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-processing existing hashed files"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
):
    """Preprocess raw PDF/MD/TXT articles into cleaned texts and visual assets."""
    cfg = load_config(config_file)
    cfg.ensure_directories()
    init_db(cfg.paths.db_path)

    scanner = IngestionScanner(config=cfg)
    target_inbox = input_dir or cfg.paths.inbox_dir

    console.print(f"[bold blue]Scanning inbox: {target_inbox}[/bold blue]")
    records = scanner.scan_inbox(inbox_dir=target_inbox, force=force, move_archive=move_archive)

    console.print(f"[green][OK] Successfully ingested {len(records)} articles into processed storage.[/green]")
    for r in records[:5]:
        console.print(f"  - [{r.doc_id}] {r.title} ({r.source_format}, chars: {r.char_count}, images: {r.image_count})")
    if len(records) > 5:
        console.print(f"  ... and {len(records) - 5} more articles.")


@app.command("extract")
def cmd_extract(
    concurrency: int = typer.Option(5, "--concurrency", "-n", help="Async semaphore concurrency"),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="LLM model name"),
    provider: str = typer.Option("openai", "--provider", "-p", help="LLM provider: openai or gemini"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Max pending articles to process"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
):
    """Asynchronously extract structured ArticleMetadata with checkpoint resumption."""
    cfg = load_config(config_file)
    cfg.ensure_directories()
    init_db(cfg.paths.db_path)

    llm = LLMClient(provider=provider, model=model)
    extractor = BatchMetadataExtractor(config=cfg, llm_client=llm, concurrency=concurrency)

    pending = extractor.get_pending_articles()
    console.print(f"[bold blue]Found {len(pending)} pending articles for metadata extraction.[/bold blue]")

    if not pending:
        console.print("[yellow]No pending articles. All articles are already INDEXED.[/yellow]")
        return

    if llm.api_key:
        processed_ids = asyncio.run(extractor.run(max_items=limit))
    else:
        processed_ids = extractor.run_sync(max_items=limit)
    console.print(f"[green][OK] Completed metadata extraction for {len(processed_ids)} articles.[/green]")


@app.command("search")
def cmd_search(
    topic: str = typer.Option(..., "--topic", "-t", help="Topic for search"),
    direction: str = typer.Option("", "--direction", "-d", help="Angle/direction for complementary search"),
    archetype: Optional[str] = typer.Option(None, "--archetype", "-a", help="Desired archetype"),
    count: int = typer.Option(3, "--count", "-k", help="Number of seed articles to retrieve (2~3)"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
):
    """Search and preview complementary Seed articles without drafting."""
    cfg = load_config(config_file)
    init_db(cfg.paths.db_path)

    arch_enum = ArticleArchetype(archetype) if archetype else None
    retriever = SeedRetriever(config=cfg)
    seeds = retriever.select_complementary_seeds(
        topic=topic,
        direction=direction,
        target_archetype=arch_enum,
        count=count,
    )

    if not seeds:
        console.print("[red]No matching seed articles found in catalog.db.[/red]")
        return

    table = Table(title=f"Complementary Seeds for: '{topic}'")
    table.add_column("Role", style="cyan")
    table.add_column("Doc ID", style="magenta")
    table.add_column("Title", style="bold white")
    table.add_column("Reason / Contribution", style="green")

    for s in seeds:
        table.add_row(s.seed_type, s.doc_id, s.title, s.reason)

    console.print(table)


@app.command("generate")
def cmd_generate(
    topic: str = typer.Option(..., "--topic", "-t", help="Draft topic"),
    direction: str = typer.Option("", "--direction", "-d", help="Writing angle or thesis"),
    archetype: Optional[str] = typer.Option(None, "--archetype", "-a", help="Article archetype"),
    count: int = typer.Option(3, "--count", "-k", help="Number of seeds to cross-synthesize (2~3)"),
    use_my_style: bool = typer.Option(False, "--use-my-style", help="Apply learned UserStyleProfile if available"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="LLM model name"),
    provider: str = typer.Option("openai", "--provider", "-p", help="LLM provider: openai or gemini"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
):
    """Retrieve complementary seeds, plan blueprint, and synthesize draft markdown."""
    cfg = load_config(config_file)
    cfg.ensure_directories()
    init_db(cfg.paths.db_path)

    arch_enum = ArticleArchetype(archetype) if archetype else None
    retriever = SeedRetriever(config=cfg)

    console.print(f"[bold cyan]>> Step 1: Retrieving complementary seeds for '{topic}'...[/bold cyan]")
    seeds = retriever.select_complementary_seeds(
        topic=topic,
        direction=direction,
        target_archetype=arch_enum,
        count=count,
    )

    if not seeds:
        console.print("[red]Error: No indexed seed articles available. Run 'ingest' and 'extract' first.[/red]")
        raise typer.Exit(code=1)

    for s in seeds:
        console.print(f"  - [{s.seed_type}] [bold]{s.doc_id}[/bold]: {s.title} ({s.reason})")

    llm = LLMClient(provider=provider, model=model)
    synthesizer = ArticleSynthesizer(config=cfg, llm_client=llm)

    style_profile = None
    if use_my_style:
        from src.synthesis.style_learner import StyleLearner
        learner = StyleLearner(config=cfg)
        style_profile = learner.get_active_profile()
        if style_profile:
            console.print(f"[bold magenta]Applying UserStyleProfile v{style_profile.profile_version}[/bold magenta]")
        else:
            console.print("[yellow]Warning: No style profile found at data/my_corpus/style_profile.json. Using neutral mode.[/yellow]")

    console.print("[bold cyan]>> Step 2: Planning blueprint and synthesizing full draft...[/bold cyan]")
    if llm.api_key:
        out_file, content, blueprint, distilled_sheets = asyncio.run(
            synthesizer.synthesize(
                topic=topic,
                direction=direction,
                seeds=seeds,
                archetype=arch_enum,
                style_profile=style_profile,
                output_dir=output_dir,
            )
        )
    else:
        out_file, content, blueprint, distilled_sheets = synthesizer.synthesize_sync(
            topic=topic,
            direction=direction,
            seeds=seeds,
            archetype=arch_enum,
            style_profile=style_profile,
            output_dir=output_dir,
        )

    console.print(f"[bold green][OK] Successfully generated draft at:[/bold green] {out_file}")
    console.print(f"[dim]Proposed Title: {blueprint.proposed_title}[/dim]")
    console.print(f"[dim]Synthesized Reframing: {blueprint.synthesized_reframing}[/dim]")


@app.command("learn-style")
def cmd_learn_style(
    min_count: int = typer.Option(5, "--min-count", "-m", help="Minimum finalized creations required"),
    force: bool = typer.Option(False, "--force", "-f", help="Force style learning even if fewer than min_count"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
):
    """Extract and persist UserStyleProfile from finalized creations."""
    cfg = load_config(config_file)
    init_db(cfg.paths.db_path)
    from src.synthesis.style_learner import StyleLearner
    learner = StyleLearner(config=cfg)
    profile = learner.learn_style_sync(min_count=min_count, force=force)
    if not profile:
        count = learner.count_finalized_creations()
        console.print(f"[yellow]Insufficient finalized creations for learning ({count}/{min_count}). Use --force to extract anyway.[/yellow]")
        return
    console.print(f"[bold green][OK] Successfully learned UserStyleProfile v{profile.profile_version} from {profile.based_on_creation_count} articles![/bold green]")
    console.print(f"[dim]Saved profile to: {learner.profile_path}[/dim]")


@app.command("ui")
@app.command("server")
def cmd_ui(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host address"),
    port: int = typer.Option(8501, "--port", "-p", help="Port for Web Studio"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload for development"),
):
    """Launch the FastAPI + React Web Studio application."""
    import uvicorn
    console.print(f"[bold cyan]Launching Seed Studio Web App on http://{host}:{port}...[/bold cyan]")
    uvicorn.run("src.api.main:app", host=host, port=port, reload=reload)


@app.command("pipeline")
def cmd_pipeline(
    topic: str = typer.Option(..., "--topic", "-t", help="Draft topic"),
    direction: str = typer.Option("", "--direction", "-d", help="Writing angle or thesis"),
    archetype: Optional[str] = typer.Option(None, "--archetype", "-a", help="Article archetype"),
    input_dir: Optional[Path] = typer.Option(None, "--input-dir", "-i", help="Inbox directory"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    concurrency: int = typer.Option(5, "--concurrency", "-n", help="Extraction concurrency"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
):
    """End-to-End One-Click Pipeline: Ingest -> Extract -> Generate."""
    console.print("[bold yellow]=== Step 1: Ingestion ===[/bold yellow]")
    cmd_ingest(input_dir=input_dir, move_archive=False, force=False, config_file=config_file)

    console.print("\n[bold yellow]=== Step 2: Metadata Extraction ===[/bold yellow]")
    cmd_extract(concurrency=concurrency, config_file=config_file)

    console.print("\n[bold yellow]=== Step 3: Synthesis Generation ===[/bold yellow]")
    cmd_generate(
        topic=topic,
        direction=direction,
        archetype=archetype,
        count=3,
        output_dir=output_dir,
        config_file=config_file,
    )


@app.command("check")
def cmd_check(
    fix: bool = typer.Option(False, "--fix", "-f", help="Automatically fix backend lint issues"),
):
    """Run full quality gate: backend lint (Ruff), frontend lint (oxlint), and parallel test suite."""
    import subprocess

    console.print("[bold cyan]>> 1. Running backend lint with Ruff...[/bold cyan]")
    ruff_args = [sys.executable, "-m", "ruff", "check", "src", "tests"]
    if fix:
        ruff_args.append("--fix")
    res_ruff = subprocess.run(ruff_args)
    if res_ruff.returncode != 0 and not fix:
        console.print("[yellow]Hint: Run 'python run.py check --fix' to auto-resolve fixable issues.[/yellow]")

    console.print("\n[bold cyan]>> 2. Running frontend lint with oxlint...[/bold cyan]")
    subprocess.run(["npm", "--prefix", "frontend", "run", "lint"], shell=True)

    console.print("\n[bold cyan]>> 3. Running parallel pytest suite...[/bold cyan]")
    subprocess.run([sys.executable, "-m", "pytest"])


@app.command("test")
def cmd_test(
    k: Optional[str] = typer.Option(None, "-k", help="Filter tests by expression"),
):
    """Run parallelized automated pytest suite."""
    import subprocess
    cmd = [sys.executable, "-m", "pytest"]
    if k:
        cmd.extend(["-k", k])
    subprocess.run(cmd)


if __name__ == "__main__":
    app()
