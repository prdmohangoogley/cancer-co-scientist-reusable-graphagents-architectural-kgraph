"""Enterprise Memory Bank and Session Persistence Engine (PAT-MEM-BANK / DOC-08 / DOC-09).

Mitigates catastrophic forgetting, session drift, and unbounded context growth through:
1. Multi-turn session persistence in Cloud Spanner (`chat_sessions`, `chat_messages`).
2. Factual clinical entity & hypothesis consolidation (`memory_bank_entities`, `memory_bank_hypotheses`).
3. Progressive disclosure & semantic recall retrieving only relevant past entities for current inquiries.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("memory_bank")


# =============================================================================
# Pydantic State & Memory Models
# =============================================================================

class ChatSession(BaseModel):
    """Conversational session metadata matching Cloud Spanner schema."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str = "New Clinical Session"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """Individual conversational turn matching Cloud Spanner schema."""
    session_id: str
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # "user", "assistant", "system"
    content_text: str
    a2ui_payload_json: Optional[Dict[str, Any]] = None
    token_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryEntity(BaseModel):
    """Consolidated clinical entity stored in Memory Bank (DOC-08)."""
    entity_id: str = Field(default_factory=lambda: f"ent_{uuid.uuid4().hex[:10]}")
    session_id: str
    entity_name: str
    entity_type: str  # "mutation", "biomarker", "drug", "gene", "disease"
    confidence: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryHypothesis(BaseModel):
    """Formulated precision oncology hypothesis stored in Memory Bank (DOC-08)."""
    hypothesis_id: str = Field(default_factory=lambda: f"hyp_{uuid.uuid4().hex[:10]}")
    session_id: str
    statement: str
    evidence_level: str = "Level_B"  # Level_A, Level_B, Level_C
    status: str = "formulated"  # "formulated", "validated", "refuted", "investigating"
    confidence: float = 0.85
    evidence_nodes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# Memory Bank Engine (PAT-MEM-BANK)
# =============================================================================

class MemoryBankEngine:
    """Manages chat sessions, turns, factual entity consolidation, and progressive recall."""

    # Lexicon for precision oncology entity identification
    KNOWN_GENES: Set[str] = {
        "EGFR", "TP53", "KRAS", "NRAS", "HRAS", "BRCA1", "BRCA2", "PIK3CA",
        "BRAF", "MYC", "PTEN", "ERBB2", "ALK", "MET", "ROS1", "RET",
        "NTRK1", "NTRK2", "NTRK3", "CDK4", "CDK6", "RB1", "APC", "ATM", "ATR",
        "FGFR1", "FGFR2", "FGFR3", "SMAD4", "VHL", "IDH1", "IDH2",
    }

    KNOWN_DRUGS: Set[str] = {
        "osimertinib", "gefitinib", "erlotinib", "afatinib", "dacomitinib",
        "mobocertinib", "amivantamab", "sotorasib", "adagrasib", "crizotinib",
        "alectinib", "brigatinib", "lorlatinib", "ceritinib", "dabrafenib",
        "trametinib", "vemurafenib", "encorafenib", "cobimetinib", "selumetinib",
        "imatinib", "dasatinib", "nilotinib", "bosutinib", "ponatinib",
        "trastuzumab", "pertuzumab", "t-dm1", "enhertu", "olaparib", "rucaparib",
        "niraparib", "talazoparib", "capivasertib", "alpelisib", "everolimus",
        "temsirolimus", "palbociclib", "ribociclib", "abemaciclib",
        "pembrolizumab", "nivolumab", "atezolizumab", "durvalumab", "ipilimumab",
    }

    KNOWN_DISEASES: Dict[str, str] = {
        "lung cancer": "Non-small cell lung carcinoma",
        "nsclc": "Non-small cell lung carcinoma",
        "sclc": "Small cell lung cancer",
        "ovarian cancer": "Ovarian Carcinoma",
        "breast cancer": "Invasive Breast Carcinoma",
        "melanoma": "Cutaneous Melanoma",
        "colorectal cancer": "Colorectal Adenocarcinoma",
        "pancreatic cancer": "Pancreatic Ductal Adenocarcinoma",
        "glioblastoma": "Glioblastoma Multiforme",
        "prostate cancer": "Prostate Adenocarcinoma",
        "aml": "Acute Myeloid Leukemia",
    }

    KNOWN_BIOMARKERS: Set[str] = {
        "pd-l1", "msi-h", "msi-l", "mss", "tmb-h", "tmb", "her2", "her2+",
        "er+", "pr+", "hr+", "dmmr", "pmmr", "brca-mutated", "ntrk fusion",
        "fgfr alteration", "met amplification", "alk fusion",
    }

    # Hypothesis indicator trigger phrases
    HYPOTHESIS_TRIGGERS: List[str] = [
        "synthetic lethality", "overcomes resistance", "confers resistance",
        "sensitizes", "synergistic", "biomarker of response", "therapeutic vulnerability",
        "hypothesize", "suggests that", "candidate target", "inhibits", "activates",
    ]

    def __init__(
        self,
        project_id: str = "fivedaysai-prd-sandbox-317383",
        instance_id: str = "primekg-instance-dev",
        database_id: str = "primekg-database",
        use_mock: bool = True,
    ) -> None:
        self.project_id = project_id
        self.instance_id = instance_id
        self.database_id = database_id
        self.use_mock = use_mock
        self._database = None

        # In-memory session and memory store (guaranteed availability & mock support)
        self._sessions: Dict[str, ChatSession] = {}
        self._messages: Dict[str, List[ChatMessage]] = {}
        self._entities: Dict[str, List[MemoryEntity]] = {}
        self._hypotheses: Dict[str, List[MemoryHypothesis]] = {}

    def _get_database(self) -> Any:
        """Lazy-initialize Cloud Spanner database handle if not in mock mode."""
        if self._database is None and not self.use_mock:
            try:
                from google.cloud import spanner
                client = spanner.Client(project=self.project_id)
                instance = client.instance(self.instance_id)
                self._database = instance.database(self.database_id)
            except Exception as e:
                logger.warning(f"Could not connect to Cloud Spanner: {e}. Defaulting to in-memory store.")
                self.use_mock = True
        return self._database

    # =========================================================================
    # Session Management
    # =========================================================================

    def create_session(
        self,
        user_id: str,
        title: str = "New Clinical Session",
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatSession:
        """Create and persist a new ChatSession."""
        sid = session_id or str(uuid.uuid4())
        session = ChatSession(
            session_id=sid,
            user_id=user_id,
            title=title,
            metadata_json=metadata or {},
        )
        self._sessions[sid] = session
        self._messages.setdefault(sid, [])
        self._entities.setdefault(sid, [])
        self._hypotheses.setdefault(sid, [])

        db = self._get_database()
        if db and not self.use_mock:
            try:
                def _insert_session(transaction: Any) -> None:
                    transaction.insert(
                        "chat_sessions",
                        columns=["session_id", "user_id", "title", "metadata_json"],
                        values=[[session.session_id, session.user_id, session.title, json.dumps(session.metadata_json)]],
                    )
                db.run_in_transaction(_insert_session)
            except Exception as e:
                logger.warning(f"Failed to persist session to Spanner: {e}")

        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Retrieve ChatSession by session_id."""
        return self._sessions.get(session_id)

    def list_sessions(self, user_id: Optional[str] = None) -> List[ChatSession]:
        """List all chat sessions, optionally filtered by user_id."""
        sessions = list(self._sessions.values())
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        return sorted(sessions, key=lambda s: s.last_active_at, reverse=True)

    # =========================================================================
    # Message Persistence
    # =========================================================================

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        a2ui_payload: Optional[Dict[str, Any]] = None,
        token_count: int = 0,
    ) -> ChatMessage:
        """Persist a conversation turn into the session."""
        now = datetime.now(timezone.utc)

        # Ensure session exists
        if session_id not in self._sessions:
            self.create_session(user_id="default_user", title="Auto-created Session", session_id=session_id)

        session = self._sessions[session_id]
        session.last_active_at = now

        # Update title if user turn and session has default title
        if role == "user" and session.title in ("New Clinical Session", "Auto-created Session"):
            clean_title = content.strip().replace("\n", " ")[:60]
            if clean_title:
                session.title = clean_title

        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content_text=content,
            a2ui_payload_json=a2ui_payload,
            token_count=token_count,
            created_at=now,
        )
        self._messages.setdefault(session_id, []).append(msg)

        db = self._get_database()
        if db and not self.use_mock:
            try:
                def _insert_message(transaction: Any) -> None:
                    transaction.insert(
                        "chat_messages",
                        columns=["session_id", "message_id", "role", "content_text", "a2ui_payload_json", "token_count"],
                        values=[[
                            msg.session_id,
                            msg.message_id,
                            msg.role,
                            msg.content_text,
                            json.dumps(msg.a2ui_payload_json) if msg.a2ui_payload_json else None,
                            msg.token_count,
                        ]],
                    )
                db.run_in_transaction(_insert_message)
            except Exception as e:
                logger.warning(f"Failed to persist chat message to Spanner: {e}")

        return msg

    def get_session_history(self, session_id: str, limit: int = 20) -> List[ChatMessage]:
        """Retrieve recent conversation history for the session."""
        msgs = self._messages.get(session_id, [])
        return msgs[-limit:]

    # =========================================================================
    # Clinical Entity & Hypothesis Extraction & Consolidation
    # =========================================================================

    def extract_and_consolidate(
        self,
        session_id: str,
        user_query: str,
        agent_response: str,
    ) -> Tuple[List[MemoryEntity], List[MemoryHypothesis]]:
        """Extract precision oncology entities and hypotheses from the turn and consolidate to Memory Bank."""
        combined_text = f"{user_query}\n{agent_response}"
        text_lower = combined_text.lower()

        new_entities: List[MemoryEntity] = []
        new_hypotheses: List[MemoryHypothesis] = []

        existing_entity_keys = {
            (e.entity_name.lower(), e.entity_type)
            for e in self._entities.get(session_id, [])
        }

        # 1. Extract Specific Mutations (e.g., EGFR T790M, KRAS G12C, BRAF V600E, exon 20 insertion)
        mutation_patterns = [
            # Gene + amino acid change (e.g., EGFR T790M, KRAS G12C, TP53 R273H, PIK3CA E545K)
            r"\b([A-Z0-9]{2,8})\s+([A-Z]\d{1,4}[A-Z])\b",
            # Standalone mutation notation (e.g., T790M, L858R, G12C, V600E)
            r"\b([A-Z]\d{2,4}[A-Z])\b",
            # Exon alterations (e.g. EGFR exon 20 insertion, MET exon 14 skipping)
            r"\b([A-Z0-9]{2,8})\s+(exon\s+\d+\s+(?:insertion|deletion|skipping))\b",
        ]

        # Extract Gene + Mutation
        for match in re.finditer(mutation_patterns[0], combined_text):
            gene, mut = match.group(1).upper(), match.group(2).upper()
            if gene in self.KNOWN_GENES:
                full_mut_name = f"{gene} {mut}"
                if (full_mut_name.lower(), "mutation") not in existing_entity_keys:
                    ent = MemoryEntity(
                        session_id=session_id,
                        entity_name=full_mut_name,
                        entity_type="mutation",
                        confidence=0.98,
                        properties={"gene": gene, "alteration": mut},
                    )
                    new_entities.append(ent)
                    existing_entity_keys.add((full_mut_name.lower(), "mutation"))

        # Extract Exon Alterations
        for match in re.finditer(mutation_patterns[2], combined_text, re.IGNORECASE):
            gene, alteration = match.group(1).upper(), match.group(2).lower()
            if gene in self.KNOWN_GENES:
                full_name = f"{gene} {alteration}"
                if (full_name.lower(), "mutation") not in existing_entity_keys:
                    ent = MemoryEntity(
                        session_id=session_id,
                        entity_name=full_name,
                        entity_type="mutation",
                        confidence=0.95,
                        properties={"gene": gene, "alteration": alteration},
                    )
                    new_entities.append(ent)
                    existing_entity_keys.add((full_name.lower(), "mutation"))

        # 2. Extract Genes
        for word in re.findall(r"\b[A-Z0-9_-]+\b", combined_text):
            upper_word = word.upper()
            if upper_word in self.KNOWN_GENES:
                if (upper_word.lower(), "gene") not in existing_entity_keys:
                    ent = MemoryEntity(
                        session_id=session_id,
                        entity_name=upper_word,
                        entity_type="gene",
                        confidence=0.99,
                        properties={"symbol": upper_word},
                    )
                    new_entities.append(ent)
                    existing_entity_keys.add((upper_word.lower(), "gene"))

        # 3. Extract Drugs / Inhibitors
        for drug in self.KNOWN_DRUGS:
            if re.search(r"\b" + re.escape(drug) + r"\b", text_lower):
                canonical_drug = drug.capitalize()
                if (canonical_drug.lower(), "drug") not in existing_entity_keys:
                    ent = MemoryEntity(
                        session_id=session_id,
                        entity_name=canonical_drug,
                        entity_type="drug",
                        confidence=0.96,
                        properties={"class": "Targeted Inhibitor"},
                    )
                    new_entities.append(ent)
                    existing_entity_keys.add((canonical_drug.lower(), "drug"))

        # 4. Extract Diseases
        for term, canonical in self.KNOWN_DISEASES.items():
            if term in text_lower:
                if (canonical.lower(), "disease") not in existing_entity_keys:
                    ent = MemoryEntity(
                        session_id=session_id,
                        entity_name=canonical,
                        entity_type="disease",
                        confidence=0.97,
                        properties={"term_matched": term},
                    )
                    new_entities.append(ent)
                    existing_entity_keys.add((canonical.lower(), "disease"))

        # 5. Extract Biomarkers
        for bm in self.KNOWN_BIOMARKERS:
            if bm in text_lower:
                bm_name = bm.upper()
                if (bm_name.lower(), "biomarker") not in existing_entity_keys:
                    ent = MemoryEntity(
                        session_id=session_id,
                        entity_name=bm_name,
                        entity_type="biomarker",
                        confidence=0.92,
                        properties={"biomarker": bm_name},
                    )
                    new_entities.append(ent)
                    existing_entity_keys.add((bm_name.lower(), "biomarker"))

        # 6. Extract Clinical Hypotheses
        sentences = re.split(r"(?<=[.!?])\s+", combined_text)
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if len(sentence_clean) < 20:
                continue
            s_lower = sentence_clean.lower()

            # Check if sentence contains hypothesis triggers and at least one known entity
            has_trigger = any(trigger in s_lower for trigger in self.HYPOTHESIS_TRIGGERS)
            if has_trigger:
                ev_nodes: List[str] = []
                for g in self.KNOWN_GENES:
                    if g in sentence_clean:
                        ev_nodes.append(g)
                for d in self.KNOWN_DRUGS:
                    if d in s_lower:
                        ev_nodes.append(d.capitalize())

                if ev_nodes:
                    existing_stmts = {h.statement for h in self._hypotheses.get(session_id, [])}
                    if sentence_clean not in existing_stmts:
                        hyp = MemoryHypothesis(
                            session_id=session_id,
                            statement=sentence_clean,
                            evidence_level="Level_B",
                            status="formulated",
                            confidence=0.88,
                            evidence_nodes=ev_nodes,
                        )
                        new_hypotheses.append(hyp)

        # Consolidate into session store
        self._entities.setdefault(session_id, []).extend(new_entities)
        self._hypotheses.setdefault(session_id, []).extend(new_hypotheses)

        # Cloud Spanner Persistence
        db = self._get_database()
        if db and not self.use_mock:
            try:
                def _insert_memory(transaction: Any) -> None:
                    if new_entities:
                        transaction.insert_or_update(
                            "memory_bank_entities",
                            columns=["entity_id", "session_id", "entity_type", "entity_name", "confidence", "attributes_json"],
                            values=[[e.entity_id, e.session_id, e.entity_type, e.entity_name, e.confidence, json.dumps(e.properties)] for e in new_entities],
                        )
                    if new_hypotheses:
                        transaction.insert_or_update(
                            "memory_bank_hypotheses",
                            columns=["hypothesis_id", "session_id", "statement", "evidence_level", "status"],
                            values=[[h.hypothesis_id, h.session_id, h.statement, h.evidence_level, h.status] for h in new_hypotheses],
                        )
                db.run_in_transaction(_insert_memory)
            except Exception as e:
                logger.warning(f"Failed to persist memory entities to Spanner: {e}")

        logger.info(
            f"MemoryBank consolidated for session {session_id}: "
            f"+{len(new_entities)} entities, +{len(new_hypotheses)} hypotheses."
        )
        return new_entities, new_hypotheses

    # =========================================================================
    # Progressive Semantic Recall (DOC-08)
    # =========================================================================

    def semantic_recall(
        self,
        session_id: str,
        current_query: str,
        top_k: int = 5,
    ) -> List[MemoryEntity]:
        """Retrieve relevant past entities from Memory Bank for the query via progressive disclosure."""
        session_entities = self._entities.get(session_id, [])
        if not session_entities:
            return []

        query_lower = current_query.lower()
        query_words = set(re.findall(r"\b[a-z0-9_-]+\b", query_lower))

        scored_entities: List[Tuple[float, MemoryEntity]] = []

        for ent in session_entities:
            name_lower = ent.entity_name.lower()
            ent_words = set(re.findall(r"\b[a-z0-9_-]+\b", name_lower))

            score = 0.0

            # 1. Exact match in query
            if name_lower in query_lower:
                score += 10.0

            # 2. Token overlap between query and entity name
            overlap = query_words.intersection(ent_words)
            score += len(overlap) * 3.0

            # 3. Association boost if entity has matching gene/property
            if ent.properties:
                for prop_val in ent.properties.values():
                    if isinstance(prop_val, str) and prop_val.lower() in query_lower:
                        score += 2.5

            # 4. Confidence weighting
            score *= ent.confidence

            scored_entities.append((score, ent))

        # Sort by score descending; if score > 0, prioritize relevant ones
        scored_entities.sort(key=lambda x: x[0], reverse=True)

        # If any entities scored > 0, return top matching entities
        matched = [e for score, e in scored_entities if score > 0.0]
        if matched:
            return matched[:top_k]

        # Progressive fallback: return the most recently added entities up to top_k
        return sorted(session_entities, key=lambda e: e.updated_at, reverse=True)[:top_k]

    def get_session_memory(self, session_id: str) -> Dict[str, Any]:
        """Return all consolidated entities and hypotheses for the session."""
        entities = self._entities.get(session_id, [])
        hypotheses = self._hypotheses.get(session_id, [])
        return {
            "session_id": session_id,
            "entities": [e.model_dump() for e in entities],
            "hypotheses": [h.model_dump() for h in hypotheses],
            "entity_count": len(entities),
            "hypothesis_count": len(hypotheses),
        }
