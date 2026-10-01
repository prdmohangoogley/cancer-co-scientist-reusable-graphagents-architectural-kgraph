"""Intent classification and worker agent delegation router."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    DRUG_REPURPOSING = "DRUG_REPURPOSING"
    PATHWAY_ANALYSIS = "PATHWAY_ANALYSIS"
    TARGET_VALIDATION = "TARGET_VALIDATION"
    CLINICAL_TRIALS = "CLINICAL_TRIALS"
    GENERAL_ONCOLOGY_QUERY = "GENERAL_ONCOLOGY_QUERY"


class RoutingDecision(BaseModel):
    """Encapsulates classified intent, extracted entities, and delegated tasks."""
    intent: IntentType
    extracted_genes: List[str] = Field(default_factory=list)
    extracted_diseases: List[str] = Field(default_factory=list)
    delegated_workers: List[str] = Field(default_factory=list)
    reasoning: str = ""


class IntentRouter:
    """Classifies user queries and routes tasks to specialized Graph Agent Workers."""

    # Common oncogenes / tumor suppressors for rapid heuristic extraction
    KNOWN_GENES = {"TP53", "EGFR", "KRAS", "BRCA1", "BRCA2", "PIK3CA", "BRAF", "MYC", "PTEN", "ERBB2", "ALK"}
    
    # Common cancer types
    KNOWN_DISEASES = {
        "lung cancer": "Non-small cell lung carcinoma",
        "nsclc": "Non-small cell lung carcinoma",
        "ovarian cancer": "Ovarian Carcinoma",
        "breast cancer": "Invasive Breast Carcinoma",
        "melanoma": "Cutaneous Melanoma",
        "colorectal cancer": "Colorectal Adenocarcinoma",
        "pancreatic cancer": "Pancreatic Ductal Adenocarcinoma",
    }

    def route_query(self, user_query: str) -> RoutingDecision:
        """Classify inquiry intent and identify target biomedical entities."""
        query_lower = user_query.lower()

        # 1. Entity Extraction
        genes: list[str] = []
        for word in re.findall(r"\b[A-Za-z0-9_-]+\b", user_query):
            upper_word = word.upper()
            if upper_word in self.KNOWN_GENES and upper_word not in genes:
                genes.append(upper_word)

        diseases: list[str] = []
        for term, canonical in self.KNOWN_DISEASES.items():
            if term in query_lower and canonical not in diseases:
                diseases.append(canonical)

        # Defaults if not matched
        if not genes:
            genes = ["EGFR"]
        if not diseases:
            diseases = ["Non-small cell lung carcinoma"]

        # 2. Intent Classification
        if any(w in query_lower for w in ["drug", "repurpose", "repurposing", "inhibitor", "therapy", "treatment"]):
            intent = IntentType.DRUG_REPURPOSING
            delegated = ["PrimeKGWorkerAgent.find_drug_repurposing_candidates"]
            reasoning = "Query focuses on therapeutic candidates and drug repurposing opportunities."
        elif any(w in query_lower for w in ["pathway", "signaling", "cascade", "mechanism", "interact"]):
            intent = IntentType.PATHWAY_ANALYSIS
            delegated = ["PrimeKGWorkerAgent.explore_gene_disease_pathways"]
            reasoning = "Query seeks biochemical signaling pathways and multi-hop interactions."
        elif any(w in query_lower for w in ["target", "vulnerability", "oncogene", "mutation", "validat"]):
            intent = IntentType.TARGET_VALIDATION
            delegated = ["PrimeKGWorkerAgent.explore_gene_disease_pathways"]
            reasoning = "Query targets oncogenic driver validation and tumor vulnerabilities."
        else:
            intent = IntentType.GENERAL_ONCOLOGY_QUERY
            delegated = ["PrimeKGWorkerAgent.explore_gene_disease_pathways"]
            reasoning = "General oncology query dispatched to standard graph traversal."

        return RoutingDecision(
            intent=intent,
            extracted_genes=genes,
            extracted_diseases=diseases,
            delegated_workers=delegated,
            reasoning=reasoning,
        )
