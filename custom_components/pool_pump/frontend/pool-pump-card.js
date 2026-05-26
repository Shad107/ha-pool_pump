/**
 * Pool Pump Card — Home Assistant Lovelace custom card
 *
 * Reads a "pool" sensor exposed by the Shad107/ha-pool_pump integration
 * (state = preset name, attributes carry shape/volume/depth and an inline
 * SVG of the pool). Renders the SVG, schedule, current state, and
 * Auto/On/Off/Refresh action buttons.
 *
 * Pure vanilla web-component — no LitElement dependency, no build step.
 * Compatible with Home Assistant >= 2024.1.
 */

const CARD_VERSION = "0.3.5";

const HA_TEMPLATE_RE = /^(\w+)\.(\w+)$/;

class PoolPumpCard extends HTMLElement {
  static getStubConfig(hass) {
    // Suggest the first pool entity found, otherwise placeholder.
    const candidates = Object.keys(hass.states).filter(
      (id) =>
        id.startsWith("sensor.") &&
        id.includes("pool_pump_manager") &&
        (id.endsWith("_piscine") || id.endsWith("_pool"))
    );
    return {
      type: "custom:pool-pump-card",
      pool_entity: candidates[0] || "sensor.pool_pump_manager_piscine",
    };
  }

  static async getConfigElement() {
    await import("./pool-pump-card-editor.js");
    return document.createElement("pool-pump-card-editor");
  }

  setConfig(config) {
    if (!config.pool_entity) {
      throw new Error("pool_entity is required");
    }
    if (!HA_TEMPLATE_RE.test(config.pool_entity)) {
      throw new Error("pool_entity must look like sensor.something");
    }
    this._config = {
      title: config.title ?? null,
      pool_entity: config.pool_entity,
      mode_entity: config.mode_entity ?? this._derive(config.pool_entity, "select", "mode"),
      status_entity: config.status_entity ?? this._derive(config.pool_entity, "sensor", "statut", "status"),
      start_entity: config.start_entity ?? this._derive(config.pool_entity, "sensor", "heure_de_debut", "pump_start_time"),
      end_entity: config.end_entity ?? this._derive(config.pool_entity, "sensor", "heure_de_fin", "pump_end_time"),
      duration_entity: config.duration_entity ?? this._derive(config.pool_entity, "sensor", "duree_journaliere", "pump_daily_duration"),
      temperature_entity: config.temperature_entity ?? this._derive(config.pool_entity, "sensor", "temperature_utilisee", "temperature_used"),
      heatwave_entity: config.heatwave_entity ?? this._derive(config.pool_entity, "binary_sensor", "mode_canicule", "heatwave_override"),
      pump_target_entity: config.pump_target_entity ?? this._derive(config.pool_entity, "binary_sensor", "pompe_doit_tourner", "pump_should_be_on"),
      pump_switch: config.pump_switch ?? null,
      electrolyzer_switch: config.electrolyzer_switch ?? null,
    };
    this._render();
  }

