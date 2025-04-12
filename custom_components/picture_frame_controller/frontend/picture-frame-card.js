import { LitElement, html, css } from "lit";
import { property } from "lit/decorators.js";

class PictureFrameCard extends LitElement {
  @property({ type: Object }) hass;
  @property({ type: Object }) config;
  @property({ type: String }) selectedImage = null;
  @property({ type: String }) albumName = null;
  @property({ type: String }) imageName = null;
  @property({ type: Number }) year = null;
  @property({ type: Number }) month = null;
  @property({ type: Array }) albums = [];
  @property({ type: Object }) activeFilters = {
    albumFilter: null,
    timeRange: {
      active: false,
      startYear: new Date().getFullYear() - 1,
      startMonth: 1,
      endYear: new Date().getFullYear(),
      endMonth: 12,
    },
  };

  static get styles() {
    return css`
      :host {
        display: block;
        padding: 16px;
      }
      .container {
        display: flex;
        flex-direction: column;
        width: 100%;
      }
      .image-container {
        position: relative;
        width: 100%;
        height: 0;
        padding-bottom: 75%; /* 4:3 Aspect Ratio */
        overflow: hidden;
        border-radius: 4px;
        margin-bottom: 16px;
      }
      .image-container img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: contain;
        background-color: #0000000a;
      }
      .controls {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
      }
      .info {
        margin-bottom: 16px;
      }
      .info-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
      }
      .button-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
      }
      .button {
        background-color: var(--primary-color);
        color: var(--text-primary-color);
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 14px;
        cursor: pointer;
        flex: 1;
        min-width: 120px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
      }
      .button:hover {
        background-color: var(--primary-color-light);
      }
      .button:active {
        background-color: var(--primary-color-dark);
      }
      .filter-section {
        border-top: 1px solid var(--divider-color);
        padding-top: 16px;
        margin-top: 8px;
      }
      .filter-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 8px;
      }
      .filter-section-title {
        font-weight: bold;
        margin-bottom: 8px;
      }
      select, input {
        flex: 1;
        min-width: 100px;
        padding: 8px;
        border-radius: 4px;
        border: 1px solid var(--divider-color);
      }
      .active-filter {
        background-color: var(--primary-color);
        color: var(--text-primary-color);
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 12px;
        margin-right: 8px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
      }
      .active-filter ha-icon {
        --mdc-icon-size: 14px;
        cursor: pointer;
      }
      .no-image {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
        color: var(--primary-text-color);
      }
      .active-filters {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        margin-top: 8px;
      }
    `;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity");
    }
    this.config = config;
  }

  getCardSize() {
    return 4;
  }

  firstUpdated() {
    this._fetchAlbums();
  }

  updated(changedProps) {
    if (changedProps.has("hass")) {
      this._updateData();
    }
  }

  _updateData() {
    const entity = this.config.entity;
    const stateObj = this.hass.states[entity];

    if (stateObj) {
      this.selectedImage = stateObj.state;
      this.albumName = stateObj.attributes.album_name || null;
      this.imageName = stateObj.attributes.image_name || null;
      this.year = stateObj.attributes.year || null;
      this.month = stateObj.attributes.month || null;
    }
  }

  _fetchAlbums() {
    // In a real implementation, we would fetch albums from the backend
    // For now, we'll use a simple discovery mechanism based on available states
    const albums = [];
    const visitedAlbums = new Set();

    for (const entityId in this.hass.states) {
      if (entityId.startsWith("sensor.picture_frame_controller_")) {
        const stateObj = this.hass.states[entityId];
        const albumName = stateObj.attributes.album_name;
        
        if (albumName && !visitedAlbums.has(albumName)) {
          visitedAlbums.add(albumName);
          albums.push({
            name: albumName,
            year: stateObj.attributes.year,
            month: stateObj.attributes.month,
          });
        }
      }
    }

    // Sort albums by year, month, name
    this.albums = albums.sort((a, b) => {
      if (a.year !== b.year && a.year && b.year) {
        return b.year - a.year;
      }
      if (a.month !== b.month && a.month && b.month) {
        return b.month - a.month;
      }
      return a.name.localeCompare(b.name);
    });
  }

  _renderImage() {
    if (!this.selectedImage || this.selectedImage === "unknown" || this.selectedImage === "None") {
      return html`
        <div class="image-container">
          <div class="no-image">No image selected</div>
        </div>
      `;
    }

    const isVideo = [".mp4", ".mov", ".avi", ".mkv", ".webm"].some(ext => 
      this.selectedImage.toLowerCase().endsWith(ext)
    );

    if (isVideo) {
      return html`
        <div class="image-container">
          <video controls autoplay loop src="${this.selectedImage}" style="width: 100%; height: 100%;"></video>
        </div>
      `;
    } else {
      return html`
        <div class="image-container">
          <img src="${this.selectedImage}" alt="${this.imageName || 'Selected image'}">
        </div>
      `;
    }
  }

  _renderControls() {
    return html`
      <div class="controls">
        <div class="button-row">
          <button class="button" @click="${this._previousImage}">
            <ha-icon icon="mdi:chevron-left"></ha-icon> Previous
          </button>
          <button class="button" @click="${this._nextImage}">
            Next <ha-icon icon="mdi:chevron-right"></ha-icon>
          </button>
        </div>
      </div>
    `;
  }

  _renderImageInfo() {
    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];

    return html`
      <div class="info">
        ${this.imageName ? html`
          <div class="info-row">
            <span>Image:</span>
            <span>${this.imageName}</span>
          </div>
        ` : ""}
        ${this.albumName ? html`
          <div class="info-row">
            <span>Album:</span>
            <span>${this.albumName}</span>
          </div>
        ` : ""}
        ${this.year && this.month ? html`
          <div class="info-row">
            <span>Date:</span>
            <span>${monthNames[this.month - 1]} ${this.year}</span>
          </div>
        ` : ""}
      </div>
    `;
  }

  _renderAlbumFilter() {
    return html`
      <div class="filter-section">
        <div class="filter-section-title">Album Filter</div>
        <div class="filter-row">
          <select @change="${this._setAlbumFilter}">
            <option value="">All Albums</option>
            ${this.albums.map(album => html`
              <option value="${album.name}" ?selected=${this.activeFilters.albumFilter === album.name}>
                ${album.name}${album.year ? ` (${album.year}-${String(album.month).padStart(2, '0')})` : ''}
              </option>
            `)}
          </select>
          <button class="button" @click="${this._clearAlbumFilter}">Clear</button>
        </div>
      </div>
    `;
  }

  _renderTimeRangeFilter() {
    // Generate year options
    const currentYear = new Date().getFullYear();
    const years = [];
    for (let i = currentYear - 20; i <= currentYear; i++) {
      years.push(i);
    }

    return html`
      <div class="filter-section">
        <div class="filter-section-title">Time Range Filter</div>
        <div class="filter-row">
          <label for="start-year">From:</label>
          <select id="start-year" @change="${this._updateTimeRange}">
            ${years.map(year => html`
              <option value="${year}" ?selected=${this.activeFilters.timeRange.startYear === year}>
                ${year}
              </option>
            `)}
          </select>
          <select id="start-month" @change="${this._updateTimeRange}">
            ${Array.from({length: 12}, (_, i) => i + 1).map(month => html`
              <option value="${month}" ?selected=${this.activeFilters.timeRange.startMonth === month}>
                ${String(month).padStart(2, '0')}
              </option>
            `)}
          </select>
        </div>
        <div class="filter-row">
          <label for="end-year">To:</label>
          <select id="end-year" @change="${this._updateTimeRange}">
            ${years.map(year => html`
              <option value="${year}" ?selected=${this.activeFilters.timeRange.endYear === year}>
                ${year}
              </option>
            `)}
          </select>
          <select id="end-month" @change="${this._updateTimeRange}">
            ${Array.from({length: 12}, (_, i) => i + 1).map(month => html`
              <option value="${month}" ?selected=${this.activeFilters.timeRange.endMonth === month}>
                ${String(month).padStart(2, '0')}
              </option>
            `)}
          </select>
        </div>
        <div class="filter-row">
          <button class="button" @click="${this._applyTimeRange}">Apply</button>
          <button class="button" @click="${this._clearTimeRange}">Clear</button>
        </div>
      </div>
    `;
  }

  _renderActiveFilters() {
    return html`
      <div class="active-filters">
        ${this.activeFilters.albumFilter ? html`
          <div class="active-filter">
            Album: ${this.activeFilters.albumFilter}
            <ha-icon icon="mdi:close" @click="${this._clearAlbumFilter}"></ha-icon>
          </div>
        ` : ""}
        
        ${this.activeFilters.timeRange.active ? html`
          <div class="active-filter">
            Time: ${this.activeFilters.timeRange.startYear}-${String(this.activeFilters.timeRange.startMonth).padStart(2, '0')} 
            to 
            ${this.activeFilters.timeRange.endYear}-${String(this.activeFilters.timeRange.endMonth).padStart(2, '0')}
            <ha-icon icon="mdi:close" @click="${this._clearTimeRange}"></ha-icon>
          </div>
        ` : ""}
      </div>
    `;
  }

  _nextImage() {
    this.hass.callService("picture_frame_controller", "next_image");
  }

  _previousImage() {
    this.hass.callService("picture_frame_controller", "previous_image");
  }

  _setAlbumFilter(e) {
    const albumName = e.target.value;
    if (albumName) {
      this.hass.callService("picture_frame_controller", "set_album_filter", {
        album_name: albumName,
      });
      this.activeFilters = {
        ...this.activeFilters,
        albumFilter: albumName,
      };
    } else {
      this._clearAlbumFilter();
    }
  }

  _clearAlbumFilter() {
    this.hass.callService("picture_frame_controller", "clear_album_filter");
    this.activeFilters = {
      ...this.activeFilters,
      albumFilter: null,
    };
  }

  _updateTimeRange(e) {
    const id = e.target.id;
    const value = Number(e.target.value);
    
    if (id === "start-year") {
      this.activeFilters.timeRange.startYear = value;
    } else if (id === "start-month") {
      this.activeFilters.timeRange.startMonth = value;
    } else if (id === "end-year") {
      this.activeFilters.timeRange.endYear = value;
    } else if (id === "end-month") {
      this.activeFilters.timeRange.endMonth = value;
    }
    
    this.requestUpdate();
  }

  _applyTimeRange() {
    const { startYear, startMonth, endYear, endMonth } = this.activeFilters.timeRange;
    
    this.hass.callService("picture_frame_controller", "set_time_range", {
      start_year: startYear,
      start_month: startMonth,
      end_year: endYear,
      end_month: endMonth,
    });
    
    this.activeFilters = {
      ...this.activeFilters,
      timeRange: {
        ...this.activeFilters.timeRange,
        active: true,
      },
    };
  }

  _clearTimeRange() {
    this.hass.callService("picture_frame_controller", "clear_time_range");
    this.activeFilters = {
      ...this.activeFilters,
      timeRange: {
        ...this.activeFilters.timeRange,
        active: false,
      },
    };
  }

  _resetSeenStatus() {
    this.hass.callService("picture_frame_controller", "reset_seen_status");
  }

  render() {
    if (!this.config || !this.hass) {
      return html``;
    }

    return html`
      <ha-card header="Picture Frame Controller">
        <div class="container">
          ${this._renderImage()}
          ${this._renderImageInfo()}
          ${this._renderControls()}
          ${this._renderActiveFilters()}
          ${this._renderAlbumFilter()}
          ${this._renderTimeRangeFilter()}
          <div class="button-row">
            <button class="button" @click="${this._resetSeenStatus}">
              <ha-icon icon="mdi:refresh"></ha-icon> Reset Seen Status
            </button>
          </div>
        </div>
      </ha-card>
    `;
  }
}

customElements.define("picture-frame-card", PictureFrameCard);

// This part is crucial for the card to be discovered by Home Assistant
window.customCards = window.customCards || [];
window.customCards.push({
  type: "picture-frame-card",
  name: "Picture Frame Card",
  description: "A card to control the picture frame display",
  preview: false,
});