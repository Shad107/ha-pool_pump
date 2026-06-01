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

const CARD_VERSION = "0.13.0";

const HA_TEMPLATE_RE = /^(\w+)\.(\w+)$/;

class PoolPumpCard extends HTMLElement {
  static async getStubConfig(hass) {
    // Suggest the first pool entity found from the running integration.
    const candidates = Object.keys(hass.states).filter(
      (id) =>
        id.startsWith("sensor.") &&
        id.includes("pool_pump_manager") &&
        (id.endsWith("_piscine") || id.endsWith("_pool"))
    );

    const stub = {
      type: "custom:pool-pump-card",
      pool_entity: candidates[0] || "sensor.pool_pump_manager_piscine",
    };

    // Pre-fill pump_switch / electrolyzer_switch from the integration's
    // config entry so the user doesn't have to re-enter what they already
    // configured. Best-effort: ignore if the WS call fails (offline, no
    // entry, permissions…).
    try {
      const entries = await hass.callWS({ type: "config_entries/get" });
      const entry = entries.find((e) => e.domain === "pool_pump");
      if (entry) {
        const opts = { ...(entry.data || {}), ...(entry.options || {}) };
        if (opts.pump_switch) stub.pump_switch = opts.pump_switch;
        if (opts.electrolyzer_switch) {
          stub.electrolyzer_switch = opts.electrolyzer_switch;
        }
      }
    } catch (_) {
      // ignore — the picker still works without the pre-fill
    }

    return stub;
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
      power_entity: config.power_entity ?? this._derive(config.pool_entity, "sensor", "puissance_actuelle", "current_power"),
      energy_today_entity: config.energy_today_entity ?? this._derive(config.pool_entity, "sensor", "energie_aujourd_hui", "energy_today"),
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
    const modeTimes = (status && status.attributes && status.attributes.mode_time_today) || {};
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
    const imageUrl = pool.attributes.image_url || pool.attributes.bundled_url || null;
    const title = c.title ?? pool.state ?? "Pool";
    const modeState = mode ? mode.state : "auto";

    // Compact schedule line
    const tempVal = temp ? parseFloat(temp.state) : null;
    const tempStr = tempVal != null ? `${tempVal.toFixed(1)}°C` : "—";
    const tempTone = tempToneFor(tempVal);
    const power = this._state(this._pick(c.power_entity));
    const energy = this._state(this._pick(c.energy_today_entity));
    const powerVal = power ? parseFloat(power.state).toFixed(0) : null;
    const energyVal = energy ? parseFloat(energy.state).toFixed(2) : null;
    const startStr = fmtTime(start);
    const endStr = fmtTime(end);
    const durStr = duration ? `${parseFloat(duration.state).toFixed(1)}h` : "—";
    const statusStr = status ? statusLabel(status.state) : "—";

    this._root.innerHTML = `
      <div class="card">
        <div class="header">
          <div class="header-left">
            <ha-icon icon="mdi:pool"></ha-icon>
            <span class="title">${title}</span>
          </div>
          <div class="header-right">
            ${heatwave && heatwave.state === "on" ? `<span class="badge heatwave">🔥 CANICULE</span>` : ""}
            <span class="mode-pill mode-${modeState}" title="Mode actuel">${modeLabel(modeState)}</span>
          </div>
        </div>

        <div class="visual ${pumpTarget && pumpTarget.state === "on" ? "running" : ""}">
          ${imageUrl
            ? `<img class="pool-img" src="${imageUrl}" alt="Pool" />`
            : (svg || `<div class="no-svg">No preset selected — pick a pool model in the integration options.</div>`)}
          <div class="hero-overlay">
            <div class="hero-temp ${tempTone}" data-entity="${this._pick(c.temperature_entity) || ""}">
              <span class="hero-temp-value">${tempStr}</span>
              <span class="hero-temp-label">T° eau</span>
            </div>
            <div class="hero-status" data-entity="${this._pick(c.status_entity) || ""}">
              <span class="hero-status-value">${statusStr}</span>
              ${powerVal != null ? `<span class="hero-status-meta">⚡ ${powerVal} W${energyVal != null ? ` · ${energyVal} kWh` : ""}</span>` : ""}
            </div>
          </div>
        </div>

        ${this._renderTimeline(status)}

        <div class="schedule-strip">
          <span class="strip-item"><ha-icon icon="mdi:clock-start"></ha-icon>${startStr}</span>
          <span class="strip-sep">→</span>
          <span class="strip-item"><ha-icon icon="mdi:clock-end"></ha-icon>${endStr}</span>
          <span class="strip-sep">·</span>
          <span class="strip-item"><ha-icon icon="mdi:timer-sand"></ha-icon>${durStr}</span>
        </div>

        <div class="actions actions-modes">
          ${actionBtn("mdi:autorenew",   "Auto",        null, modeState === "auto",      modeTimes.auto,      "tone-auto")}
          ${actionBtn("mdi:play",        "Marche",      null, modeState === "on",        modeTimes.on,        "tone-on")}
          ${actionBtn("mdi:water-pump",  "Pompe seule", null, modeState === "pump_only", modeTimes.pump_only, "tone-pump-only")}
          ${actionBtn("mdi:stop",        "Arrêt",       null, modeState === "off",       modeTimes.off,       "tone-off")}
        </div>

        <div class="actions actions-utils">
          ${actionBtn("mdi:auto-fix",    "Routines",    null, false,                       null,                 "tone-util")}
          ${actionBtn("mdi:test-tube",   "Chimie",      null, modeState === "maintenance", modeTimes.maintenance, "tone-util")}
          ${actionBtn("mdi:filter",      "Backwash",    null, false,                       null,                 "tone-util")}
          ${actionBtn("mdi:refresh",     "Refresh",     null, false,                       null,                 "tone-util")}
        </div>
      </div>
    `;

    // Bind the buttons. New layout: modes row (Auto/Marche/Pompe/Arrêt)
    // followed by utils row (Routines/Chimie/Backwash/Refresh).
    const btns = this._root.querySelectorAll(".action-btn");
    btns[0].onclick = () => this._setMode("auto");
    btns[1].onclick = () => this._setMode("on");
    btns[2].onclick = () => this._setMode("pump_only");
    btns[3].onclick = () => this._setMode("off");
    btns[4].onclick = () => this._openRoutines();
    btns[5].onclick = () => this._openMaintenance();
    btns[6].onclick = () => this._backwash();
    btns[7].onclick = () => this._refresh();

    // Bind tap-to-more-info on each schedule cell that has data-entity
    this._root.querySelectorAll("[data-entity]").forEach((el) => {
      el.style.cursor = "pointer";
      el.onclick = () => this._openMoreInfo(el.getAttribute("data-entity"));
    });
  }

