/**
 * Pure Declarative A2UI (Agent-to-UI) Renderer Client
 * Conforms to DOC-03 (Open AI Agent Protocol Stack):
 * - Non-executable JSON parsing
 * - Zero eval() or unsafe script evaluation (XSS Prevention)
 * - Safe mapping of catalog components to certified DOM nodes
 * - Parameterized component state bindings
 */





export class A2UIRenderer {
  constructor(targetElement) {
    this.targetElement = targetElement;
  }

  /**
   * Render an A2UI declarative payload tree into the target container.
   */
  renderSurface(payload){
    this.targetElement.innerHTML = ''; // Safely clear previous elements

    if (!payload.components || !Array.isArray(payload.components)) {
      console.warn('Invalid A2UI surface payload:', payload);
      return;
    }

    // Optional Surface Header with Intent and Governance Meta
    if (payload.intent || (payload.guidelines_cited && payload.guidelines_cited.length > 0)) {
      const surfaceMeta = this.renderSurfaceHeader(payload);
      this.targetElement.appendChild(surfaceMeta);
    }

    for (const comp of payload.components) {
      try {
        const el = this.renderComponent(comp);
        if (el) {
          this.targetElement.appendChild(el);
        }
      } catch (err) {
        console.error(`Error rendering component ${comp.component}:`, err);
      }
    }
  }

  /**
   * Append a single A2UI component to the surface.
   */
  appendComponent(comp){
    const el = this.renderComponent(comp);
    if (el) {
      this.targetElement.appendChild(el);
    }
  }

  /**
   * Render metadata header for the A2UI Surface.
   */
  renderSurfaceHeader(payload){
    const metaBar = document.createElement('div');
    metaBar.className = 'a2ui-surface-header';

    const intentPill = document.createElement('span');
    intentPill.className = 'surface-intent-badge';
    intentPill.textContent = `Intent: ${payload.intent || 'CLINICAL_ANALYSIS'}`;
    metaBar.appendChild(intentPill);

    if (payload.guidelines_cited && payload.guidelines_cited.length > 0) {
      const guidelinesList = document.createElement('div');
      guidelinesList.className = 'surface-guidelines';
      for (const g of payload.guidelines_cited) {
        const gBadge = document.createElement('span');
        gBadge.className = 'guideline-pill';
        gBadge.textContent = g;
        guidelinesList.appendChild(gBadge);
      }
      metaBar.appendChild(guidelinesList);
    }

    return metaBar;
  }

  /**
   * Dispatch component creation based on catalog schema.
   */
  renderComponent(comp){
    switch (comp.component) {
            case 'InteractiveGraphExplorer':
        return this.renderInteractiveGraphExplorer(comp.props);
      case 'InsightCard':
        return this.renderInsightCard(comp.props);
      case 'KnowledgeGraphView':
        return this.renderKnowledgeGraphView(comp.props);
      case 'PathwayChart':
        return this.renderPathwayChart(comp.props);
      case 'DrugRepurposingTable':
        return this.renderDrugRepurposingTable(comp.props);
      case 'MemoryTimeline':
        return this.renderMemoryTimeline(comp.props);
      case 'SimulationViewer':
        return this.renderSimulationViewer(comp.props);
      case 'ToxicityWarning':
        return this.renderToxicityWarning(comp.props);
      default:
        console.warn(`Unrecognized A2UI component type: ${comp.component}`);
        return null;
    }
  }

