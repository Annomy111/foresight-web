"""Enhanced visual components for the Foresight Analyzer"""
import time
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import (
    Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn,
    SpinnerColumn, MofNCompleteColumn, TimeElapsedColumn
)
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from rich.rule import Rule
from rich.columns import Columns
from rich.markdown import Markdown
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import base64
from io import BytesIO

console = Console()

class ForesightVisuals:
    """Enhanced visual components for foresight analysis"""

    def __init__(self):
        self.console = console
        plt.style.use('default')
        sns.set_palette("husl")

    def show_banner(self):
        """Display an enhanced startup banner"""
        banner_text = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║    ███████╗ ██████╗ ██████╗ ███████╗███████╗██╗ ██████╗ ██╗  ║
║    ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██║██╔════╝ ██║  ║
║    █████╗  ██║   ██║██████╔╝█████╗  ███████╗██║██║  ███╗██║  ║
║    ██╔══╝  ██║   ██║██╔══██╗██╔══╝  ╚════██║██║██║   ██║██║  ║
║    ██║     ╚██████╔╝██║  ██║███████╗███████║██║╚██████╔╝██║  ║
║    ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ║
║                                                               ║
║           🔮 AI-Powered Probabilistic Forecasting 🔮          ║
║                                                               ║
║                "Wisdom of the Silicon Crowd"                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """

        self.console.print(banner_text, style="bold cyan")

        # Add subtitle with animation
        subtitle = Text("Ensemble Forecasting with Large Language Models", style="italic blue")
        self.console.print(Align.center(subtitle))

        # Version and attribution
        self.console.print(Align.center("v2.0 Enhanced | Based on Schoenegger et al. (2024)"), style="dim")
        self.console.print()

    def create_forecast_overview_panel(self, question: str, models: List[str], iterations: int) -> Panel:
        """Create an overview panel for the forecast"""

        # Model list with emojis
        model_emojis = {
            "gemini": "🟢",
            "gpt": "🔵",
            "claude": "🟠",
            "grok": "⚫",
            "deepseek": "🟣"
        }

        model_display = []
        for model in models:
            model_name = model.split('/')[-1].lower()
            emoji = "🤖"
            for key, em in model_emojis.items():
                if key in model_name:
                    emoji = em
                    break
            model_display.append(f"{emoji} {model.split('/')[-1]}")

        content = f"""
[bold]Question:[/bold] {question}

[bold]Models ({len(models)}):[/bold]
{chr(10).join([f"  {model}" for model in model_display])}