  _derive(refEntity, domain, ...candidates) {
    // ref = "sensor.pool_pump_manager_piscine" → prefix = "pool_pump_manager"
    const [, name] = refEntity.split(".", 2);
    const idx = name.lastIndexOf("_");
    if (idx <= 0) return null;
    const prefix = name.slice(0, idx);
    // Try each candidate suffix; the caller is expected to pick the
    // matching translation. We can't probe hass here (setConfig has no
    // hass yet), so we just take the first suggestion and resolve it
    // against this.hass in _render().
    return candidates.map((c) => `${domain}.${prefix}_${c}`);
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _pick(entityCandidates) {
    if (!entityCandidates) return null;
    if (typeof entityCandidates === "string") return entityCandidates;
    if (!this._hass) return entityCandidates[0];
    for (const eid of entityCandidates) {
      if (this._hass.states[eid]) return eid;
    }
    return entityCandidates[0];
  }

  _state(entity) {
    if (!this._hass || !entity) return null;
    return this._hass.states[entity] || null;
  }

  _render() {
    if (!this._config) return;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this.shadowRoot.appendChild(document.createElement("style")).textContent = STYLES;
      this._root = document.createElement("ha-card");
      this.shadowRoot.appendChild(this._root);
    }
    if (!this._hass) {
      // No hass yet (picker preview, or pre-attach). Render a neutral
      // placeholder so the picker doesn't show an infinite spinner.
      this._root.innerHTML = `
        <div class="placeholder">
          <ha-icon icon="mdi:pool"></ha-icon>
          <div class="placeholder-title">Pool Pump Card</div>
          <div class="placeholder-subtitle">Visuel + contrôles pour ta piscine</div>
        </div>`;
      return;
    }

    const c = this._config;
    const pool = this._state(c.pool_entity);
    const status = this._state(this._pick(c.status_entity));
    const mode = this._state(this._pick(c.mode_entity));
    const start = this._state(this._pick(c.start_entity));
    const end = this._state(this._pick(c.end_entity));
    const duration = this._state(this._pick(c.duration_entity));
    const temp = this._state(this._pick(c.temperature_entity));
    const heatwave = this._state(this._pick(c.heatwave_entity));
    const pumpTarget = this._state(this._pick(c.pump_target_entity));

    if (!pool) {
      this._root.innerHTML = `
        <div class="error">
          <ha-icon icon="mdi:alert-circle"></ha-icon>
          Entity not found: <code>${c.pool_entity}</code>
        </div>`;
      return;
    }

    const svg = pool.attributes.svg || "";
    const title = c.title ?? pool.state ?? "Pool";
    const modeState = mode ? mode.state : "auto";

    this._root.innerHTML = `
      <div class="card">
        <div class="header">
          <ha-icon icon="mdi:pool"></ha-icon>
          <span class="title">${title}</span>
          ${heatwave && heatwave.state === "on" ? `<span class="badge heatwave">CANICULE</span>` : ""}
          <span class="mode-pill mode-${modeState}" title="Mode actuel">${modeLabel(modeState)}</span>
        </div>

        <div class="visual ${pumpTarget && pumpTarget.state === "on" ? "running" : ""}">
          ${svg || `<div class="no-svg">No preset selected — pick a pool model in the integration options to enable the visual.</div>`}
        </div>

        <div class="schedule">
          ${cell("mdi:clock-start", "Début", fmtTime(start))}
          ${cell("mdi:clock-end", "Fin",    fmtTime(end))}
          ${cell("mdi:timer-sand", "Durée", duration ? `${parseFloat(duration.state).toFixed(1)} h` : "—")}
          ${cell("mdi:thermometer", "T° eau", temp ? `${parseFloat(temp.state).toFixed(1)} °C` : "—")}
          ${cell("mdi:state-machine", "État", status ? statusLabel(status.state) : "—")}
        </div>

        <div class="actions">
          ${actionBtn("mdi:play",       "Marche", () => this._setMode("on"),    modeState === "on")}
          ${actionBtn("mdi:autorenew",  "Auto",   () => this._setMode("auto"),  modeState === "auto")}
          ${actionBtn("mdi:stop",       "Arrêt",  () => this._setMode("off"),   modeState === "off")}
          ${actionBtn("mdi:refresh",    "Refresh",() => this._refresh(),        false)}
        </div>
      </div>
    `;

    // Bind the buttons (innerHTML lost handlers)
    const btns = this._root.querySelectorAll(".action-btn");
    btns[0].onclick = () => this._setMode("on");
    btns[1].onclick = () => this._setMode("auto");
    btns[2].onclick = () => this._setMode("off");
    btns[3].onclick = () => this._refresh();
  }

  _setMode(option) {
    const modeId = this._pick(this._config.mode_entity);
    if (!modeId || !this._hass) return;
    this._hass.callService("select", "select_option", {
      entity_id: modeId,
      option,
    });
  }

  _refresh() {
    if (!this._hass) return;
    this._hass.callService("pool_pump", "refresh", {});
  }

  getCardSize() {
    return 4;
  }
}

function modeLabel(s) {
  return { auto: "Auto", on: "Marche", off: "Arrêt" }[s] || s;
}

function statusLabel(s) {
  return ({
    auto: "Filtre (auto)",
    off: "Arrêté",
    heatwave: "Canicule",
    manual_on: "Marche forcée",
    manual_off: "Arrêt forcé",
    water_low: "Niveau d'eau bas",
  })[s] || s;
}

function fmtTime(state) {
  if (!state || !state.state || state.state === "unknown" || state.state === "unavailable") return "—";
  try {
    const d = new Date(state.state);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return state.state;
  }
}

