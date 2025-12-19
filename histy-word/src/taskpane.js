(function () {
  "use strict";

  const statusEl = () => document.getElementById("status");
  const resultsEl = () => document.getElementById("results");

  function setStatus(text, ok) {
    const el = statusEl();
    el.textContent = text;
    el.style.color = ok ? "#1f7a1f" : "#a12020";
  }

  function createUuid() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  async function checkConnection() {
    try {
      const res = await window.histyApi.health();
      setStatus(res.status === "ok" ? "Connected" : "Server error", res.status === "ok");
    } catch (err) {
      setStatus("Not connected", false);
    }
  }

  async function ensureDocument() {
    return Word.run(async (context) => {
      const props = context.document.properties;
      const customProps = props.customProperties;

      props.load("title");
      const fingerprintProp = customProps.getItemOrNullObject("HISTY_DOC_FINGERPRINT");
      fingerprintProp.load("value");
      await context.sync();

      let fingerprint = fingerprintProp.isNullObject ? null : fingerprintProp.value;
      if (!fingerprint) {
        fingerprint = createUuid();
        customProps.add("HISTY_DOC_FINGERPRINT", fingerprint);
      }
      await context.sync();

      return { fingerprint: fingerprint, name: props.title || "Untitled" };
    });
  }

  async function insertRunsIntoControl(control, runs, fallbackText) {
    control.insertText("", Word.InsertLocation.replace);

    if (!runs || !runs.length) {
      control.insertText(fallbackText || "", Word.InsertLocation.replace);
      return;
    }

    let cursor = control.getRange(Word.RangeLocation.start);
    runs.forEach((run) => {
      const inserted = cursor.insertText(run.text, Word.InsertLocation.after);
      if (run.italic) {
        inserted.font.italic = true;
      }
      if (run.bold) {
        inserted.font.bold = true;
      }
      if (run.small_caps) {
        inserted.font.smallCaps = true;
      }
      cursor = inserted.getRange(Word.RangeLocation.after);
    });
  }

  async function insertCitation(sourceId, locator) {
    const docInfo = await ensureDocument();
    const docResponse = await window.histyApi.upsertDocument({
      doc_fingerprint: docInfo.fingerprint,
      name: docInfo.name,
    });

    const doc = docResponse.document;
    const citationResponse = await window.histyApi.createCitation({
      doc_id: doc.id,
      source_id: sourceId,
      locator: locator || null,
    });

    const citationUuid = citationResponse.citation.citation_uuid;
    const renderResponse = await window.histyApi.renderCitation({
      citation_uuid: citationUuid,
      doc_id: doc.id,
    });

    const token = window.histyTokens.buildToken({
      citation_uuid: citationUuid,
      source_id: sourceId,
      locator: locator,
      doc_id: doc.id,
      style_id: doc.active_style_id,
    });
    window.histyTokens.updateTokenWithRender(token, renderResponse, renderResponse.style_version);

    await Word.run(async (context) => {
      const selection = context.document.getSelection();
      const footnote = selection.insertFootnote("");
      footnote.load("body");
      await context.sync();

      const control = footnote.body.insertContentControl();
      control.title = "HISTY_CITATION";
      control.tag = JSON.stringify(token);
      control.appearance = Word.ContentControlAppearance.hidden;
      control.color = "#b14c2c";

      await insertRunsIntoControl(control, renderResponse.runs, renderResponse.plain_text);
      await context.sync();
    });
  }

  async function refreshAll() {
    const docInfo = await ensureDocument();
    const docResponse = await window.histyApi.upsertDocument({
      doc_fingerprint: docInfo.fingerprint,
      name: docInfo.name,
    });
    const docId = docResponse.document.id;

    const tokenSnapshots = [];
    await Word.run(async (context) => {
      const controls = context.document.contentControls.getByTitle("HISTY_CITATION");
      controls.load("items");
      await context.sync();

      controls.items.forEach((control) => {
        control.load("id,tag");
      });
      await context.sync();

      controls.items.forEach((control) => {
        const token = window.histyTokens.parseToken(control.tag);
        if (token) {
          tokenSnapshots.push({ id: control.id, token: token });
        }
      });
    });

    const orderedUuids = tokenSnapshots.map((item) => item.token.citation_uuid);
    if (!orderedUuids.length) {
      return;
    }

    const refreshResponse = await window.histyApi.renderRefresh({
      doc_id: docId,
      citation_uuids: orderedUuids,
    });
    const itemsById = {};
    refreshResponse.items.forEach((item) => {
      itemsById[item.citation_uuid] = item;
    });

    await Word.run(async (context) => {
      for (const entry of tokenSnapshots) {
        const renderItem = itemsById[entry.token.citation_uuid];
        if (!renderItem) {
          continue;
        }
        const control = context.document.contentControls.getById(entry.id);
        window.histyTokens.updateTokenWithRender(
          entry.token,
          renderItem,
          refreshResponse.style_version
        );
        control.tag = JSON.stringify(entry.token);
        await insertRunsIntoControl(control, renderItem.runs, renderItem.plain_text);
      }
      await context.sync();
    });
  }

  async function insertList(title, renderFn) {
    const docInfo = await ensureDocument();
    const docResponse = await window.histyApi.upsertDocument({
      doc_fingerprint: docInfo.fingerprint,
      name: docInfo.name,
    });
    const docId = docResponse.document.id;
    const response = await renderFn({ doc_id: docId });
    const text = response.items.map((item) => item.plain_text).join("\n");

    await Word.run(async (context) => {
      let control = context.document.contentControls.getByTitle(title).getFirstOrNullObject();
      control.load("isNullObject");
      await context.sync();

      if (control.isNullObject) {
        const paragraph = context.document.body.insertParagraph("", Word.InsertLocation.end);
        control = paragraph.insertContentControl();
        control.title = title;
      }

      control.insertText(text, Word.InsertLocation.replace);
      await context.sync();
    });
  }

  function renderResults(items) {
    const container = resultsEl();
    container.innerHTML = "";

    if (!items.length) {
      container.innerHTML = "<div class=\"muted\">No results.</div>";
      return;
    }

    items.forEach((item) => {
      const div = document.createElement("div");
      div.className = "result-item";
      const title = document.createElement("div");
      title.textContent = item.title + (item.year ? " (" + item.year + ")" : "");
      const btn = document.createElement("button");
      btn.textContent = "Insert";
      btn.addEventListener("click", async () => {
        const locator = document.getElementById("locatorInput").value;
        await insertCitation(item.id, locator);
      });
      div.appendChild(title);
      div.appendChild(btn);
      container.appendChild(div);
    });
  }

  Office.onReady(() => {
    const serverInput = document.getElementById("serverUrl");
    serverInput.value = window.histyApi.getBaseUrl();
    serverInput.addEventListener("change", () => {
      window.histyApi.setBaseUrl(serverInput.value.trim());
    });

    document.getElementById("checkConnection").addEventListener("click", async () => {
      window.histyApi.setBaseUrl(serverInput.value.trim());
      await checkConnection();
    });

    document.getElementById("searchButton").addEventListener("click", async () => {
      const query = document.getElementById("searchBox").value;
      const results = await window.histyApi.searchSources(query, 20);
      renderResults(results.items || []);
    });

    document.getElementById("refreshButton").addEventListener("click", async () => {
      await refreshAll();
    });

    document.getElementById("bibliographyButton").addEventListener("click", async () => {
      await insertList("HISTY_BIBLIOGRAPHY", window.histyApi.renderBibliography);
    });

    document.getElementById("sourcesButton").addEventListener("click", async () => {
      await insertList("HISTY_SOURCES", window.histyApi.renderSourcesList);
    });

    checkConnection();
  });
})();
