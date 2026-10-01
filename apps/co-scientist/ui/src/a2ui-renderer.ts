/**
 * Pure Declarative A2UI (Agent-to-UI) Renderer Client
 * Conforms to DOC-03 (Open AI Agent Protocol Stack):
 * - Non-executable JSON parsing
 * - Zero eval() or unsafe script evaluation (XSS Prevention)
 * - Safe mapping of catalog components to certified DOM nodes
 */

export interface A2UIComponent {
  component: string;
  id: string;
  props: Record<string, any>;
}

export interface A2UISurfacePayload {
  type: string;
  surface_id: string;
  intent?: string;
  components: A2UIComponent[];
  guidelines_cited?: string[];
}

export class A2UIRenderer {
  private targetElement: HTMLElement;

  constructor(targetElement: HTMLElement) {
    this.targetElement = targetElement;
  }

  /**
   * Render an A2UI declarative payload tree into the target container.
   */
  public renderSurface(payload: A2UISurfacePayload): void {
    this.targetElement.innerHTML = ''; // Clear container safely

    if (!payload.components || !Array.isArray(payload.components)) {
      console.warn('Invalid A2UI surface payload:', payload);
      return;
    }

    for (const comp of payload.components) {
      const el = this.renderComponent(comp);
      if (el) {
        this.targetElement.appendChild(el);
      }
    }
  }

  /**
   * Dispatch component creation based on catalog schema.
   */
  private renderComponent(comp: A2UIComponent): HTMLElement | null {
    switch (comp.component) {
      case 'InsightCard':
        return this.renderInsightCard(comp.props);
      case 'DrugRepurposingTable':
        return this.renderDrugRepurposingTable(comp.props);
      case 'KnowledgeGraphView':
        return this.renderKnowledgeGraphView(comp.props);
      default:
        console.warn(`Unrecognized A2UI component type: ${comp.component}`);
        return null;
    }
  }

  /**
   * Render an InsightCard component.
   */
  private renderInsightCard(props: Record<string, any>): HTMLElement {
    const card = document.createElement('div');
    card.className = `a2ui-card ${props.severity || 'info'}`;

    const header = document.createElement('div');
    header.className = 'card-header';

    const titleGroup = document.createElement('div');
    const title = document.createElement('div');
    title.className = 'card-title';
    title.textContent = props.title || 'Clinical Insight';
    titleGroup.appendChild(title);

    if (props.subtitle) {
      const sub = document.createElement('div');
      sub.className = 'card-subtitle';
      sub.textContent = props.subtitle;
      titleGroup.appendChild(sub);
    }
    header.appendChild(titleGroup);

    if (props.confidence_score !== undefined) {
      const badge = document.createElement('span');
      badge.className = 'confidence-badge';
      badge.textContent = `Confidence: ${(props.confidence_score * 100).toFixed(0)}%`;
      header.appendChild(badge);
    }
    card.appendChild(header);

    const summary = document.createElement('p');
    summary.className = 'card-summary';
    summary.textContent = props.summary || '';
    card.appendChild(summary);

    if (props.tags && Array.isArray(props.tags)) {
      const tagContainer = document.createElement('div');
      tagContainer.className = 'card-tags';
      for (const tag of props.tags) {
        const t = document.createElement('span');
        t.className = 'tag-badge';
        t.textContent = tag;
        tagContainer.appendChild(t);
      }
      card.appendChild(tagContainer);
    }

    return card;
  }

  /**
   * Render a DrugRepurposingTable component.
   */
  private renderDrugRepurposingTable(props: Record<string, any>): HTMLElement {
    const container = document.createElement('div');
    container.className = 'a2ui-table-container';

    if (props.title) {
      const h3 = document.createElement('h3');
      h3.textContent = props.title;
      h3.style.marginBottom = '1rem';
      container.appendChild(h3);
    }

    const table = document.createElement('table');
    table.className = 'a2ui-table';

    const thead = document.createElement('thead');
    thead.innerHTML = `
      <tr>
        <th>Drug</th>
        <th>Target Gene</th>
        <th>Clinical Phase</th>
        <th>Mechanism</th>
        <th>Confidence</th>
      </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    for (const item of props.candidates || []) {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><strong>${this.escapeHtml(item.drug_name || '')}</strong></td>
        <td><code>${this.escapeHtml(item.target_gene || '')}</code></td>
        <td>${this.escapeHtml(item.clinical_phase || '')}</td>
        <td>${this.escapeHtml(item.mechanism || '')}</td>
        <td><code>${((item.confidence || 0) * 100).toFixed(0)}%</code></td>
      `;
      tbody.appendChild(row);
    }
    table.appendChild(tbody);
    container.appendChild(table);

    return container;
  }

  /**
   * Render a KnowledgeGraphView component.
   */
  private renderKnowledgeGraphView(props: Record<string, any>): HTMLElement {
    const container = document.createElement('div');
    container.className = 'a2ui-graph-container';

    const stats = document.createElement('div');
    stats.className = 'graph-stats';
    const nodeCount = props.nodes ? props.nodes.length : 0;
    const edgeCount = props.edges ? props.edges.length : 0;
    stats.textContent = `Knowledge Graph Subgraph: ${nodeCount} Nodes • ${edgeCount} Edges (PrimeKG Traversal)`;
    container.appendChild(stats);

    const chips = document.createElement('div');
    chips.className = 'node-chips';

    for (const node of props.nodes || []) {
      const chip = document.createElement('div');
      chip.className = `node-chip ${node.label || ''}`;
      chip.textContent = `${node.label}: ${node.name}`;
      chips.appendChild(chip);
    }
    container.appendChild(chips);

    return container;
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}
