/**
 * Visual editor for Pool Pump Card.
 *
 * Renders ha-form (HA's built-in dynamic form) bound to the card config
 * schema. Picks the right entities by domain and filters by integration.
 */

const LABELS = {
  title: "Titre (optionnel)",
  pool_entity: "Capteur de la piscine (sensor)",
  mode_entity: "Sélecteur de mode (select)",
  pump_switch: "Switch pompe (optionnel)",
  electrolyzer_switch: "Switch électrolyseur (optionnel)",
};

const SCHEMA = [
  { name: "title", selector: { text: {} } },
  {
    name: "pool_entity",
    required: true,
    selector: {
      entity: { domain: "sensor", filter: { integration: "pool_pump" } },
    },
  },
  {
    name: "mode_entity",
    selector: {
      entity: { domain: "select", filter: { integration: "pool_pump" } },
    },
  },
  {
    name: "pump_switch",
    selector: { entity: { domain: "switch" } },
  },
  {
    name: "electrolyzer_switch",
    selector: { entity: { domain: "switch" } },
  },
];

function computeLabel(schema) {
  // ha-form's computeLabel passes the FULL schema entry (an object),
  // not a string. We need to pull schema.name; the previous version
  // treated it as a string and produced "[object Object]" labels.
  if (!schema || typeof schema !== "object") return String(schema ?? "");
  return LABELS[schema.name] || schema.name;
}


class PoolPumpCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...(config || {}) };
    if (this._form) {
      this._form.data = this._config;
    } else {
      this._tryRender();
    }
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) {
      this._form.hass = hass;
    } else {
      this._tryRender();
    }
  }

  _tryRender() {
    if (this._rendered || !this._hass || !this._config) return;

    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }

    this._form = document.createElement("ha-form");
    this._form.hass = this._hass;
    this._form.data = this._config;
    this._form.schema = SCHEMA;
    this._form.computeLabel = computeLabel;
    this._form.addEventListener("value-changed", (e) => this._onChange(e));

    this.shadowRoot.innerHTML = "";
    this.shadowRoot.appendChild(this._form);
    this._rendered = true;
  }

  _onChange(e) {
    if (!this._config) return;
    const next = e.detail.value;
    // Skip no-op value-changed events to prevent re-render loops.
    if (JSON.stringify(next) === JSON.stringify(this._config)) return;
    this._config = next;
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: next },
        bubbles: true,
        composed: true,
      })
    );
  }
}

if (!customElements.get("pool-pump-card-editor")) {
  customElements.define("pool-pump-card-editor", PoolPumpCardEditor);
}
