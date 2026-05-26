/**
 * Visual editor for Pool Pump Card.
 *
 * Renders ha-form (HA's built-in dynamic form) bound to the card config
 * schema. Picks the right entities by domain.
 */

class PoolPumpCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (e) => this._onChange(e));
      this.shadowRoot.appendChild(this._form);
    }
    if (!this._hass || !this._config) return;

    this._form.hass = this._hass;
    this._form.data = this._config;
    this._form.schema = [
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
    this._form.computeLabel = (s) =>
      ({
        title: "Titre (optionnel)",
        pool_entity: "Capteur de la piscine (sensor)",
        mode_entity: "Sélecteur de mode (select)",
        pump_switch: "Switch pompe (optionnel, lien direct)",
        electrolyzer_switch: "Switch électrolyseur (optionnel, lien direct)",
      })[s] || s;
  }

  _onChange(e) {
    if (!this._config) return;
    const next = e.detail.value;
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

customElements.define("pool-pump-card-editor", PoolPumpCardEditor);