  _renderTimeline(status) {
    if (!status || !status.attributes || !status.attributes.runs) return "";
    const runs = status.attributes.runs;
    if (!runs.length) return "";

    const now = new Date();
    const startOfDay = new Date(now);
    startOfDay.setHours(0, 0, 0, 0);
    const dayMs = 24 * 3600 * 1000;
    const nowPct = Math.max(0, Math.min(100, ((now - startOfDay) / dayMs) * 100));

    let runsHtml = "";
    runs.forEach((r) => {
      try {
        const s = new Date(r.start);
        const e = new Date(r.end);
        const sPct = Math.max(0, ((s - startOfDay) / dayMs) * 100);
        const ePct = Math.min(100, ((e - startOfDay) / dayMs) * 100);
        const w = Math.max(0, ePct - sPct);
        if (w > 0) {
          runsHtml += `<div class="timeline-run" style="left:${sPct}%; width:${w}%" title="${fmtTimeLabel(s)} → ${fmtTimeLabel(e)}"></div>`;
        }
      } catch (_) {
        // ignore malformed run
      }
    });

    const fc = status.attributes.forecast_temperature_max_24h;
    const fcCond = status.attributes.forecast_condition;
    const learnedOffset = status.attributes.learned_temperature_offset;
    const calPoints = status.attributes.calibration_points;
    let extras = [];
    if (fc !== null && fc !== undefined) {
      const icon = forecastIcon(fcCond);
      extras.push(
        `<span title="T° max prévue 24h">${icon} ${parseFloat(fc).toFixed(1)}°C</span>`
      );
    }
    if (calPoints && learnedOffset !== undefined && learnedOffset !== null) {
      const sign = learnedOffset >= 0 ? "+" : "";
      extras.push(
        `<span title="Offset appris (${calPoints} calibration${calPoints > 1 ? "s" : ""})">⚖ ${sign}${parseFloat(learnedOffset).toFixed(2)}°C</span>`
      );
    }
    const extrasHtml = extras.length
      ? `<div class="timeline-extras">${extras.join("")}</div>`
      : "";

    return `
      <div class="timeline">
        <div class="timeline-bar">
          ${runsHtml}
          <div class="timeline-now" style="left:${nowPct}%" title="Maintenant"></div>
        </div>
        <div class="timeline-labels">
          <span>0h</span><span>6h</span><span>12h</span><span>18h</span><span>24h</span>
        </div>
        ${extrasHtml}
      </div>
    `;
  }