[bold]Analysis Plan:[/bold]
  🎯 {iterations} iterations per model
  📊 {len(models) * iterations} total queries
  🧮 Statistical aggregation
  📈 Excel report generation
        """

        return Panel(
            content.strip(),
            title="🔮 Forecast Configuration",
            title_align="left",
            border_style="blue",
            padding=(1, 2)
        )

    def create_enhanced_progress(self) -> Progress:
        """Create an enhanced progress display"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
            expand=True
        )

    def create_results_table(self, model_stats: Dict[str, Any]) -> Table:
        """Create a beautiful results table"""
        table = Table(title="🎯 Model Performance Summary", show_header=True, header_style="bold magenta")

        table.add_column("Model", style="cyan", no_wrap=True, width=20)
        table.add_column("Mean", style="green", justify="center", width=10)
        table.add_column("Std Dev", style="yellow", justify="center", width=10)
        table.add_column("Range", style="blue", justify="center", width=12)
        table.add_column("Count", style="white", justify="center", width=8)
        table.add_column("Success", style="green", justify="center", width=10)
        table.add_column("Quality", style="magenta", justify="center", width=12)

        for model, stats in model_stats.items():
            model_name = model.split('/')[-1]

            # Quality indicator based on consistency
            consistency = 1 / (1 + stats.std) if stats.std > 0 else 1
            if consistency > 0.8:
                quality = "🟢 High"
            elif consistency > 0.6:
                quality = "🟡 Medium"
            else:
                quality = "🔴 Low"

            table.add_row(
                f"🤖 {model_name}",
                f"{stats.mean:.1f}%",
                f"±{stats.std:.1f}%",
                f"{stats.min:.0f}-{stats.max:.0f}%",
                str(stats.count),
                f"{stats.success_rate*100:.0f}%",
                quality
            )

        return table

    def create_consensus_panel(self, statistics: Any) -> Panel:
        """Create consensus analysis panel"""
        if statistics.std is None:
            consensus_text = "[red]Insufficient data for consensus analysis[/red]"
        else:
            # Consensus scoring
            cv = statistics.std / statistics.mean if statistics.mean > 0 else 1

            if cv < 0.1:
                consensus_level = "🟢 Very High"
                consensus_desc = "Models strongly agree"
            elif cv < 0.2:
                consensus_level = "🟡 High"
                consensus_desc = "Good agreement between models"
            elif cv < 0.4:
                consensus_level = "🟠 Moderate"
                consensus_desc = "Some disagreement between models"
            else:
                consensus_level = "🔴 Low"
                consensus_desc = "Significant disagreement between models"

            consensus_text = f"""
[bold]Consensus Level:[/bold] {consensus_level}
[bold]Description:[/bold] {consensus_desc}

[bold]Statistics:[/bold]
  • Standard Deviation: {statistics.std:.1f}%
  • Coefficient of Variation: {cv:.2f}
  • Range: {statistics.max - statistics.min:.1f}%
            """

        return Panel(
            consensus_text.strip(),
            title="🤝 Consensus Analysis",
            border_style="green"
        )

    def display_final_summary(self, ensemble_prob: float, statistics: Any, duration: float):
        """Display the final forecast summary with visual flair"""

        # Main result panel
        if ensemble_prob:
            prob_color = "green" if 30 <= ensemble_prob <= 70 else "yellow" if 20 <= ensemble_prob <= 80 else "red"

            result_text = f"""
[bold {prob_color}]{ensemble_prob:.1f}%[/bold {prob_color}]

[dim]Ensemble Probability[/dim]
            """

            result_panel = Panel(
                Align.center(result_text.strip()),
                title="🎯 Final Forecast",
                border_style=prob_color,
                width=30
            )
        else:
            result_panel = Panel(
                Align.center("[red]Unable to calculate\nensemble probability[/red]"),
                title="❌ Forecast Error",
                border_style="red",
                width=30
            )

        # Stats panel
        stats_text = f"""
[bold]Analysis Completed[/bold]

⏱️  Duration: {duration:.1f}s
📊  Queries: {statistics.total_queries}
✅  Success: {statistics.successful_queries}
❌  Failed: {statistics.failed_queries}
🎯  Valid Probabilities: {statistics.valid_probabilities}
        """

        stats_panel = Panel(
            stats_text.strip(),
            title="📈 Statistics",
            border_style="blue",
            width=30
        )

        # Display side by side
        self.console.print(Columns([result_panel, stats_panel], equal=True))

    def create_model_comparison_chart(self, model_stats: Dict[str, Any], output_path: Path) -> str:
        """Create a model comparison chart"""
        models = list(model_stats.keys())
        model_names = [m.split('/')[-1] for m in models]
        means = [stats.mean for stats in model_stats.values()]
        stds = [stats.std for stats in model_stats.values()]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Mean comparison
        colors = sns.color_palette("husl", len(models))
        bars1 = ax1.bar(model_names, means, color=colors, alpha=0.8)
        ax1.set_title('Mean Probability by Model', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Probability (%)')
        ax1.set_ylim(0, 100)

        # Add value labels on bars
        for bar, mean in zip(bars1, means):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{mean:.1f}%', ha='center', va='bottom', fontweight='bold')

        # Standard deviation comparison
        bars2 = ax2.bar(model_names, stds, color=colors, alpha=0.8)
        ax2.set_title('Standard Deviation by Model', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Standard Deviation (%)')

        for bar, std in zip(bars2, stds):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{std:.1f}%', ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        chart_path = output_path / "model_comparison.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        return str(chart_path)

    def create_probability_distribution_chart(self, responses: List[Any], output_path: Path) -> str:
        """Create probability distribution visualization"""
        valid_probs = [r.probability for r in responses if r.probability is not None]

        if not valid_probs:
            return None

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Histogram
        ax1.hist(valid_probs, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(np.mean(valid_probs), color='red', linestyle='--',
                   label=f'Mean: {np.mean(valid_probs):.1f}%')
        ax1.axvline(np.median(valid_probs), color='green', linestyle='--',
                   label=f'Median: {np.median(valid_probs):.1f}%')
        ax1.set_xlabel('Probability (%)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Distribution of Forecasts', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Box plot by model
        model_probs = {}
        for response in responses:
            if response.probability is not None:
                model = response.model.split('/')[-1]
                if model not in model_probs:
                    model_probs[model] = []
                model_probs[model].append(response.probability)

        if model_probs:
            ax2.boxplot(model_probs.values(), labels=model_probs.keys())
            ax2.set_ylabel('Probability (%)')
            ax2.set_title('Probability Range by Model', fontsize=14, fontweight='bold')
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        chart_path = output_path / "probability_distribution.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        return str(chart_path)

    def create_timeline_chart(self, responses: List[Any], output_path: Path) -> str:
        """Create timeline of responses"""
        from datetime import datetime

        timestamps = []
        probabilities = []
        models = []

        for response in responses:
            if response.probability is not None:
                try:
                    timestamp = datetime.fromisoformat(response.timestamp.replace('Z', '+00:00'))
                    timestamps.append(timestamp)
                    probabilities.append(response.probability)
                    models.append(response.model.split('/')[-1])
                except:
                    continue

        if not timestamps:
            return None

        fig, ax = plt.subplots(figsize=(15, 8))

        # Create scatter plot with different colors for each model
        unique_models = list(set(models))
        colors = sns.color_palette("husl", len(unique_models))

        for i, model in enumerate(unique_models):
            model_times = [t for t, m in zip(timestamps, models) if m == model]
            model_probs = [p for p, m in zip(probabilities, models) if m == model]

            ax.scatter(model_times, model_probs, label=model,
                      color=colors[i], s=60, alpha=0.7)

        # Add trend line
        if len(timestamps) > 1:
            # Convert timestamps to numbers for trend calculation
            time_nums = [(t - timestamps[0]).total_seconds() for t in timestamps]
            z = np.polyfit(time_nums, probabilities, 1)
            p = np.poly1d(z)
            ax.plot(timestamps, p(time_nums), "r--", alpha=0.8, linewidth=2, label='Trend')

        ax.set_xlabel('Time')
        ax.set_ylabel('Probability (%)')
        ax.set_title('Forecast Timeline', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Format x-axis
        fig.autofmt_xdate()

        plt.tight_layout()
        chart_path = output_path / "forecast_timeline.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        return str(chart_path)

    def show_completion_celebration(self, excel_path: str):
        """Show completion celebration"""
        celebration = """
        🎉✨🎉✨🎉✨🎉✨🎉✨🎉✨🎉✨🎉

               ANALYSIS COMPLETE!

        📊 Your forecast report is ready!
        📁 Location: {excel_path}

        🎉✨🎉✨🎉✨🎉✨🎉✨🎉✨🎉✨🎉
        """.format(excel_path=excel_path)

        panel = Panel(
            celebration,
            title="🏆 Success",
            border_style="green",
            padding=(1, 2)
        )

        self.console.print(panel)

# Global instance
visual = ForesightVisuals()