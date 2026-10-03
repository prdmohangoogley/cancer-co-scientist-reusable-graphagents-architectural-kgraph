"""Vertex AI Reasoning Engine / Gemini Enterprise Agent (GEA) Runtime Adapter.

Conforms to:
- DOC-01: AI Agent Quality Engineering & Observability
- DOC-02: Zero Ambient Authority (ZAA) task-level scoping
- DOC-03: Open AI Agent Protocol Stack & A2UI Declarative Interfaces
- DOC-08: Context Engineering & Progressive Disclosure via Memory Bank
- DOC-09: Platform-Native State Management (Vertex AI Agent Engine)

Allows deploying the Cancer Co-Scientist Agent directly into Vertex AI Agent Builder
as a google.cloud.aiplatform.ReasoningEngine resource while preserving 100% of the
existing web application and local agent loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from .auth import UserProfile
from .orchestrator import CancerCoScientistOrchestrator

logger = logging.getLogger("reasoning_engine")


class CancerCoScientistReasoningEngine:
    """Vertex AI Reasoning Engine implementation for Gemini Enterprise Agents (GEA).
    
    Provides a standardized interface for Vertex AI Agent Builder, Agent Engine,
    and GCP Console Playground while invoking the exact same Orchestrator, Memory Bank,
    and 15-algorithm Graph Engine.
    """

    def __init__(self, model_name: str = "gemini-1.5-pro") -> None:
        self.model_name = model_name
        self.orchestrator: Optional[CancerCoScientistOrchestrator] = None

    def set_up(self) -> None:
        """Initialize the agent within Vertex AI Agent Engine."""
        logger.info(f"Initializing CancerCoScientistReasoningEngine with model {self.model_name}")
        self.orchestrator = CancerCoScientistOrchestrator(use_mock=False)

    def query(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: str = "gea_clinician",
        tenant_id: str = "mskcc_oncology",
    ) -> Dict[str, Any]:
        """Main entry point for Gemini Enterprise Agents & Vertex AI Playground.
        
        Args:
            query: The natural-language precision oncology clinical inquiry.
            session_id: Optional conversational session ID for multi-turn state.
            user_id: Authenticated user ID (scoped under ZAA).
            tenant_id: Medical center or hospital tenant domain.
            
        Returns:
            Declarative A2UI surface payload and reasoning trajectory metadata.
        """
        if not self.orchestrator:
            self.set_up()

        user_profile = UserProfile(
            user_id=user_id,
            email=f"{user_id}@cancercenter.org",
            full_name="Dr. Attending Oncologist (GEA)",
            roles=["clinician"],
            tenant_id=tenant_id,
        )

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(
                self.orchestrator.process_clinical_inquiry(
                    query=query,
                    session_id=session_id,
                    user_profile=user_profile,
                )
            )
        else:
            return loop.run_until_complete(
                self.orchestrator.process_clinical_inquiry(
                    query=query,
                    session_id=session_id,
                    user_profile=user_profile,
                )
            )

    def explore_primekg(self, focal_entity: str = "EGFR", depth: int = 2) -> Dict[str, Any]:
        """GEA tool to explore the Cloud Spanner PrimeKG property graph neighborhood."""
        if not self.orchestrator:
            self.set_up()
        return self.orchestrator.get_primekg_exploration_payload(focal_entity=focal_entity, depth=depth)

    def get_telemetry(self) -> Dict[str, Any]:
        """GEA tool to retrieve live system latency percentiles and token economics."""
        if not self.orchestrator:
            self.set_up()
        sessions = self.orchestrator.memory_bank.list_sessions()
        total_msgs = sum(len(self.orchestrator.memory_bank.get_session_history(s.session_id, limit=1000)) for s in sessions)
        return self.orchestrator.telemetry.get_stats(
            active_sessions=len(sessions),
            total_messages=total_msgs,
        )
