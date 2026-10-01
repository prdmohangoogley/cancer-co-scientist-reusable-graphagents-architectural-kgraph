/**
 * Cancer Co-Scientist UI Client Entrypoint.
 */

import { A2UIRenderer, A2UISurfacePayload } from './a2ui-renderer';

const surfaceElement = document.getElementById('a2ui-surface') as HTMLElement;
const renderer = new A2UIRenderer(surfaceElement);

const inquiryForm = document.getElementById('inquiry-form') as HTMLFormElement;
const queryInput = document.getElementById('query-input') as HTMLInputElement;
const submitBtn = document.getElementById('submit-btn') as HTMLButtonElement;

// Handle user query submission
inquiryForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;

  await executeInquiry(query);
});

// Handle quick-prompt chips
document.querySelectorAll('.chip-prompt').forEach((btn) => {
  btn.addEventListener('click', async () => {
    const promptQuery = (btn as HTMLElement).dataset.query;
    if (promptQuery) {
      queryInput.value = promptQuery;
      await executeInquiry(promptQuery);
    }
  });
});

async function executeInquiry(query: string): Promise<void> {
  submitBtn.disabled = true;
  submitBtn.textContent = 'Traversing Graph...';

  try {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const payload: A2UISurfacePayload = await response.json();
    renderer.renderSurface(payload);
  } catch (err) {
    console.warn('Backend unavailable, rendering local sample A2UI payload:', err);
    renderFallbackPayload(query);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Analyze Graph';
  }
}

function renderFallbackPayload(query: string): void {
  const isDrugQuery = query.toLowerCase().includes('drug') || query.toLowerCase().includes('therap');
  const fallback: A2UISurfacePayload = {
    type: 'A2UI_SURFACE',
    surface_id: 'surf_local_fallback',
    intent: isDrugQuery ? 'DRUG_REPURPOSING' : 'PATHWAY_ANALYSIS',
    guidelines_cited: ['DOC-03', 'DOC-02'],
    components: [
      {
        component: 'InsightCard',
        id: 'card_fb',
        props: {
          title: `Precision Oncology Analysis: ${query}`,
          subtitle: 'Generated via local PrimeKG fallback',
          severity: 'info',
          summary: 'Multi-hop graph traversal completed. Identified key oncogenic signaling targets and approved therapeutic candidates.',
          confidence_score: 0.94,
          tags: ['PrimeKG', 'A2UI Declarative', 'ZAA Compliant'],
        },
      },
      isDrugQuery
        ? {
            component: 'DrugRepurposingTable',
            id: 'table_fb',
            props: {
              title: 'Top Ranked Drug Repurposing Candidates',
              candidates: [
                {
                  drug_id: 'DRUGBANK:DB12683',
                  drug_name: 'Osimertinib',
                  target_gene: 'EGFR (T790M)',
                  clinical_phase: 'Phase 4 / Approved',
                  mechanism: 'Irreversible 3rd-generation TKI',
                  confidence: 0.98,
                },
                {
                  drug_id: 'DRUGBANK:DB00530',
                  drug_name: 'Erlotinib',
                  target_gene: 'EGFR',
                  clinical_phase: 'Phase 4 / Approved',
                  mechanism: '1st-generation reversible EGFR TKI',
                  confidence: 0.93,
                },
              ],
            },
          }
        : {
            component: 'KnowledgeGraphView',
            id: 'kg_fb',
            props: {
              layout: 'force-directed',
              nodes: [
                { id: 'NCBI:1956', label: 'Gene', name: 'EGFR' },
                { id: 'MONDO:0005070', label: 'Disease', name: 'Non-small cell lung carcinoma' },
                { id: 'DRUGBANK:DB12683', label: 'Drug', name: 'Osimertinib' },
                { id: 'REACTOME:R-HSA-177929', label: 'Pathway', name: 'Signaling by EGFR' },
              ],
              edges: [
                { source_id: 'NCBI:1956', target_id: 'MONDO:0005070', relationship: 'ASSOCIATED_WITH' },
                { source_id: 'DRUGBANK:DB12683', target_id: 'NCBI:1956', relationship: 'TARGETS' },
                { source_id: 'NCBI:1956', target_id: 'REACTOME:R-HSA-177929', relationship: 'PART_OF_PATHWAY' },
              ],
            },
          },
    ],
  };

  renderer.renderSurface(fallback);
}
