"""PrimeKG Ingestion Pipeline for Cloud Spanner Graph (ISO GQL) and BigQuery Analytics.

Adheres to Enterprise Agent Architectural Guidelines:
- DOC-09: Platform-Native State Management (Cloud Spanner Graph + BigQuery)
- DOC-02: Zero Ambient Authority (ZAA) with fine-grained credential scoping
- DOC-01: Quality Engineering & Observability
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Tuple

logger = logging.getLogger("primekg_loader")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@dataclass
class IngestionStats:
    """Summary metrics of a knowledge graph ingestion run."""

    total_records_read: int = 0
    unique_nodes_staged: int = 0
    edges_staged: int = 0
    batches_committed: int = 0
    duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def throughput_triples_sec(self) -> float:
        if self.duration_seconds <= 0:
            return 0.0
        return round(self.total_records_read / self.duration_seconds, 2)


class PrimeKGLoader:
    """High-throughput streaming loader for PrimeKG into Cloud Spanner Graph and BigQuery."""

    # Node label mapping from raw PrimeKG x_type / y_type to Spanner Graph Node Labels
    NODE_TYPE_MAP: dict[str, str] = {
        "gene/protein": "Gene",
        "disease": "Disease",
        "drug": "Drug",
        "pathway": "Pathway",
        "anatomy": "Anatomy",
        "biological_process": "BiologicalProcess",
        "molecular_function": "MolecularFunction",
        "cellular_component": "CellularComponent",
        "effect/phenotype": "EffectPhenotype",
        "exposure": "Exposure",
    }

    # Relationship mapping to Spanner Graph Edge Labels
    RELATION_MAP: dict[str, str] = {
        "drug_protein": "TARGETS",
        "indication": "INDICATION",
        "contraindication": "CONTRAINDICATION",
        "off-label use": "OFF_LABEL_USE",
        "disease_protein": "ASSOCIATED_WITH",
        "protein_protein": "INTERACTS_WITH",
        "pathway_protein": "PART_OF_PATHWAY",
        "anatomy_protein_present": "EXPRESSED_IN",
        "disease_phenotype_positive": "MANIFESTS_AS",
    }

    def __init__(
        self,
        project_id: str = "fivedaysai-prd-sandbox-317383",
        spanner_instance_id: str = "primekg-instance-dev",
        spanner_database_id: str = "primekg-database",
        bq_dataset_id: str = "primekg_analytics_dev",
        use_mock: bool = False,
    ) -> None:
        self.project_id = project_id
        self.spanner_instance_id = spanner_instance_id
        self.spanner_database_id = spanner_database_id
        self.bq_dataset_id = bq_dataset_id
        self.use_mock = use_mock
        self._seen_node_ids: set[str] = set()

    def normalize_node_label(self, raw_type: str) -> str:
        """Map raw PrimeKG entity type to canonical Spanner Graph label."""
        clean = raw_type.strip().lower()
        return self.NODE_TYPE_MAP.get(clean, "Entity")

    def normalize_relation(self, raw_relation: str) -> str:
        """Map raw PrimeKG relation to canonical Spanner Graph edge label."""
        clean = raw_relation.strip().lower()
        return self.RELATION_MAP.get(clean, clean.upper().replace(" ", "_"))

    def build_canonical_id(self, entity_type: str, entity_id: str, source: str) -> str:
        """Construct deterministic, collision-free canonical node identifier."""
        clean_id = str(entity_id).strip()
        clean_src = str(source).strip().upper()
        return f"{clean_src}:{clean_id}"

    def stream_kg_triples(
        self,
        csv_file_path: Path,
        limit: int | None = None,
    ) -> Iterator[Tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
        """Stream normalized (source_node, target_node, edge) triples from kg.csv.

        Memory-efficient: processes row by row without reading the full file.
        """
        if not csv_file_path.exists():
            raise FileNotFoundError(f"PrimeKG file not found at: {csv_file_path}")

        records_count = 0
        with open(csv_file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                x_id = row.get("x_id", "").strip()
                y_id = row.get("y_id", "").strip()
                if not x_id or not y_id:
                    continue

                x_source = row.get("x_source", "NCBI")
                y_source = row.get("y_source", "NCBI")
                source_node_id = self.build_canonical_id(row.get("x_type", ""), x_id, x_source)
                target_node_id = self.build_canonical_id(row.get("y_type", ""), y_id, y_source)

                source_node = {
                    "node_id": source_node_id,
                    "label": self.normalize_node_label(row.get("x_type", "")),
                    "name": row.get("x_name", ""),
                    "properties_json": json.dumps({
                        "raw_id": x_id,
                        "source": x_source,
                        "raw_type": row.get("x_type", ""),
                    }),
                }

                target_node = {
                    "node_id": target_node_id,
                    "label": self.normalize_node_label(row.get("y_type", "")),
                    "name": row.get("y_name", ""),
                    "properties_json": json.dumps({
                        "raw_id": y_id,
                        "source": y_source,
                        "raw_type": row.get("y_type", ""),
                    }),
                }

                rel = self.normalize_relation(row.get("relation", ""))
                edge_id = f"{source_node_id}->{rel}->{target_node_id}"
                edge = {
                    "edge_id": edge_id,
                    "source_id": source_node_id,
                    "target_id": target_node_id,
                    "relationship": rel,
                    "confidence": 1.0,
                    "evidence_json": json.dumps({
                        "display_relation": row.get("display_relation", ""),
                        "raw_relation": row.get("relation", ""),
                    }),
                }

                yield source_node, target_node, edge
                records_count += 1
                if limit and records_count >= limit:
                    break

    def ingest_to_spanner(
        self,
        kg_csv_path: Path,
        batch_size: int = 1000,
        limit: int | None = None,
        dry_run: bool = False,
    ) -> IngestionStats:
        """Stream and commit batches of nodes and edges into Cloud Spanner Graph."""
        stats = IngestionStats()
        start_time = time.time()
        logger.info(
            f"Starting Spanner Graph ingestion from {kg_csv_path} (limit={limit}, batch_size={batch_size}, dry_run={dry_run})"
        )

        spanner_database = None
        if not dry_run and not self.use_mock:
            from google.cloud import spanner

            client = spanner.Client(project=self.project_id)
            instance = client.instance(self.spanner_instance_id)
            spanner_database = instance.database(self.spanner_database_id)
            logger.info(f"Connected to Cloud Spanner: {self.spanner_instance_id}/{self.spanner_database_id}")

        node_batch: list[dict[str, Any]] = []
        edge_batch: list[dict[str, Any]] = []

        def flush_batch() -> None:
            if not node_batch and not edge_batch:
                return

            if dry_run or self.use_mock:
                stats.batches_committed += 1
                stats.unique_nodes_staged += len(node_batch)
                stats.edges_staged += len(edge_batch)
                node_batch.clear()
                edge_batch.clear()
                return

            try:
                with spanner_database.batch() as batch:
                    if node_batch:
                        batch.insert_or_update(
                            table="Nodes",
                            columns=["node_id", "label", "name", "properties_json", "created_at"],
                            values=[
                                (
                                    n["node_id"],
                                    n["label"],
                                    n["name"],
                                    n["properties_json"],
                                    spanner.COMMIT_TIMESTAMP,
                                )
                                for n in node_batch
                            ],
                        )
                    if edge_batch:
                        batch.insert_or_update(
                            table="Edges",
                            columns=[
                                "source_id",
                                "target_id",
                                "edge_id",
                                "relationship",
                                "confidence",
                                "evidence_json",
                                "created_at",
                            ],
                            values=[
                                (
                                    e["source_id"],
                                    e["target_id"],
                                    e["edge_id"],
                                    e["relationship"],
                                    e["confidence"],
                                    e["evidence_json"],
                                    spanner.COMMIT_TIMESTAMP,
                                )
                                for e in edge_batch
                            ],
                        )

                stats.batches_committed += 1
                stats.unique_nodes_staged += len(node_batch)
                stats.edges_staged += len(edge_batch)
            except Exception as e:
                logger.error(f"Error committing batch to Spanner: {e}")
                stats.errors.append(str(e))
            finally:
                node_batch.clear()
                edge_batch.clear()

        for source_node, target_node, edge in self.stream_kg_triples(kg_csv_path, limit=limit):
            stats.total_records_read += 1

            if source_node["node_id"] not in self._seen_node_ids:
                self._seen_node_ids.add(source_node["node_id"])
                node_batch.append(source_node)

            if target_node["node_id"] not in self._seen_node_ids:
                self._seen_node_ids.add(target_node["node_id"])
                node_batch.append(target_node)

            edge_batch.append(edge)

            if len(node_batch) + len(edge_batch) >= batch_size:
                flush_batch()
                if stats.batches_committed % 10 == 0:
                    logger.info(
                        f"Progress: {stats.total_records_read} records processed ({stats.unique_nodes_staged} nodes, {stats.edges_staged} edges committed)"
                    )

        # Flush trailing records
        flush_batch()
        stats.duration_seconds = round(time.time() - start_time, 2)
        logger.info(
            f"Ingestion completed in {stats.duration_seconds}s. Total read: {stats.total_records_read}, "
            f"Unique nodes: {stats.unique_nodes_staged}, Edges: {stats.edges_staged}, "
            f"Throughput: {stats.throughput_triples_sec} triples/s"
        )
        return stats

    def ingest_features_to_bigquery(
        self,
        staging_dir: Path,
        dry_run: bool = False,
    ) -> dict[str, int]:
        """Ingest disease_features and drug_features into BigQuery tables."""
        counts = {"disease_features": 0, "drug_features": 0}
        if dry_run or self.use_mock:
            logger.info("Dry-run / mock mode: BigQuery ingestion skipped.")
            return {"disease_features": 100, "drug_features": 100}

        from google.cloud import bigquery

        bq_client = bigquery.Client(project=self.project_id)
        timestamp_now = datetime.now(timezone.utc).isoformat()

        # Ingest disease_features.tab
        disease_file = staging_dir / "disease_features.tab"
        if disease_file.exists():
            table_ref = f"{self.project_id}.{self.bq_dataset_id}.disease_features"
            rows_to_insert = []
            with open(disease_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    rows_to_insert.append({
                        "disease_id": row.get("node_id", row.get("mondo_id", "")),
                        "disease_name": row.get("node_name", ""),
                        "mondo_id": row.get("mondo_id", None),
                        "umls_cui": row.get("umls_cui", None),
                        "phenotypic_features": row.get("phenotypic_features", None),
                        "clinical_description": row.get("description", None),
                        "updated_at": timestamp_now,
                    })
                    if len(rows_to_insert) >= 500:
                        errors = bq_client.insert_rows_json(table_ref, rows_to_insert)
                        if errors:
                            logger.error(f"BQ insert errors for disease_features: {errors[:2]}")
                        counts["disease_features"] += len(rows_to_insert)
                        rows_to_insert.clear()

            if rows_to_insert:
                bq_client.insert_rows_json(table_ref, rows_to_insert)
                counts["disease_features"] += len(rows_to_insert)
            logger.info(f"Ingested {counts['disease_features']} rows into BigQuery {table_ref}")

        # Ingest drug_features.tab
        drug_file = staging_dir / "drug_features.tab"
        if drug_file.exists():
            table_ref = f"{self.project_id}.{self.bq_dataset_id}.drug_features"
            rows_to_insert = []
            with open(drug_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    mw_val = None
                    try:
                        mw_str = row.get("molecular_weight", "")
                        if mw_str:
                            mw_val = float(mw_str)
                    except ValueError:
                        pass

                    rows_to_insert.append({
                        "drug_id": row.get("node_id", row.get("drugbank_id", "")),
                        "drug_name": row.get("node_name", ""),
                        "indication": row.get("indication", None),
                        "pharmacodynamics": row.get("pharmacodynamics", None),
                        "smiles": row.get("smiles", None),
                        "molecular_weight": mw_val,
                        "updated_at": timestamp_now,
                    })
                    if len(rows_to_insert) >= 500:
                        errors = bq_client.insert_rows_json(table_ref, rows_to_insert)
                        if errors:
                            logger.error(f"BQ insert errors for drug_features: {errors[:2]}")
                        counts["drug_features"] += len(rows_to_insert)
                        rows_to_insert.clear()

            if rows_to_insert:
                bq_client.insert_rows_json(table_ref, rows_to_insert)
                counts["drug_features"] += len(rows_to_insert)
            logger.info(f"Ingested {counts['drug_features']} rows into BigQuery {table_ref}")

        return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PrimeKG Ingestion Loader for Cloud Spanner Graph & BigQuery"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default="fivedaysai-prd-sandbox-317383",
        help="Google Cloud Project ID",
    )
    parser.add_argument(
        "--spanner-instance",
        type=str,
        default="primekg-instance-dev",
        help="Cloud Spanner Instance ID",
    )
    parser.add_argument(
        "--spanner-database",
        type=str,
        default="primekg-database",
        help="Cloud Spanner Database ID",
    )
    parser.add_argument(
        "--bq-dataset",
        type=str,
        default="primekg_analytics_dev",
        help="BigQuery Analytics Dataset ID",
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default="/tmp/primekg_staging",
        help="Directory containing downloaded PrimeKG files (kg.csv, *.tab)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum records to ingest (useful for testing and benchmarks)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Mutation batch size per commit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and stream records without writing to cloud databases",
    )

    args = parser.parse_args()

    loader = PrimeKGLoader(
        project_id=args.project_id,
        spanner_instance_id=args.spanner_instance,
        spanner_database_id=args.spanner_database,
        bq_dataset_id=args.bq_dataset,
    )

    source_path = Path(args.source_dir)
    kg_csv = source_path / "kg.csv"
    if not kg_csv.exists():
        logger.error(f"Cannot find kg.csv at {kg_csv}. Run data acquisition first!")
        sys.exit(1)

    print("=================================================================")
    print("  PrimeKG Worker Tier Ingestion (Spanner Graph + BigQuery)")
    print(f"  Source:       {kg_csv}")
    print(f"  Spanner DB:   {args.spanner_instance}/{args.spanner_database}")
    print(f"  BigQuery DS:  {args.bq_dataset}")
    print(f"  Dry Run:      {args.dry_run}")
    print(f"  Record Limit: {args.limit or 'Full Release'}")
    print("=================================================================")

    stats = loader.ingest_to_spanner(
        kg_csv_path=kg_csv,
        batch_size=args.batch_size,
        limit=args.limit,
        dry_run=args.dry_run,
    )

    print("\n--- Ingestion Statistics ---")
    print(f"Records Read:      {stats.total_records_read:,}")
    print(f"Unique Nodes:      {stats.unique_nodes_staged:,}")
    print(f"Edges Inserted:    {stats.edges_staged:,}")
    print(f"Batches Committed: {stats.batches_committed:,}")
    print(f"Duration:          {stats.duration_seconds}s")
    print(f"Throughput:        {stats.throughput_triples_sec:,} triples/s")
    if stats.errors:
        print(f"Errors Encountered:{len(stats.errors)}")


if __name__ == "__main__":
    main()
