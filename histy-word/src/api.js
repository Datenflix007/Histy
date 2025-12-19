(function () {
  "use strict";

  const STORAGE_KEY = "histy.serverUrl";

  function getBaseUrl() {
    return window.localStorage.getItem(STORAGE_KEY) || "http://localhost:8000";
  }

  function setBaseUrl(url) {
    window.localStorage.setItem(STORAGE_KEY, url);
  }

  async function request(path, options) {
    const baseUrl = getBaseUrl().replace(/\/$/, "");
    const response = await fetch(baseUrl + path, options);
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "request_failed");
    }
    return response.json();
  }

  async function health() {
    return request("/api/health", { method: "GET" });
  }

  async function searchSources(q, limit) {
    return request("/api/sources/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q: q, limit: limit || 20 }),
    });
  }

  async function upsertDocument(payload) {
    return request("/api/documents/upsert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async function createCitation(payload) {
    return request("/api/citations/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async function renderCitation(payload) {
    return request("/api/render/citation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async function renderRefresh(payload) {
    return request("/api/render/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async function renderBibliography(payload) {
    return request("/api/render/bibliography", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async function renderSourcesList(payload) {
    return request("/api/render/sourceslist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  window.histyApi = {
    getBaseUrl: getBaseUrl,
    setBaseUrl: setBaseUrl,
    health: health,
    searchSources: searchSources,
    upsertDocument: upsertDocument,
    createCitation: createCitation,
    renderCitation: renderCitation,
    renderRefresh: renderRefresh,
    renderBibliography: renderBibliography,
    renderSourcesList: renderSourcesList,
  };
})();
