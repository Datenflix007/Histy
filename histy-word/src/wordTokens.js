(function () {
  "use strict";

  function buildToken(data) {
    return {
      citation_uuid: data.citation_uuid,
      source_id: data.source_id,
      locator: data.locator || "",
      doc_id: data.doc_id,
      style_id: data.style_id,
      render_mode: data.render_mode || "auto",
      cached_text: data.cached_text || "",
      cached_style_version: data.cached_style_version || "",
      cached_render_hash: data.cached_render_hash || "",
    };
  }

  function updateTokenWithRender(token, renderOutput, styleVersion) {
    token.cached_text = renderOutput.plain_text || "";
    token.cached_style_version = styleVersion || token.cached_style_version;
    token.cached_render_hash = renderOutput.metadata?.render_hash || token.cached_render_hash;
    return token;
  }

  function parseToken(tagValue) {
    if (!tagValue) {
      return null;
    }
    try {
      return JSON.parse(tagValue);
    } catch (err) {
      return null;
    }
  }

  window.histyTokens = {
    buildToken: buildToken,
    updateTokenWithRender: updateTokenWithRender,
    parseToken: parseToken,
  };
})();
