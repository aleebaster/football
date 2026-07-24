"""Dashboard Live Pages — page layouts for Live Engine monitoring.

Each page aggregates widgets from the Application Layer through the Presenter.
Dashboard does NOT access Live Engine directly — only through Application Layer.

Pages:
    - Live Matches: currently tracked matches
    - Workers: worker pool status
    - Heartbeat: system health heartbeat
    - Live Metrics: performance metrics
    - Recent Events: recent live events
    - Provider Health: data provider health
    - Queue Status: match processing queue
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.dashboard.widgets import Widget, WidgetFactory


class LivePage(BaseModel):
    """A live dashboard page layout."""

    title: str
    description: str = ""
    widgets: list[Widget] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LivePageFactory:
    """Creates Live Engine dashboard pages from DTOs.

    All methods receive pre-built DTOs from the Application Layer.
    Does NOT access Live Engine directly.
    """

    @staticmethod
    def live_matches_page(
        matches: list[dict[str, Any]],
        active_count: int = 0,
    ) -> LivePage:
        """Build the Live Matches page.

        Shows all currently tracked matches with their state and score.
        """
        widgets = [
            WidgetFactory.stat_widget(
                title="Active Matches",
                value=active_count,
                icon="activity",
                color="blue",
            ),
            WidgetFactory.stat_widget(
                title="Live",
                value=len(
                    [m for m in matches if m.get("state") in ("live", "half_time")]
                ),
                icon="play",
                color="green",
            ),
            WidgetFactory.stat_widget(
                title="Scheduled",
                value=len([m for m in matches if m.get("state") == "scheduled"]),
                icon="clock",
                color="yellow",
            ),
        ]

        table_rows = []
        for m in matches:
            table_rows.append(
                {
                    "Fixture": f"{m.get('home_team', '?')} vs {m.get('away_team', '?')}",
                    "Competition": m.get("competition_name", "N/A"),
                    "State": m.get("state", "unknown"),
                    "Score": f"{m.get('home_score', '-')} - {m.get('away_score', '-')}",
                    "Status": m.get("status", "N/A"),
                }
            )

        return LivePage(
            title="Live Matches",
            description="Currently tracked matches and their real-time status",
            widgets=widgets,
            tables=table_rows,
        )

    @staticmethod
    def workers_page(
        workers: list[dict[str, Any]],
    ) -> LivePage:
        """Build the Workers page.

        Shows worker pool status, processing counts, and errors.
        """
        total = len(workers)
        active = len([w for w in workers if w.get("status") == "processing"])
        idle = len([w for w in workers if w.get("status") == "idle"])
        errors = len([w for w in workers if w.get("status") == "error"])

        widgets = [
            WidgetFactory.stat_widget(
                title="Total Workers", value=total, icon="cpu", color="blue"
            ),
            WidgetFactory.stat_widget(
                title="Active", value=active, icon="play", color="green"
            ),
            WidgetFactory.stat_widget(
                title="Idle", value=idle, icon="pause", color="gray"
            ),
            WidgetFactory.stat_widget(
                title="Errors", value=errors, icon="alert-triangle", color="red"
            ),
        ]

        table_rows = []
        for w in workers:
            table_rows.append(
                {
                    "Worker ID": w.get("worker_id", "unknown"),
                    "Status": w.get("status", "unknown"),
                    "Current Fixture": w.get("current_fixture_id", "-"),
                    "Processed": w.get("processed_count", 0),
                    "Errors": w.get("error_count", 0),
                }
            )

        return LivePage(
            title="Workers",
            description="Worker pool status and utilization",
            widgets=widgets,
            tables=table_rows,
        )

    @staticmethod
    def heartbeat_page(
        heartbeat: dict[str, Any],
    ) -> LivePage:
        """Build the Heartbeat page.

        Shows scheduler health, worker health, provider health, and uptime.
        """
        scheduler_ok = heartbeat.get("scheduler_running", False)
        provider_ok = heartbeat.get("provider_healthy", False)
        workers_healthy = heartbeat.get("workers_healthy", 0)
        workers_total = heartbeat.get("workers_total", 0)

        widgets = [
            Widget(
                title="Scheduler",
                value="Running" if scheduler_ok else "Stopped",
                icon="activity",
                color="green" if scheduler_ok else "red",
            ),
            Widget(
                title="Providers",
                value="Healthy" if provider_ok else "Unhealthy",
                icon="server",
                color="green" if provider_ok else "red",
            ),
            WidgetFactory.stat_widget(
                title="Workers Healthy",
                value=f"{workers_healthy}/{workers_total}",
                icon="cpu",
                color="green" if workers_healthy == workers_total else "yellow",
            ),
            WidgetFactory.stat_widget(
                title="Uptime",
                value=f"{heartbeat.get('uptime_seconds', 0):.0f}s",
                icon="clock",
                color="blue",
            ),
        ]

        return LivePage(
            title="Heartbeat",
            description="System health heartbeat and component status",
            widgets=widgets,
        )

    @staticmethod
    def live_metrics_page(
        metrics: dict[str, Any],
    ) -> LivePage:
        """Build the Live Metrics page.

        Shows performance metrics: prediction time, signal time, provider latency.
        """
        widgets = [
            WidgetFactory.stat_widget(
                title="Active Matches",
                value=metrics.get("active_matches", 0),
                icon="activity",
                color="blue",
            ),
            WidgetFactory.stat_widget(
                title="Events Published",
                value=metrics.get("events_published", 0),
                icon="zap",
                color="purple",
            ),
            WidgetFactory.stat_widget(
                title="Avg Prediction Time",
                value=f"{metrics.get('avg_prediction_time_ms', 0):.1f}ms",
                icon="clock",
                color="green",
            ),
            WidgetFactory.stat_widget(
                title="Avg Signal Time",
                value=f"{metrics.get('avg_signal_time_ms', 0):.1f}ms",
                icon="zap",
                color="yellow",
            ),
            WidgetFactory.stat_widget(
                title="Provider Latency",
                value=f"{metrics.get('provider_latency_ms', 0):.1f}ms",
                icon="server",
                color="orange",
            ),
            WidgetFactory.stat_widget(
                title="Uptime",
                value=f"{metrics.get('uptime_seconds', 0):.0f}s",
                icon="clock",
                color="blue",
            ),
        ]

        return LivePage(
            title="Live Metrics",
            description="Real-time performance metrics for the Live Engine",
            widgets=widgets,
        )

    @staticmethod
    def recent_events_page(
        events: list[dict[str, Any]],
    ) -> LivePage:
        """Build the Recent Events page.

        Shows recent live events with type, fixture, and correlation ID.
        """
        widgets = [
            WidgetFactory.stat_widget(
                title="Total Events",
                value=len(events),
                icon="list",
                color="blue",
            ),
            WidgetFactory.stat_widget(
                title="Event Types",
                value=len({e.get("event_type", "") for e in events}),
                icon="tag",
                color="purple",
            ),
        ]

        table_rows = []
        for e in events:
            table_rows.append(
                {
                    "Event ID": e.get("event_id", "")[:12],
                    "Type": e.get("event_type", "unknown"),
                    "Fixture": e.get("fixture_id", 0),
                    "Correlation": e.get("correlation_id", "-") or "-",
                    "Worker": e.get("worker_id", "-") or "-",
                    "Timestamp": str(e.get("timestamp", "")),
                }
            )

        return LivePage(
            title="Recent Events",
            description="Recent events published by the Live Engine",
            widgets=widgets,
            tables=table_rows,
        )

    @staticmethod
    def provider_health_page(
        providers: list[dict[str, Any]],
    ) -> LivePage:
        """Build the Provider Health page.

        Shows provider status, success rates, and response times.
        """
        healthy = len([p for p in providers if p.get("status") == "healthy"])
        total = len(providers)

        widgets = [
            WidgetFactory.stat_widget(
                title="Providers Healthy",
                value=f"{healthy}/{total}",
                icon="server",
                color="green" if healthy == total else "yellow",
            ),
        ]

        table_rows = []
        for p in providers:
            table_rows.append(
                {
                    "Provider": p.get("name", "unknown"),
                    "Status": p.get("status", "unknown"),
                    "Success Rate": f"{p.get('success_rate', 0):.1f}%",
                    "Avg Response": f"{p.get('avg_response_ms', 0):.0f}ms",
                    "Requests": p.get("total_requests", 0),
                    "Failures": p.get("consecutive_failures", 0),
                }
            )

        return LivePage(
            title="Provider Health",
            description="Data provider health status and performance",
            widgets=widgets,
            tables=table_rows,
        )

    @staticmethod
    def queue_status_page(
        queue_stats: dict[str, Any],
    ) -> LivePage:
        """Build the Queue Status page.

        Shows queue size, priority queue, and processed count.
        """
        widgets = [
            WidgetFactory.stat_widget(
                title="Queue Size",
                value=queue_stats.get("total", 0),
                icon="list",
                color="blue",
            ),
            WidgetFactory.stat_widget(
                title="Priority Queue",
                value=queue_stats.get("priority", 0),
                icon="alert-circle",
                color="orange",
            ),
            WidgetFactory.stat_widget(
                title="Normal Queue",
                value=queue_stats.get("normal", 0),
                icon="list",
                color="gray",
            ),
            WidgetFactory.stat_widget(
                title="Processed",
                value=queue_stats.get("processed", 0),
                icon="check-circle",
                color="green",
            ),
        ]

        return LivePage(
            title="Queue Status",
            description="Match processing queue status and statistics",
            widgets=widgets,
        )
