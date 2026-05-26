/**
 * Visual editor for Pool Pump Card — minimal.
 *
 * v0.5 only exposes a "title" override field. Every other config option
 * (pool_entity, mode_entity, pump_switch, electrolyzer_switch) is
 * auto-prefilled by the card's getStubConfig from the integration's
 * config entry, with prefix-based auto-detection as a second fallback.
 * Power users can still set advanced fields via the YAML code editor.
 */

const LABELS = {
  title: "Titre (optionnel) — laisse vide pour utiliser le nom du modèle",
};

const SCHEMA = [
  { name: "title", selector: { text: {} } },
];

function computeLabel(arg) {
  if (typeof arg === "string") return LABELS[arg] || arg;
  if (arg && typeof arg === "object") {
    const name = arg.name || (arg.schema && arg.schema.name);
    if (typeof name === "string") return LABELS[name] || name;
  }
  return "";
}


class PoolPumpCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...(config || {}) };
    if (this._form) this._form.data = this._config;
    else this._tryRender();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
    else this._tryRender();
  }

  _tryRender() {
    if (this._rendered || !this._hass || !this._config) return;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });

    this._form = document.createElement("ha-form");
    this._form.hass = this._hass;
    this._form.data = this._config;
    this._form.schema = SCHEMA;
    this._form.computeLabel = computeLabel;
    this._form.addEventListener("value-changed", (e) => this._onChange(e));

    this.shadowRoot.innerHTML = "";
    const help = document.createElement("div");
    help.style.cssText = "padding: 0 8px 12px; font-size: 12px; color: var(--secondary-text-color);";
    help.innerHTML = "ℹ️ Toute la config est auto-déduite de l'intégration. Le titre est optionnel. Pour des overrides avancés, utilise le bouton « SHOW CODE EDITOR » en haut.";
    this.shadowRoot.appendChild(help);
    this.shadowRoot.appendChild(this._form);
    this._rendered = true;
  }

  _onChange(e) {
    if (!this._config) return;
    const next = e.detail.value;
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