  _powerCells(c) {
    const power = this._state(this._pick(c.power_entity));
    const energy = this._state(this._pick(c.energy_today_entity));
    if (!power && !energy) return "";
    const out = [];
    if (power) {
      out.push(cell("mdi:flash", "Puissance",
        `${parseFloat(power.state).toFixed(0)} W`,
        this._pick(c.power_entity)));
    }
    if (energy) {
      out.push(cell("mdi:lightning-bolt", "Énergie j.",
        `${parseFloat(energy.state).toFixed(2)} kWh`,
        this._pick(c.energy_today_entity)));
    }
    return out.join("");
  }

  _openMoreInfo(entityId) {
    if (!entityId || !this._hass) return;
    const event = new CustomEvent("hass-more-info", {
      detail: { entityId },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
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

  _backwash() {
    if (!this._hass) return;
    if (confirm("Lancer un backwash filtre ? (pompe ON + cellule OFF pendant la durée configurée)")) {
      this._hass.callService("pool_pump", "backwash", {});
    }
  }

  _openRoutines() {
    if (!this._hass) return;
    const c = this._config;
    const status = this._state(this._pick(c.status_entity));
    if (!status || !status.attributes) {
      alert("Sensor de statut indisponible.");
      return;
    }
    const routines = status.attributes.available_routines || [];
    const recos = status.attributes.chemistry_recommendations || [];
    const active = status.attributes.active_routine;

    let modal = this.shadowRoot.querySelector(".pp-modal");
    if (modal) modal.remove();

    modal = document.createElement("div");
    modal.className = "pp-modal";
    modal.innerHTML = renderRoutinesModal(routines, recos, active);
    this.shadowRoot.appendChild(modal);

    modal.querySelector(".pp-modal-close").onclick = () => modal.remove();
    modal.querySelector(".pp-modal-backdrop").onclick = () => modal.remove();

    // Toggle "Plus" expand
    const moreBtn = modal.querySelector(".pp-routines-more");
    const moreList = modal.querySelector(".pp-routines-more-list");
    if (moreBtn && moreList) {
      moreBtn.onclick = () => {
        const open = moreList.style.display === "grid";
        moreList.style.display = open ? "none" : "grid";
        moreBtn.textContent = open ? "⋮ Plus" : "▲ Moins";
      };
    }

    // Routine apply buttons
    modal.querySelectorAll("[data-routine-key]").forEach((btn) => {
      btn.onclick = () => {
        const key = btn.dataset.routineKey;
        const r = routines.find((x) => x.key === key);
        if (!r) return;
        const reco = r.smart
          ? recos.find((x) => x.issue_key && x.issue_key.startsWith(routineSmartPrefix(key)))
          : null;
        const dose = reco
          ? (reco.dose_g ? `${reco.dose_g.toFixed(0)} g de ${reco.product}`
                         : reco.dose_ml ? `${reco.dose_ml.toFixed(0)} mL de ${reco.product}`
                         : reco.product)
          : null;
        const dur = (reco && reco.pump_duration_min) || r.default_min;
        const msg = dose
          ? `${r.label} :\n→ ${dose}\n→ pompe ${fmtHours(dur)} puis retour Auto\n\nLancer ?`
          : `${r.label} :\n→ ${r.smart ? "(aucune mesure récente, dose par défaut)\n" : ""}→ pompe ${fmtHours(dur)} puis retour Auto\n\nLancer ?`;
        if (confirm(msg)) {
          this._hass.callService("pool_pump", "start_routine", { routine_key: key });
          modal.remove();
        }
      };
    });

    // Cancel active routine
    const cancelBtn = modal.querySelector(".pp-routine-cancel");
    if (cancelBtn) {
      cancelBtn.onclick = () => {
        this._hass.callService("pool_pump", "maintenance_cancel", {});
        modal.remove();
      };
    }
  }

  _openMaintenance() {
    if (!this._hass) return;
    const c = this._config;
    const status = this._state(this._pick(c.status_entity));
    if (!status || !status.attributes) {
      alert("Sensor de statut indisponible — vérifie la config de la card.");
      return;
    }
    const chemistry = status.attributes.chemistry || [];
    const recos = status.attributes.chemistry_recommendations || [];

    // Build modal DOM in the shadow root.
    let modal = this.shadowRoot.querySelector(".pp-modal");
    if (modal) modal.remove();

    modal = document.createElement("div");
    modal.className = "pp-modal";
    modal.innerHTML = renderMaintenanceModal(chemistry, recos);
    this.shadowRoot.appendChild(modal);

    // Close handlers
    modal.querySelector(".pp-modal-close").onclick = () => modal.remove();
    modal.querySelector(".pp-modal-backdrop").onclick = () => modal.remove();

    // Save chemistry handler
    modal.querySelector(".pp-save-chem").onclick = () => {
      const payload = {};
      modal.querySelectorAll("[data-chem-key]").forEach((el) => {
        const v = parseFloat(el.value);
        if (!Number.isNaN(v)) payload[el.dataset.chemKey] = v;
      });
      if (Object.keys(payload).length === 0) {
        alert("Aucune valeur à enregistrer.");
        return;
      }
      this._hass.callService("pool_pump", "set_chemistry", payload);
      modal.remove();
    };

    // Recommendation apply buttons
    modal.querySelectorAll("[data-apply-action]").forEach((btn) => {
      btn.onclick = () => {
        const dur = parseInt(btn.dataset.applyDuration, 10) || 180;
        const action = btn.dataset.applyAction;
        if (action === "maintenance") {
          this._hass.callService("pool_pump", "maintenance_start", {
            duration_minutes: dur,
          });
          modal.remove();
        }
      };
    });
  }

  getCardSize() {
    return 4;
  }
}

function modeLabel(s) {
  return ({
    auto: "Auto",
    on: "Marche",
    off: "Arrêt",
    pump_only: "Pompe seule",
  })[s] || s;
}

function statusLabel(s) {
  return ({
    auto: "Filtre (auto)",
    off: "Arrêté",
    heatwave: "Canicule",
    manual_on: "Marche forcée",
    manual_off: "Arrêt forcé",
    water_low: "Niveau d'eau bas",
    pump_only: "Pompe seule",
    backwash: "Backwash",
    winterization: "Hivernage",
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

function fmtTimeLabel(d) {
  try {
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function forecastIcon(cond) {
  const map = {
    sunny: "☀",
    clear: "☀",
    "clear-night": "☾",
    cloudy: "☁",
    partlycloudy: "⛅",
    fog: "🌫",
    rainy: "🌧",
    pouring: "🌧",
    snowy: "❄",
    lightning: "⛈",
    "lightning-rainy": "⛈",
    windy: "🌬",
    hail: "🌨",
  };
  return map[cond] || "🌤";
}

function cell(icon, label, value, entityId) {
  const dataAttr = entityId ? ` data-entity="${entityId}"` : "";
  return `
    <div class="cell"${dataAttr}>
      <ha-icon icon="${icon}"></ha-icon>
      <div class="cell-text">
        <span class="cell-label">${label}</span>
        <span class="cell-value">${value}</span>
      </div>
    </div>`;
}

function routineSmartPrefix(key) {
  return ({
    shock_chlorine: "free_chlorine_",
    ph_adjust: "ph_",
    tac_adjust: "tac_",
    stabilizer_dissolve: "cya_",
  })[key] || "";
}

function fmtHours(min) {
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m === 0 ? `${h}h` : `${h}h${String(m).padStart(2, "0")}`;
}

function renderRoutineCard(r, recos) {
  const reco = r.smart
    ? recos.find((x) => x.issue_key && x.issue_key.startsWith(routineSmartPrefix(r.key)))
    : null;
  const applicable = !r.smart || reco !== undefined && reco !== null;
  const dose = reco
    ? (reco.dose_g ? `${reco.dose_g.toFixed(0)} g`
                   : reco.dose_ml ? `${reco.dose_ml.toFixed(0)} mL`
                   : "")
    : (r.smart ? "(pas de mesure récente)" : "");
  const dur = (reco && reco.pump_duration_min) || r.default_min;
  return `
    <button class="pp-routine-card ${applicable ? '' : 'pp-routine-na'}"
            data-routine-key="${r.key}"
            title="${applicable ? '' : 'Calculé sur tes dernières mesures chimie'}">
      <div class="pp-routine-label">${r.label}${r.smart ? ' <span class="pp-smart-tag">auto</span>' : ''}</div>
      <div class="pp-routine-sub">
        ${dose ? `<span>${dose}</span>` : ''}
        <span>pompe ${fmtHours(dur)}</span>
      </div>
    </button>`;
}

function renderRoutinesModal(routines, recos, active) {
  const favs = routines.filter((r) => r.favorite);
  const more = routines.filter((r) => !r.favorite);

  const activeBanner = active ? `
    <div class="pp-routine-active">
      <span>🟢 Routine <b>${active.key}</b> en cours · fin ${fmtTimeFromIso(active.ends_at)}</span>
      <button class="pp-routine-cancel">Annuler</button>
    </div>` : '';

  const favHtml = favs.map((r) => renderRoutineCard(r, recos)).join("");
  const moreHtml = more.map((r) => renderRoutineCard(r, recos)).join("");

  return `
    <div class="pp-modal-backdrop"></div>
    <div class="pp-modal-body">
      <div class="pp-modal-header">
        <span>🔧 Routines</span>
        <button class="pp-modal-close">✕</button>
      </div>
      ${activeBanner}
      <div class="pp-routines-fav">${favHtml}</div>
      <button class="pp-routines-more">⋮ Plus</button>
      <div class="pp-routines-more-list" style="display:none">${moreHtml}</div>
    </div>
  `;
}

function fmtTimeFromIso(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch { return "—"; }
}

function renderMaintenanceModal(chemistry, recos) {
  const sevColor = { critical: "#d32f2f", warning: "#f57c00", info: "#1976d2" };
  const statusColor = { ok: "#4caf50", low: "#f57c00", high: "#d32f2f", unknown: "#9e9e9e" };

  const rows = chemistry.map((c) => {
    const dot = `<span class="pp-status-dot" style="background:${statusColor[c.status]}"></span>`;
    const tgt = `cible ${c.target_low}–${c.target_high}`;
    const cur = c.value === null ? "" : `value="${c.value}"`;
    return `
      <div class="pp-chem-row">
        <div class="pp-chem-label">${dot}<span>${c.label}</span>
          <span class="pp-chem-target">${tgt} ${c.unit}</span>
        </div>
        <input type="number" step="0.1" ${cur} data-chem-key="${c.key}"
               placeholder="—" class="pp-chem-input"/>
        <span class="pp-chem-unit">${c.unit}</span>
      </div>`;
  }).join("");

  const recoBlocks = recos.length === 0
    ? `<div class="pp-no-reco">✅ Tout est dans les clous. Continue en mode Auto.</div>`
    : recos.map((r) => {
        const sev = sevColor[r.severity] || "#666";
        const dose = r.dose_g ? `${r.dose_g.toFixed(0)} g` :
                     r.dose_ml ? `${r.dose_ml.toFixed(0)} mL` : "—";
        const applyBtn = r.pump_action === "maintenance"
          ? `<button class="pp-apply-btn" data-apply-action="maintenance"
                     data-apply-duration="${r.pump_duration_min}">
               Pompe ${(r.pump_duration_min / 60).toFixed(1)}h
             </button>`
          : "";
        return `
          <div class="pp-reco" style="border-left-color:${sev}">
            <div class="pp-reco-title">${r.title}</div>
            <div class="pp-reco-product">→ ${r.product} : <b>${dose}</b></div>
            ${r.notes ? `<div class="pp-reco-notes">${r.notes}</div>` : ""}
            ${applyBtn}
          </div>`;
      }).join("");

  return `
    <div class="pp-modal-backdrop"></div>
    <div class="pp-modal-body">
      <div class="pp-modal-header">
        <span>🧪 Maintenance chimie</span>
        <button class="pp-modal-close">✕</button>
      </div>
      <div class="pp-modal-section">
        <div class="pp-section-title">Saisie / lecture</div>
        ${rows}
        <button class="pp-save-chem">Enregistrer & diagnostiquer</button>
      </div>
      <div class="pp-modal-section">
        <div class="pp-section-title">Recommandations</div>
        ${recoBlocks}
      </div>
    </div>
  `;
}

function actionBtn(icon, label, _onclick, active, seconds, tone) {
  const time = seconds != null && seconds > 0
    ? `<span class="btn-time">${fmtSeconds(seconds)}</span>`
    : "";
  const cls = ["action-btn"];
  if (active) cls.push("active");
  if (tone) cls.push(tone);
  return `
    <button class="${cls.join(" ")}" title="${label}">
      <ha-icon icon="${icon}"></ha-icon>
      <span class="btn-label">${label}</span>
      ${time}
    </button>`;
}

function tempToneFor(t) {
  if (t == null) return "tone-neutral";
  if (t < 15) return "tone-cold";       // cellule bloquée par le bas
  if (t < 22) return "tone-cool";       // baignade fraîche
  if (t <= 30) return "tone-comfort";   // zone confort
  if (t <= 35) return "tone-warm";      // chaud
  return "tone-hot";                    // limite haute cellule
}

function fmtSeconds(sec) {
  if (sec < 60) return `${Math.floor(sec)}s`;
  const totalMin = Math.floor(sec / 60);
  if (totalMin < 60) return `${totalMin} min`;
  const h = Math.floor(totalMin / 60);
  const m = totalMin % 60;
  return m === 0 ? `${h}h` : `${h}h${String(m).padStart(2, "0")}`;
}

const STYLES = `
  :host {
    --pp-blue: #03a9f4;
    --pp-blue-deep: #0277bd;
    --pp-green: #43a047;
    --pp-amber: #fb8c00;
    --pp-red: #e53935;
    --pp-purple: #8e24aa;
    --pp-bg-tint: rgba(3, 169, 244, 0.06);
    display: block;
  }
  ha-card {
    padding: 14px;
    display: block;
  }
  .card {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  /* ---------- Header ---------- */
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-wrap: wrap;
  }
  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex: 1;
  }
  .header-right {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .header ha-icon {
    --mdc-icon-size: 22px;
    color: var(--pp-blue);
  }
  .title {
    font-size: 16px;
    font-weight: 700;
    color: var(--primary-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .badge {
    color: white;
    padding: 3px 9px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.4px;
  }
  .badge.heatwave {
    background: linear-gradient(135deg, #ff6f00 0%, #f4511e 100%);
    box-shadow: 0 2px 6px rgba(244, 81, 30, 0.35);
    animation: pulse 2.4s ease-in-out infinite;
  }
  .mode-pill {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.3px;
    color: white;
    background: rgba(127,127,127,0.4);
  }
  .mode-pill.mode-auto         { background: linear-gradient(135deg, #43a047, #2e7d32); }
  .mode-pill.mode-on           { background: linear-gradient(135deg, #1e88e5, #1565c0); }
  .mode-pill.mode-pump_only    { background: linear-gradient(135deg, #fb8c00, #e65100); }
  .mode-pill.mode-off          { background: linear-gradient(135deg, #757575, #424242); }
  .mode-pill.mode-maintenance  { background: linear-gradient(135deg, #8e24aa, #5e35b1); }
  /* ---------- Visual (pool image + hero stats) ---------- */
  .visual {
    border-radius: 14px;
    overflow: hidden;
    background: linear-gradient(180deg, #e1f5fe 0%, #b3e5fc 100%);
    padding: 8px;
    position: relative;
    box-shadow: inset 0 0 0 1px rgba(3, 169, 244, 0.15);
  }
  .visual svg, .visual .pool-img {
    display: block;
    width: 100%;
    height: auto;
    border-radius: 10px;
  }
  .hero-overlay {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding: 8px 6px 2px 6px;
    gap: 8px;
  }
  .hero-temp {
    display: flex;
    flex-direction: column;
    line-height: 1;
    cursor: pointer;
    padding: 6px 10px;
    border-radius: 10px;
    background: rgba(255,255,255,0.7);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
  }
  .hero-temp-value {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.5px;
  }
  .hero-temp-label {
    font-size: 10px;
    text-transform: uppercase;
    color: var(--secondary-text-color);
    margin-top: 2px;
    letter-spacing: 0.4px;
  }
  .hero-temp.tone-cold    .hero-temp-value { color: #1565c0; }
  .hero-temp.tone-cool    .hero-temp-value { color: #0288d1; }
  .hero-temp.tone-comfort .hero-temp-value { color: #00897b; }
  .hero-temp.tone-warm    .hero-temp-value { color: #ef6c00; }
  .hero-temp.tone-hot     .hero-temp-value { color: #c62828; }
  .hero-temp.tone-neutral .hero-temp-value { color: var(--primary-text-color); }

  .hero-status {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    text-align: right;
    cursor: pointer;
    padding: 6px 10px;
    border-radius: 10px;
    background: rgba(255,255,255,0.7);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
  }
  .hero-status-value {
    font-size: 13px;
    font-weight: 700;
    color: var(--pp-blue-deep);
  }
  .hero-status-meta {
    font-size: 11px;
    color: var(--secondary-text-color);
    margin-top: 2px;
  }
  .visual.running .pool-img {
    animation: gentle-shimmer 4s ease-in-out infinite;
    transform-origin: center;
  }
  /* Animate only the water shape — earlier rect[fill^="url"] was too
     broad and made the wooden deck pulse too. The new SVG always tags
     the water shape with class="pool-water" so the selector is exact. */
  .visual.running svg .pool-water {
    animation: gentle-shimmer 4s ease-in-out infinite;
    transform-origin: center;
    transform-box: fill-box;
  }
  /* Water-flow sweep: a soft gradient slides across the pool visual
     whenever the pump is running. The overlay is positioned over the
     whole visual box and only catches the eye thanks to the gradient's
     narrow band; pointer-events none so it never blocks clicks. */
  .visual.running::after {
    content: "";
    position: absolute;
    inset: 8px;
    border-radius: 8px;
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.12) 45%,
      rgba(255, 255, 255, 0.20) 50%,
      rgba(255, 255, 255, 0.12) 55%,
      transparent 100%
    );
    background-size: 200% 100%;
    animation: water-flow 5s linear infinite;
    pointer-events: none;
    mix-blend-mode: screen;
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
  /* ---------- Action rows ---------- */
  .actions {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
  }
  .actions-utils {
    margin-top: -2px;
  }
  .action-btn {
    background: var(--secondary-background-color);
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 10px 4px;
    cursor: pointer;
    color: var(--primary-text-color);
    font-size: 11px;
    font-weight: 600;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    transition: transform 0.1s, box-shadow 0.15s, background 0.15s;
  }
  .action-btn ha-icon {
    --mdc-icon-size: 20px;
    color: var(--secondary-text-color);
    transition: color 0.15s;
  }
  .action-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.10);
  }
  .action-btn:active {
    transform: scale(0.96);
  }
  .btn-label { letter-spacing: 0.2px; }
  .btn-time {
    font-size: 9px;
    font-weight: 600;
    opacity: 0.72;
    margin-top: 0;
    letter-spacing: 0.2px;
  }

  /* Mode-row tones (only colorize on hover; active gets full color) */
  .action-btn.tone-auto:hover       ha-icon { color: var(--pp-green); }
  .action-btn.tone-on:hover         ha-icon { color: var(--pp-blue); }
  .action-btn.tone-pump-only:hover  ha-icon { color: var(--pp-amber); }
  .action-btn.tone-off:hover        ha-icon { color: var(--pp-red); }

  .action-btn.active.tone-auto {
    background: linear-gradient(135deg, rgba(67,160,71,0.18), rgba(46,125,50,0.10));
    border-color: rgba(67,160,71,0.45);
    color: #1b5e20;
  }
  .action-btn.active.tone-auto ha-icon { color: var(--pp-green); }
  .action-btn.active.tone-on {
    background: linear-gradient(135deg, rgba(30,136,229,0.18), rgba(21,101,192,0.10));
    border-color: rgba(30,136,229,0.45);
    color: #0d47a1;
  }
  .action-btn.active.tone-on ha-icon { color: var(--pp-blue); }
  .action-btn.active.tone-pump-only {
    background: linear-gradient(135deg, rgba(251,140,0,0.20), rgba(230,81,0,0.10));
    border-color: rgba(251,140,0,0.45);
    color: #bf360c;
  }
  .action-btn.active.tone-pump-only ha-icon { color: var(--pp-amber); }
  .action-btn.active.tone-off {
    background: linear-gradient(135deg, rgba(117,117,117,0.20), rgba(66,66,66,0.10));
    border-color: rgba(117,117,117,0.45);
    color: var(--primary-text-color);
  }
  .action-btn.active.tone-off ha-icon { color: var(--pp-red); }

  /* Utility row (less prominent) */
  .actions-utils .action-btn {
    background: transparent;
    border-color: rgba(127,127,127,0.20);
    font-size: 10.5px;
  }
  .actions-utils .action-btn ha-icon {
    --mdc-icon-size: 18px;
  }
  .actions-utils .action-btn.active {
    background: linear-gradient(135deg, rgba(142,36,170,0.16), rgba(94,53,177,0.10));
    border-color: rgba(142,36,170,0.45);
    color: #4a148c;
  }
  .actions-utils .action-btn.active ha-icon { color: var(--pp-purple); }
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
  /* ---------- Timeline ---------- */
  .timeline {
    background: var(--pp-bg-tint);
    padding: 10px 12px;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    border: 1px solid rgba(3,169,244,0.10);
  }
  .timeline-bar {
    position: relative;
    height: 12px;
    background: rgba(127, 127, 127, 0.18);
    border-radius: 6px;
    overflow: visible;
  }
  .timeline-run {
    position: absolute;
    top: 0;
    bottom: 0;
    background: linear-gradient(180deg, #66bb6a, #2e7d32);
    border-radius: 3px;
    box-shadow: 0 1px 4px rgba(46, 125, 50, 0.35);
  }
  .timeline-now {
    position: absolute;
    top: -3px;
    bottom: -3px;
    width: 2px;
    background: var(--pp-blue);
    border-radius: 1px;
    box-shadow: 0 0 8px var(--pp-blue);
  }
  .timeline-labels {
    display: flex;
    justify-content: space-between;
    font-size: 9px;
    color: var(--secondary-text-color);
    font-weight: 500;
  }
  .timeline-extras {
    display: flex;
    gap: 14px;
    font-size: 11px;
    color: var(--secondary-text-color);
    margin-top: 2px;
  }

  /* ---------- Compact schedule strip ---------- */
  .schedule-strip {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 12px;
    color: var(--secondary-text-color);
    padding: 6px 10px;
    background: rgba(127,127,127,0.06);
    border-radius: 10px;
  }
  .strip-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-weight: 600;
    color: var(--primary-text-color);
  }
  .strip-item ha-icon {
    --mdc-icon-size: 14px;
    color: var(--pp-blue);
  }
  .strip-sep {
    color: var(--secondary-text-color);
    opacity: 0.5;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }
  @keyframes gentle-shimmer {
    0%, 100% { filter: brightness(1); }
    50%      { filter: brightness(1.08); }
  }
  @keyframes water-flow {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  /* === Maintenance modal === */
  .pp-modal { position: fixed; inset: 0; z-index: 9999; display: flex;
    align-items: center; justify-content: center; }
  .pp-modal-backdrop { position: absolute; inset: 0;
    background: rgba(0, 0, 0, 0.55); }
  .pp-modal-body { position: relative; background: var(--card-background-color, white);
    color: var(--primary-text-color, #111); border-radius: 16px; padding: 20px;
    width: min(560px, 92vw); max-height: 88vh; overflow-y: auto;
    box-shadow: 0 24px 48px rgba(0,0,0,0.35); }
  .pp-modal-header { display: flex; justify-content: space-between;
    align-items: center; font-size: 18px; font-weight: 700; margin-bottom: 16px; }
  .pp-modal-close { background: none; border: none; font-size: 20px;
    cursor: pointer; color: var(--secondary-text-color); }
  .pp-modal-section { margin-bottom: 24px; }
  .pp-section-title { font-size: 12px; font-weight: 700;
    color: var(--secondary-text-color); text-transform: uppercase;
    letter-spacing: 0.5px; margin-bottom: 12px; }
  .pp-chem-row { display: grid;
    grid-template-columns: 1fr auto 30px; gap: 8px; align-items: center;
    padding: 8px 0; border-bottom: 1px solid rgba(127,127,127,0.15); }
  .pp-chem-label { display: flex; align-items: center; gap: 8px;
    font-size: 13px; }
  .pp-chem-target { color: var(--secondary-text-color); font-size: 11px;
    margin-left: 6px; }
  .pp-chem-input { width: 80px; padding: 6px 8px; border-radius: 6px;
    border: 1px solid rgba(127,127,127,0.3); font-size: 13px;
    text-align: right; background: var(--card-background-color, white);
    color: var(--primary-text-color, #111); }
  .pp-chem-unit { font-size: 11px; color: var(--secondary-text-color); }
  .pp-status-dot { display: inline-block; width: 10px; height: 10px;
    border-radius: 50%; }
  .pp-save-chem { margin-top: 14px; padding: 10px 16px; border-radius: 10px;
    background: var(--primary-color, #2196f3); color: white; border: none;
    cursor: pointer; font-weight: 600; font-size: 13px; width: 100%; }
  .pp-reco { border-left: 4px solid #1976d2; padding: 10px 14px;
    margin-bottom: 10px; background: rgba(127,127,127,0.08); border-radius: 8px; }
  .pp-reco-title { font-weight: 700; font-size: 13px; margin-bottom: 4px; }
  .pp-reco-product { font-size: 12px; margin-bottom: 4px; }
  .pp-reco-notes { font-size: 11px; color: var(--secondary-text-color);
    font-style: italic; margin-bottom: 8px; }
  .pp-apply-btn { padding: 6px 12px; border-radius: 6px;
    background: var(--primary-color, #2196f3); color: white; border: none;
    cursor: pointer; font-size: 12px; font-weight: 600; }
  .pp-no-reco { padding: 16px; text-align: center;
    color: var(--secondary-text-color); font-size: 13px; }

  /* Routines modal */
  .pp-routine-active { background: rgba(76, 175, 80, 0.15);
    border: 1px solid rgba(76, 175, 80, 0.5); padding: 10px 14px;
    border-radius: 10px; display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 16px; font-size: 12px; }
  .pp-routine-cancel { padding: 6px 12px; border-radius: 6px;
    background: rgba(0,0,0,0.1); color: inherit; border: none;
    cursor: pointer; font-size: 11px; font-weight: 600; }
  .pp-routines-fav, .pp-routines-more-list {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 8px; margin-bottom: 12px; }
  .pp-routine-card { padding: 12px; border-radius: 10px;
    background: rgba(127,127,127,0.1); border: 1px solid rgba(127,127,127,0.2);
    cursor: pointer; text-align: left; color: inherit;
    transition: background 0.15s, transform 0.1s; }
  .pp-routine-card:hover { background: rgba(33, 150, 243, 0.15); }
  .pp-routine-card:active { transform: scale(0.97); }
  .pp-routine-na { opacity: 0.55; }
  .pp-routine-label { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
  .pp-routine-sub { display: flex; flex-wrap: wrap; gap: 8px;
    font-size: 11px; color: var(--secondary-text-color); }
  .pp-smart-tag { background: var(--primary-color, #2196f3); color: white;
    padding: 1px 6px; border-radius: 4px; font-size: 9px; font-weight: 700;
    letter-spacing: 0.3px; vertical-align: middle; }
  .pp-routines-more { padding: 8px; border-radius: 8px; background: none;
    border: 1px dashed rgba(127,127,127,0.4); cursor: pointer;
    color: var(--secondary-text-color); font-size: 12px; width: 100%;
    margin-bottom: 8px; }
  .pp-routines-more:hover { background: rgba(127,127,127,0.08); }
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
