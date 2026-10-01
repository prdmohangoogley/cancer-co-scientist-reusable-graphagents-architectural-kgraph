# GraphAgent: Reusable Worker Tier

`graphagent` is a domain-specialized, reusable Python library empowering autonomous AI agents to explore, reason over, and extract subgraphs from biomedical precision medicine knowledge graphs like **PrimeKG**.

---

## 🧩 Architecture & Components

```markdown
packages/graphagent/
├── adk/               # ADK definitions for PrimeKG traversal
│   ├── agent.py       # PrimeKGWorkerAgent execution logic
│   └── traversal.py   # Multi-hop biomedical path discovery algorithms
├── tools/             # GQL/SQL Traversal & Querying tools
│   ├── gql_tools.py   # Cloud Spanner Graph ISO GQL query execution
│   └── sql_tools.py   # BigQuery analytics & target feature scoring
├── data_loaders/       # 🚚 PrimeKG Ingestion Pipelines
│   └── primekg_loader.py # Batch streaming into Spanner Graph & BQ
└── iac/               # Package-specific IaC (Spanner + BQ)
    ├── main.tf
    ├── spanner.tf     # Spanner Graph DDL schema
    ├── bigquery.tf    # BigQuery dataset & embedding tables
    └── variables.tf
```

---

## ⚡ Usage Example

```python
from graphagent.adk.agent import PrimeKGWorkerAgent
from graphagent.adk.traversal import TraversalConfig

# Initialize worker agent with Cloud Spanner Graph bindings
worker = PrimeKGWorkerAgent(project_id="my-gcp-project")

# Query drug-target-disease subgraph for a cancer gene
subgraph = await worker.explore_gene_disease_pathways(
    gene_symbol="EGFR",
    disease_name="Non-small cell lung carcinoma",
    max_hops=2,
)

print(f"Discovered {len(subgraph.nodes)} entities and {len(subgraph.edges)} relations.")
```