function cell(icon, label, value) {
  return `
    <div class="cell">
      <ha-icon icon="${icon}"></ha-icon>
      <div class="cell-text">
        <span class="cell-label">${label}</span>
        <span class="cell-value">${value}</span>
      </div>
    </div>`;
}

function actionBtn(icon, label, _onclick, active) {
  return `
    <button class="action-btn ${active ? "active" : ""}" title="${label}">
      <ha-icon icon="${icon}"></ha-icon>
      <span>${label}</span>
    </button>`;
}

const STYLES = `
  :host {
    display: block;
  }
  ha-card {
    padding: 16px;
    display: block;
  }
  .card {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .header {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .header ha-icon {
    --mdc-icon-size: 22px;
    color: var(--primary-color);
  }
  .title {
    font-size: 16px;
    font-weight: 600;
    flex-grow: 1;
  }
  .badge {
    background: #ff7043;
    color: white;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .badge.heatwave {
    animation: pulse 2s ease-in-out infinite;
  }
  .mode-pill {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    background: var(--secondary-background-color);
    color: var(--primary-text-color);
  }
  .mode-pill.mode-on   { background: #2196f3; color: white; }
  .mode-pill.mode-auto { background: #4caf50; color: white; }
  .mode-pill.mode-off  { background: #757575; color: white; }
  .visual {
    border-radius: 12px;
    overflow: hidden;
    background: var(--secondary-background-color);
    padding: 8px;
  }
  .visual svg {
    display: block;
    width: 100%;
    height: auto;
  }
  .visual.running svg ellipse,
  .visual.running svg circle,
  .visual.running svg rect[fill^="url"] {
    animation: gentle-shimmer 4s ease-in-out infinite;
  }
  .no-svg {
    padding: 24px;
    text-align: center;
    color: var(--secondary-text-color);
    font-size: 13px;
  }
  .schedule {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
    gap: 8px;
  }
  .cell {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--secondary-background-color);
    padding: 8px 10px;
    border-radius: 10px;
  }
  .cell ha-icon {
    --mdc-icon-size: 18px;
    color: var(--secondary-text-color);
    flex-shrink: 0;
  }
  .cell-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .cell-label {
    font-size: 10px;
    color: var(--secondary-text-color);
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  .cell-value {
    font-size: 13px;
    font-weight: 600;
    color: var(--primary-text-color);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .actions {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
  }
  .action-btn {
    background: var(--secondary-background-color);
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 10px 4px;
    cursor: pointer;
    color: var(--primary-text-color);
    font-size: 11px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    transition: background 0.15s, transform 0.1s;
  }
  .action-btn:hover {
    background: var(--primary-color);
    color: white;
  }
  .action-btn:active {
    transform: scale(0.96);
  }
  .action-btn.active {
    background: var(--primary-color);
    color: white;
  }
  .action-btn ha-icon {
    --mdc-icon-size: 20px;
  }
  .error {
    padding: 16px;
    color: var(--error-color);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .loading {
    padding: 24px;
    text-align: center;
    color: var(--secondary-text-color);
  }
  .placeholder {
    padding: 32px 16px;
    text-align: center;
    color: var(--secondary-text-color);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
  .placeholder ha-icon {
    --mdc-icon-size: 36px;
    color: var(--primary-color);
  }
  .placeholder-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--primary-text-color);
  }
  .placeholder-subtitle {
    font-size: 12px;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }
  @keyframes gentle-shimmer {
    0%, 100% { filter: brightness(1); }
    50%      { filter: brightness(1.08); }
  }
`;

// Guard double-define (HA's scoped-custom-element-registry sometimes
// invokes the module twice — once globally and once scoped to the
// dashboard panel). Without this guard, the second call throws a
// DOMException and kills the rest of the script's execution.
if (!customElements.get("pool-pump-card")) {
  customElements.define("pool-pump-card", PoolPumpCard);
}

// Register with HA's card picker so it shows up in "Add card" search.
window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "pool-pump-card")) {
  window.customCards.push({
    type: "pool-pump-card",
    name: "Pool Pump Card",
    description: "Visuel + contrôles pour ta piscine (Pool Pump Manager)",
    preview: true,
    documentationURL: "https://github.com/Shad107/ha-pool_pump",
  });
}

console.info(
  `%c POOL-PUMP-CARD %c v${CARD_VERSION} `,
  "color: white; background: #2196f3; font-weight: 700;",
  "color: #2196f3; background: white; font-weight: 700;"
);