  /**
   * 1. Render an InsightCard component.
   */
  renderInsightCard(props){
    const card = document.createElement('div');
    card.className = `a2ui-card insight-card ${props.severity || 'info'}`;

    const header = document.createElement('div');
    header.className = 'card-header';

    const titleGroup = document.createElement('div');
    titleGroup.className = 'card-title-group';

    const title = document.createElement('h3');
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

    if (props.tags && Array.isArray(props.tags) && props.tags.length > 0) {
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
   * 2. Render a KnowledgeGraphView component (PrimeKG Subgraph).
   */
  renderKnowledgeGraphView(props){
    const container = document.createElement('div');
    container.className = 'a2ui-card a2ui-graph-card';

    const header = document.createElement('div');
    header.className = 'card-header';

    const title = document.createElement('h3');
    title.className = 'card-title';
    title.textContent = 'Biomedical Knowledge Graph Subgraph';
    header.appendChild(title);

    const nodeCount = props.nodes ? props.nodes.length : 0;
    const edgeCount = props.edges ? props.edges.length : 0;

    const stats = document.createElement('span');
    stats.className = 'confidence-badge';
    stats.textContent = `${nodeCount} Nodes • ${edgeCount} Edges (PrimeKG GQL)`;
    header.appendChild(stats);
    container.appendChild(header);

    // Nodes Section
    const nodesLabel = document.createElement('div');
    nodesLabel.className = 'graph-section-title';
    nodesLabel.textContent = 'Graph Entities:';
    container.appendChild(nodesLabel);

    const chips = document.createElement('div');
    chips.className = 'node-chips';

    for (const node of props.nodes || []) {
      const chip = document.createElement('div');
      chip.className = `node-chip ${node.label || 'Default'}`;
      chip.textContent = `${node.label}: ${node.name}`;
      if (node.properties && node.properties.role) {
        const roleSpan = document.createElement('span');
        roleSpan.className = 'chip-extra';
        roleSpan.textContent = ` (${node.properties.role})`;
        chip.appendChild(roleSpan);
      }
      chips.appendChild(chip);
    }
    container.appendChild(chips);

    // Edges Section
    if (props.edges && Array.isArray(props.edges) && props.edges.length > 0) {
      const edgesLabel = document.createElement('div');
      edgesLabel.className = 'graph-section-title';
      edgesLabel.style.marginTop = '1rem';
      edgesLabel.textContent = 'Knowledge Relationships:';
      container.appendChild(edgesLabel);

      const edgeList = document.createElement('div');
      edgeList.className = 'edge-list';

      for (const edge of props.edges) {
        const edgeItem = document.createElement('div');
        edgeItem.className = 'edge-item';

        const source = document.createElement('span');
        source.className = 'edge-node';
        source.textContent = edge.source_id;

        const rel = document.createElement('span');
        rel.className = 'edge-rel';
        rel.textContent = `—[ ${edge.relationship} ]—▶`;

        const target = document.createElement('span');
        target.className = 'edge-node';
        target.textContent = edge.target_id;

        edgeItem.appendChild(source);
        edgeItem.appendChild(rel);
        edgeItem.appendChild(target);

        if (edge.confidence !== undefined) {
          const conf = document.createElement('span');
          conf.className = 'edge-conf';
          conf.textContent = `(${(edge.confidence * 100).toFixed(0)}%)`;
          edgeItem.appendChild(conf);
        }

        edgeList.appendChild(edgeItem);
      }
      container.appendChild(edgeList);
    }

    return container;
  }

  /**
   * 3. Render a PathwayChart component.
   */
  renderPathwayChart(props){
    const card = document.createElement('div');
    card.className = 'a2ui-card pathway-chart-card';

    const header = document.createElement('div');
    header.className = 'card-header';

    const titleGroup = document.createElement('div');
    const title = document.createElement('h3');
    title.className = 'card-title';
    title.textContent = props.pathway_name || 'Biochemical Signaling Pathway';
    titleGroup.appendChild(title);

    if (props.pathway_id) {
      const sub = document.createElement('div');
      sub.className = 'card-subtitle';
      sub.textContent = `Pathway ID: ${props.pathway_id}`;
      titleGroup.appendChild(sub);
    }
    header.appendChild(titleGroup);

    if (props.dysregulation_status) {
      const statusBadge = document.createElement('span');
      statusBadge.className = `status-badge ${props.dysregulation_status}`;
      statusBadge.textContent = props.dysregulation_status.toUpperCase();
      header.appendChild(statusBadge);
    }
    card.appendChild(header);

    // Genes Involved Flow
    const cascadeContainer = document.createElement('div');
    cascadeContainer.className = 'pathway-cascade';

    const genes = props.genes_involved || [];
    const targetables = new Set(props.targetable_nodes || []);

    for (let i = 0; i < genes.length; i++) {
      const geneName = genes[i];
      const isTargetable = targetables.has(geneName);

      const nodeEl = document.createElement('div');
      nodeEl.className = `pathway-node ${isTargetable ? 'targetable' : ''}`;

      const nameSpan = document.createElement('span');
      nameSpan.className = 'node-symbol';
      nameSpan.textContent = geneName;
      nodeEl.appendChild(nameSpan);

      if (isTargetable) {
        const tBadge = document.createElement('span');
        tBadge.className = 'targetable-badge';
        tBadge.textContent = 'TARGETABLE';
        nodeEl.appendChild(tBadge);
      }

      cascadeContainer.appendChild(nodeEl);

      if (i < genes.length - 1) {
        const arrow = document.createElement('div');
        arrow.className = 'cascade-arrow';
        arrow.textContent = '➔';
        cascadeContainer.appendChild(arrow);
      }
    }

    card.appendChild(cascadeContainer);
    return card;
  }

  /**
   * 4. Render a DrugRepurposingTable component.
   */
  renderDrugRepurposingTable(props){
    const container = document.createElement('div');
    container.className = 'a2ui-card a2ui-table-container';

    if (props.title) {
      const header = document.createElement('div');
      header.className = 'card-header';
      const h3 = document.createElement('h3');
      h3.className = 'card-title';
      h3.textContent = props.title;
      header.appendChild(h3);
      container.appendChild(header);
    }

    const tableWrapper = document.createElement('div');
    tableWrapper.className = 'table-responsive-wrapper';

    const table = document.createElement('table');
    table.className = 'a2ui-table';

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const columns = ['Candidate Drug', 'Target Gene / Variant', 'Clinical Phase', 'Mechanism of Action', 'Confidence Score'];
    for (const col of columns) {
      const th = document.createElement('th');
      th.textContent = col;
      headerRow.appendChild(th);
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    for (const item of props.candidates || []) {
      const row = document.createElement('tr');

      const tdDrug = document.createElement('td');
      const drugName = document.createElement('strong');
      drugName.textContent = item.drug_name || '';
      tdDrug.appendChild(drugName);
      if (item.drug_id) {
        const drugId = document.createElement('div');
        drugId.className = 'cell-subtext';
        drugId.textContent = item.drug_id;
        tdDrug.appendChild(drugId);
      }
      row.appendChild(tdDrug);

      const tdGene = document.createElement('td');
      const geneCode = document.createElement('code');
      geneCode.className = 'code-pill';
      geneCode.textContent = item.target_gene || '—';
      tdGene.appendChild(geneCode);
      row.appendChild(tdGene);

      const tdPhase = document.createElement('td');
      const phaseBadge = document.createElement('span');
      phaseBadge.className = 'phase-badge';
      phaseBadge.textContent = item.clinical_phase || 'Investigational';
      tdPhase.appendChild(phaseBadge);
      row.appendChild(tdPhase);

      const tdMech = document.createElement('td');
      tdMech.textContent = item.mechanism || '—';
      row.appendChild(tdMech);

      const tdConf = document.createElement('td');
      const scoreVal = item.confidence !== undefined ? item.confidence : 0;
      const scoreBar = document.createElement('div');
      scoreBar.className = 'score-bar-wrapper';

      const barFill = document.createElement('div');
      barFill.className = 'score-bar-fill';
      barFill.style.width = `${Math.min(100, Math.max(0, scoreVal * 100))}%`;
      scoreBar.appendChild(barFill);

      const scoreLabel = document.createElement('span');
      scoreLabel.className = 'score-label';
      scoreLabel.textContent = `${(scoreVal * 100).toFixed(0)}%`;
      scoreBar.appendChild(scoreLabel);

      tdConf.appendChild(scoreBar);
      row.appendChild(tdConf);

      tbody.appendChild(row);
    }
    table.appendChild(tbody);
    tableWrapper.appendChild(table);
    container.appendChild(tableWrapper);

    return container;
  }

  /**
   * 5. Render a MemoryTimeline component (PAT-MEM-BANK).
   * Displays extracted clinical entities, biomarkers, and hypotheses across conversation turns.
   */
  renderMemoryTimeline(props){
    const card = document.createElement('div');
    card.className = 'a2ui-card memory-timeline-card';

    const header = document.createElement('div');
    header.className = 'card-header';

    const titleGroup = document.createElement('div');
    const title = document.createElement('h3');
    title.className = 'card-title';
    title.textContent = props.title || 'Memory Bank Longitudinal Timeline';
    titleGroup.appendChild(title);

    if (props.session_id) {
      const sub = document.createElement('div');
      sub.className = 'card-subtitle';
      sub.textContent = `Session: ${props.session_id} • PAT-MEM-BANK Progressive Recall`;
      titleGroup.appendChild(sub);
    }
    header.appendChild(titleGroup);

    const statsGroup = document.createElement('div');
    statsGroup.className = 'timeline-stats-group';

    if (props.confirmed_hypotheses_count !== undefined) {
      const hypBadge = document.createElement('span');
      hypBadge.className = 'confidence-badge';
      hypBadge.textContent = `${props.confirmed_hypotheses_count} Confirmed Hypotheses`;
      statsGroup.appendChild(hypBadge);
    }
    header.appendChild(statsGroup);
    card.appendChild(header);

    // Active Biomarkers Pill Row
    if (props.active_biomarkers && Array.isArray(props.active_biomarkers) && props.active_biomarkers.length > 0) {
      const bioRow = document.createElement('div');
      bioRow.className = 'memory-biomarkers-row';

      const label = document.createElement('span');
      label.className = 'row-label';
      label.textContent = 'Active Patient Biomarkers:';
      bioRow.appendChild(label);

      for (const bio of props.active_biomarkers) {
        const bioPill = document.createElement('span');
        bioPill.className = 'tag-badge biomarker-tag';
        bioPill.textContent = bio;
        bioRow.appendChild(bioPill);
      }
      card.appendChild(bioRow);
    }

    // Turns Timeline
    const timelineList = document.createElement('div');
    timelineList.className = 'timeline-turns-list';

    const turns = props.turns || [];
    for (const turn of turns) {
      const turnItem = document.createElement('div');
      turnItem.className = 'timeline-turn-item';

      const stepIndicator = document.createElement('div');
      stepIndicator.className = 'turn-step-indicator';
      stepIndicator.textContent = `T${turn.turn_number}`;
      turnItem.appendChild(stepIndicator);

      const turnContent = document.createElement('div');
      turnContent.className = 'turn-content-box';

      // Turn Header
      const turnHeader = document.createElement('div');
      turnHeader.className = 'turn-header-row';

      const turnTitle = document.createElement('span');
      turnTitle.className = 'turn-title-text';
      turnTitle.textContent = `Turn #${turn.turn_number}: "${turn.user_query}"`;
      turnHeader.appendChild(turnTitle);

      if (turn.timestamp) {
        const turnTime = document.createElement('span');
        turnTime.className = 'turn-time';
        turnTime.textContent = new Date(turn.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        turnHeader.appendChild(turnTime);
      }
      turnContent.appendChild(turnHeader);

      // Extracted Entities
      if (turn.extracted_entities && turn.extracted_entities.length > 0) {
        const entityBox = document.createElement('div');
        entityBox.className = 'turn-entities-box';

        const entLabel = document.createElement('span');
        entLabel.className = 'mini-label';
        entLabel.textContent = 'Extracted Entities: ';
        entityBox.appendChild(entLabel);

        for (const ent of turn.extracted_entities) {
          const pill = document.createElement('span');
          pill.className = `entity-pill ${ent.type || 'Entity'}`;
          pill.textContent = `${ent.type}: ${ent.name}`;
          entityBox.appendChild(pill);
        }
        turnContent.appendChild(entityBox);
      }

      // Hypotheses
      if (turn.hypotheses && turn.hypotheses.length > 0) {
        const hypBox = document.createElement('div');
        hypBox.className = 'turn-hypotheses-box';

        for (const h of turn.hypotheses) {
          const hRow = document.createElement('div');
          hRow.className = `hypothesis-item status-${h.status || 'formulated'}`;

          const statusBadge = document.createElement('span');
          statusBadge.className = `hyp-status-badge ${h.status}`;
          statusBadge.textContent = (h.status || 'Formulated').toUpperCase();
          hRow.appendChild(statusBadge);

          const statement = document.createElement('span');
          statement.className = 'hyp-statement';
          statement.textContent = h.statement;
          hRow.appendChild(statement);

          hypBox.appendChild(hRow);
        }
        turnContent.appendChild(hypBox);
      }

      // Turn Summary
      if (turn.summary) {
        const summary = document.createElement('p');
        summary.className = 'turn-summary-text';
        summary.textContent = turn.summary;
        turnContent.appendChild(summary);
      }

      turnItem.appendChild(turnContent);
      timelineList.appendChild(turnItem);
    }

    card.appendChild(timelineList);
    return card;
  }

  /**
   * 6. Render a SimulationViewer component.
   * 3D/continuous trajectory viewer for AlphaFold docking paths (OMPL) or cellular swarming density (PhysiCell).
   */
  renderSimulationViewer(props){
    const card = document.createElement('div');
    card.className = 'a2ui-card simulation-viewer-card';

    const header = document.createElement('div');
    header.className = 'card-header';

    const titleGroup = document.createElement('div');
    const title = document.createElement('h3');
    title.className = 'card-title';
    title.textContent = props.title || 'Continuous Molecular Trajectory Simulation';
    titleGroup.appendChild(title);

    const sub = document.createElement('div');
    sub.className = 'card-subtitle';
    sub.textContent = `Target: ${props.target_protein || 'Target Kinase'} • Ligand: ${props.ligand_name || 'Candidate Small Molecule'}`;
    titleGroup.appendChild(sub);
    header.appendChild(titleGroup);

    const typeBadge = document.createElement('span');
    typeBadge.className = 'sim-type-badge';
    typeBadge.textContent = props.simulation_type || 'AlphaFold_Docking_OMPL';
    header.appendChild(typeBadge);
    card.appendChild(header);

    // 3D Visualizer Mockup Canvas
    const viewportContainer = document.createElement('div');
    viewportContainer.className = 'sim-viewport-container';

    // SVG 3D representation
    const svgStage = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svgStage.setAttribute('viewBox', '0 0 600 240');
    svgStage.setAttribute('class', 'sim-svg-stage');

    // Binding pocket mesh representation
    const pocketPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    pocketPath.setAttribute('d', 'M 100,180 Q 200,60 300,120 T 500,80 Q 550,160 480,210 T 200,220 Z');
    pocketPath.setAttribute('fill', 'rgba(56, 189, 248, 0.08)');
    pocketPath.setAttribute('stroke', 'rgba(56, 189, 248, 0.4)');
    pocketPath.setAttribute('stroke-width', '2');
    pocketPath.setAttribute('stroke-dasharray', '4 4');
    svgStage.appendChild(pocketPath);

    // Trajectory spline (OMPL Docking path)
    const trajectoryPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    trajectoryPath.setAttribute('d', 'M 80,40 C 180,30 220,150 300,125 C 380,100 420,160 460,140');
    trajectoryPath.setAttribute('fill', 'none');
    trajectoryPath.setAttribute('stroke', '#a855f7');
    trajectoryPath.setAttribute('stroke-width', '3');
    svgStage.appendChild(trajectoryPath);

    // Active site pocket highlight
    const pocketCenter = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    pocketCenter.setAttribute('cx', '300');
    pocketCenter.setAttribute('cy', '125');
    pocketCenter.setAttribute('r', '24');
    pocketCenter.setAttribute('fill', 'rgba(16, 185, 129, 0.15)');
    pocketCenter.setAttribute('stroke', '#10b981');
    pocketCenter.setAttribute('stroke-width', '2');
    svgStage.appendChild(pocketCenter);

    // Current Ligand position
    const ligandPoint = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    ligandPoint.setAttribute('cx', '300');
    ligandPoint.setAttribute('cy', '125');
    ligandPoint.setAttribute('r', '10');
    ligandPoint.setAttribute('fill', '#f59e0b');
    ligandPoint.setAttribute('stroke', '#ffffff');
    ligandPoint.setAttribute('stroke-width', '2');
    svgStage.appendChild(ligandPoint);

    // Overlay stage text
    const textPocket = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    textPocket.setAttribute('x', '300');
    textPocket.setAttribute('y', '165');
    textPocket.setAttribute('text-anchor', 'middle');
    textPocket.setAttribute('fill', '#94a3b8');
    textPocket.setAttribute('font-size', '12');
    textPocket.textContent = 'ATP Binding Pocket (T790M Mutant)';
    svgStage.appendChild(textPocket);

    viewportContainer.appendChild(svgStage);

    // HUD overlays on top of the 3D viewport
    const hudOverlay = document.createElement('div');
    hudOverlay.className = 'sim-hud-overlay';

    const frameInfo = document.createElement('span');
    frameInfo.className = 'sim-frame-counter';
    frameInfo.textContent = `Frame: ${props.current_frame || 180} / ${props.trajectory_frames || 250}`;
    hudOverlay.appendChild(frameInfo);

    const cameraMode = document.createElement('span');
    cameraMode.className = 'sim-camera-mode';
    cameraMode.textContent = `Camera: ${props.view_config?.camera_preset || 'Binding Pocket'}`;
    hudOverlay.appendChild(cameraMode);

    viewportContainer.appendChild(hudOverlay);
    card.appendChild(viewportContainer);

    // Scrubber Bar & Controls
    const controlsBar = document.createElement('div');
    controlsBar.className = 'sim-controls-bar';

    const playBtn = document.createElement('button');
    playBtn.type = 'button';
    playBtn.className = 'sim-btn-play';
    playBtn.textContent = '▶ Play Trajectory';
    let isPlaying = false;
    playBtn.addEventListener('click', () => {
      isPlaying = !isPlaying;
      playBtn.textContent = isPlaying ? '⏸ Pause' : '▶ Play Trajectory';
    });
    controlsBar.appendChild(playBtn);

    const slider = document.createElement('input');
    slider.type = 'range';
    slider.className = 'sim-scrubber-slider';
    slider.min = '1';
    slider.max = `${props.trajectory_frames || 250}`;
    slider.value = `${props.current_frame || 180}`;
    slider.addEventListener('input', () => {
      frameInfo.textContent = `Frame: ${slider.value} / ${props.trajectory_frames || 250}`;
    });
    controlsBar.appendChild(slider);

    const resetBtn = document.createElement('button');
    resetBtn.type = 'button';
    resetBtn.className = 'sim-btn-tool';
    resetBtn.textContent = 'Reset View';
    controlsBar.appendChild(resetBtn);

    card.appendChild(controlsBar);

    // Simulation Metrics Panel
    if (props.metrics) {
      const metricsPanel = document.createElement('div');
      metricsPanel.className = 'sim-metrics-grid';

      if (props.metrics.binding_affinity_kcal_mol !== undefined) {
        const m1 = this.createMetricCard('Binding Affinity', `${props.metrics.binding_affinity_kcal_mol} kcal/mol`, 'High Affinity');
        metricsPanel.appendChild(m1);
      }
      if (props.metrics.rmsd_angstrom !== undefined) {
        const m2 = this.createMetricCard('RMSD', `${props.metrics.rmsd_angstrom} Å`, 'Stable Geometry');
        metricsPanel.appendChild(m2);
      }
      if (props.metrics.clash_score !== undefined) {
        const m3 = this.createMetricCard('Clash Score', `${props.metrics.clash_score}`, 'Optimal Sterics');
        metricsPanel.appendChild(m3);
      }
      if (props.metrics.cell_density_confluence_pct !== undefined) {
        const m4 = this.createMetricCard('Swarming Confluence', `${props.metrics.cell_density_confluence_pct}%`, 'PhysiCell In Vitro');
        metricsPanel.appendChild(m4);
      }

      card.appendChild(metricsPanel);
    }

    return card;
  }

  /**
   * Helper to create a single metric card inside simulation telemetry.
   */
  createMetricCard(label, value, badge){
    const card = document.createElement('div');
    card.className = 'metric-tile';

    const lbl = document.createElement('div');
    lbl.className = 'metric-tile-label';
    lbl.textContent = label;
    card.appendChild(lbl);

    const val = document.createElement('div');
    val.className = 'metric-tile-val';
    val.textContent = value;
    card.appendChild(val);

    const bdg = document.createElement('div');
    bdg.className = 'metric-tile-badge';
    bdg.textContent = badge;
    card.appendChild(bdg);

    return card;
  }

  /**
   * 7. Render a ToxicityWarning component.
   * Displays contraindications, adverse reactions, and clinical warnings.
   */
  renderToxicityWarning(props){
    const card = document.createElement('div');
    const severity = props.severity || 'high';
    card.className = `a2ui-card toxicity-warning-card severity-${severity}`;

    const banner = document.createElement('div');
    banner.className = 'tox-banner';

    const iconSpan = document.createElement('span');
    iconSpan.className = 'tox-icon';
    iconSpan.textContent = severity === 'black_box' ? '☠️' : '⚠️';
    banner.appendChild(iconSpan);

    const headerText = document.createElement('div');
    headerText.className = 'tox-header-text';

    const title = document.createElement('h3');
    title.className = 'tox-title';
    title.textContent = `${(props.warning_type || 'Clinical Warning').toUpperCase()}: ${props.drug_name || 'Pharmacological Agent'}`;
    headerText.appendChild(title);

    const sevBadge = document.createElement('span');
    sevBadge.className = `tox-sev-badge ${severity}`;
    sevBadge.textContent = `${severity.replace('_', ' ').toUpperCase()} PRIORITY`;
    headerText.appendChild(sevBadge);

    banner.appendChild(headerText);
    card.appendChild(banner);

    // Warning Message
    const msg = document.createElement('p');
    msg.className = 'tox-message-body';
    msg.textContent = props.message || '';
    card.appendChild(msg);

    // Contraindicated Conditions List
    if (props.contraindicated_conditions && Array.isArray(props.contraindicated_conditions) && props.contraindicated_conditions.length > 0) {
      const condSection = document.createElement('div');
      condSection.className = 'tox-section';

      const condTitle = document.createElement('div');
      condTitle.className = 'tox-section-label';
      condTitle.textContent = 'Contraindicated Conditions:';
      condSection.appendChild(condTitle);

      const ul = document.createElement('ul');
      ul.className = 'tox-list';
      for (const cond of props.contraindicated_conditions) {
        const li = document.createElement('li');
        li.textContent = cond;
        ul.appendChild(li);
      }
      condSection.appendChild(ul);
      card.appendChild(condSection);
    }

    // Interacting Drugs
    if (props.interacting_drugs && Array.isArray(props.interacting_drugs) && props.interacting_drugs.length > 0) {
      const drugSection = document.createElement('div');
      drugSection.className = 'tox-section';

      const drugTitle = document.createElement('div');
      drugTitle.className = 'tox-section-label';
      drugTitle.textContent = 'Significant Drug-Drug Interactions:';
      drugSection.appendChild(drugTitle);

      const chips = document.createElement('div');
      chips.className = 'tox-chips-row';
      for (const drug of props.interacting_drugs) {
        const chip = document.createElement('span');
        chip.className = 'tox-chip-drug';
        chip.textContent = drug;
        chips.appendChild(chip);
      }
      drugSection.appendChild(chips);
      card.appendChild(drugSection);
    }

    // Adverse Effects Table
    if (props.adverse_effects && Array.isArray(props.adverse_effects) && props.adverse_effects.length > 0) {
      const aeSection = document.createElement('div');
      aeSection.className = 'tox-section';

      const aeTitle = document.createElement('div');
      aeTitle.className = 'tox-section-label';
      aeTitle.textContent = 'Reported Adverse Reactions:';
      aeSection.appendChild(aeTitle);

      const table = document.createElement('table');
      table.className = 'tox-table';

      const thead = document.createElement('thead');
      const tr = document.createElement('tr');
      ['Adverse Event', 'Incidence', 'Clinical Severity'].forEach((h) => {
        const th = document.createElement('th');
        th.textContent = h;
        tr.appendChild(th);
      });
      thead.appendChild(tr);
      table.appendChild(thead);

      const tbody = document.createElement('tbody');
      for (const ae of props.adverse_effects) {
        const row = document.createElement('tr');
        const td1 = document.createElement('td');
        td1.textContent = ae.effect || '—';
        const td2 = document.createElement('td');
        td2.textContent = ae.frequency || '—';
        const td3 = document.createElement('td');
        td3.textContent = ae.severity || '—';
        row.appendChild(td1);
        row.appendChild(td2);
        row.appendChild(td3);
        tbody.appendChild(row);
      }
      table.appendChild(tbody);
      aeSection.appendChild(table);
      card.appendChild(aeSection);
    }

    // Clinical Recommendation Box
    if (props.clinical_recommendation) {
      const recBox = document.createElement('div');
      recBox.className = 'tox-recommendation-box';

      const recIcon = document.createElement('span');
      recIcon.className = 'rec-icon';
      recIcon.textContent = '📋';
      recBox.appendChild(recIcon);

      const recText = document.createElement('div');
      recText.className = 'rec-text';

      const recTitle = document.createElement('strong');
      recTitle.textContent = 'Actionable Clinical Recommendation: ';
      recText.appendChild(recTitle);

      const recContent = document.createElement('span');
      recContent.textContent = props.clinical_recommendation;
      recText.appendChild(recContent);

      recBox.appendChild(recText);
      card.appendChild(recBox);
    }

    return card;
  }

  renderInteractiveGraphExplorer(props) {
    try {
      const card = document.createElement('div');
      card.className = 'a2ui-card interactive-graph-card';

      const header = document.createElement('div');
      header.className = 'card-header';
      header.innerHTML = `
        <div class="card-title-group">
          <h3 class="card-title">${props.title || 'Interactive PrimeKG Knowledge Graph'}</h3>
          <div class="card-subtitle">Algorithm: <span class="badge-algo">${props.algorithm_applied || 'GQL Traversal'}</span> &bull; ${props.node_count || (props.nodes ? props.nodes.length : 0)} Nodes &bull; ${props.edge_count || (props.edges ? props.edges.length : 0)} Edges</div>
        </div>
        <div class="graph-actions-toolbar">
          <button type="button" class="btn-ctrl btn-zoom-in" title="Zoom In">+</button>
          <button type="button" class="btn-ctrl btn-zoom-out" title="Zoom Out">−</button>
          <button type="button" class="btn-ctrl btn-reset" title="Reset View">Reset</button>
        </div>
      `;
      card.appendChild(header);

      const svgWrap = document.createElement('div');
      svgWrap.className = 'graph-canvas-wrap';
      svgWrap.style.position = 'relative';
      svgWrap.style.overflow = 'hidden';
      svgWrap.style.background = '#090d16';
      svgWrap.style.borderRadius = '8px';
      svgWrap.style.border = '1px solid #1e293b';
      svgWrap.style.height = '520px';
      svgWrap.style.minHeight = '520px';

      const vb = props.view_box || { width: 860, height: 500 };
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', `0 0 ${vb.width} ${vb.height}`);
      svg.setAttribute('width', '100%');
      svg.setAttribute('height', '500');
      svg.style.width = '100%';
      svg.style.height = '500px';
      svg.style.display = 'block';
      svg.style.cursor = 'grab';

      // Inject standard defs into svg
      svg.innerHTML = `
        <defs>
          <marker id="arrow" markerWidth="10" markerHeight="7" refX="26" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
          </marker>
          <marker id="arrow-active" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#10b981" />
          </marker>
          <filter id="glow-hub" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="glow-gatekeeper" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feColorMatrix type="matrix" values="1 0 0 0 0.95  0 0 0 0 0.2  0 0 0 0 0.35  0 0 0 1 0"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
      `;

      const gViewport = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      gViewport.setAttribute('class', 'graph-viewport');

      const nodeMap = new Map();
      if (props.nodes && Array.isArray(props.nodes)) {
        for (const n of props.nodes) {
          if (n.id) nodeMap.set(n.id, n);
          if (n.name) nodeMap.set(n.name, n);
        }
      }

      // Edges
      const edgesG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      if (props.edges && Array.isArray(props.edges)) {
        for (const e of props.edges) {
          const s = nodeMap.get(e.source_id);
          const t = nodeMap.get(e.target_id);
          if (s && t) {
            const sx = s.x !== undefined ? s.x : 400;
            const sy = s.y !== undefined ? s.y : 250;
            const tx = t.x !== undefined ? t.x : 400;
            const ty = t.y !== undefined ? t.y : 250;

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', String(sx));
            line.setAttribute('y1', String(sy));
            line.setAttribute('x2', String(tx));
            line.setAttribute('y2', String(ty));
            line.setAttribute('stroke', e.is_shortest_path ? '#10b981' : '#334155');
            line.setAttribute('stroke-width', e.is_shortest_path ? '3.5' : '1.8');
            line.setAttribute('stroke-dasharray', e.style === 'dashed' ? '5,5' : 'none');
            line.setAttribute('marker-end', e.is_shortest_path ? 'url(#arrow-active)' : 'url(#arrow)');
            line.setAttribute('opacity', '0.85');
            edgesG.appendChild(line);

            // Edge label
            const midX = (sx + tx) / 2;
            const midY = (sy + ty) / 2;
            const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            txt.setAttribute('x', String(midX));
            txt.setAttribute('y', String(midY - 5));
            txt.setAttribute('text-anchor', 'middle');
            txt.setAttribute('fill', '#64748b');
            txt.setAttribute('font-size', '9px');
            txt.setAttribute('font-family', 'Roboto Mono, monospace');
            txt.textContent = e.relationship || 'INTERACTS_WITH';
            edgesG.appendChild(txt);
          }
        }
      }
      gViewport.appendChild(edgesG);

      // Nodes
      const nodesG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      if (props.nodes && Array.isArray(props.nodes)) {
        for (const n of props.nodes) {
          const nx = n.x !== undefined ? n.x : 400;
          const ny = n.y !== undefined ? n.y : 250;
          const nr = n.radius || 24;

          const nodeG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
          nodeG.style.cursor = 'pointer';

          const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          circle.setAttribute('cx', String(nx));
          circle.setAttribute('cy', String(ny));
          circle.setAttribute('r', String(nr));
          circle.setAttribute('fill', n.color || '#38bdf8');
          circle.setAttribute('stroke', n.is_gatekeeper ? '#f43f5e' : (n.is_hub ? '#fbbf24' : '#0f172a'));
          circle.setAttribute('stroke-width', n.is_gatekeeper ? '3.5' : (n.is_hub ? '3' : '2'));
          if (n.is_gatekeeper) {
            circle.setAttribute('filter', 'url(#glow-gatekeeper)');
          } else if (n.is_hub) {
            circle.setAttribute('filter', 'url(#glow-hub)');
          }

          const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          label.setAttribute('x', String(nx));
          label.setAttribute('y', String(ny + 4));
          label.setAttribute('text-anchor', 'middle');
          label.setAttribute('fill', '#ffffff');
          label.setAttribute('font-size', n.name && n.name.length > 8 ? '10px' : '12px');
          label.setAttribute('font-weight', '600');
          label.setAttribute('font-family', 'Google Sans, sans-serif');
          label.textContent = n.name || n.id;

          const badge = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          badge.setAttribute('x', String(nx));
          badge.setAttribute('y', String(ny + nr + 14));
          badge.setAttribute('text-anchor', 'middle');
          badge.setAttribute('fill', '#94a3b8');
          badge.setAttribute('font-size', '10px');
          badge.setAttribute('font-family', 'Roboto Mono, monospace');
          badge.textContent = n.label || 'Entity';

          nodeG.appendChild(circle);
          nodeG.appendChild(label);
          nodeG.appendChild(badge);

          nodeG.addEventListener('click', (ev) => {
            ev.stopPropagation();
            alert(`🧬 Entity Inspector:\nName: ${n.name || n.id}\nType: ${n.label || 'Entity'}\nCanonical ID: ${n.id}\nRole: ${n.is_hub ? 'Network Hub' : (n.is_gatekeeper ? 'Gatekeeper Bottleneck' : 'Member')}\nDegree: ${n.degree || 1}`);
          });

          nodesG.appendChild(nodeG);
        }
      }
      gViewport.appendChild(nodesG);
      svg.appendChild(gViewport);
      svgWrap.appendChild(svg);
      card.appendChild(svgWrap);

      // Zoom Controls
      let scale = 1.0;
      const btnIn = header.querySelector('.btn-zoom-in');
      const btnOut = header.querySelector('.btn-zoom-out');
      const btnReset = header.querySelector('.btn-reset');

      btnIn?.addEventListener('click', () => {
        scale = Math.min(2.5, scale + 0.2);
        gViewport.setAttribute('transform', `scale(${scale})`);
      });
      btnOut?.addEventListener('click', () => {
        scale = Math.max(0.5, scale - 0.2);
        gViewport.setAttribute('transform', `scale(${scale})`);
      });
      btnReset?.addEventListener('click', () => {
        scale = 1.0;
        gViewport.setAttribute('transform', 'scale(1)');
      });

      return card;
    } catch (err) {
      console.error('Error in renderInteractiveGraphExplorer:', err);
      const fallback = document.createElement('div');
      fallback.className = 'a2ui-card';
      fallback.innerHTML = `<div style="color: #f87171; padding: 1rem;">Failed to render interactive graph: ${err.message}</div>`;
      return fallback;
    }
  }
}
