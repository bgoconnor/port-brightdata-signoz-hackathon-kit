/* Ported from the design handoff (pf-hl.js) to ES modules.
   JSX, class names and markup are unchanged: the prototype is the
   visual spec. Only the module wiring differs (globals -> imports). */


  var KW = /^(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield|match|case)$/;
  var BUILTIN = /^(abs|all|any|bool|dict|enumerate|float|int|len|list|max|min|print|range|round|set|str|sum|tuple|type|zip|isinstance|super|open|sorted|map|filter|getattr|setattr|hasattr|repr|format|self|cls)$/;

  function tokenize(src) {
    var out = [], i = 0, n = src.length;
    function push(c, t) { if (t) out.push({ c: c, t: t }); }
    while (i < n) {
      var ch = src[i];
      if (ch === "\n" || ch === " " || ch === "\t") { var j = i; while (j < n && (src[j] === "\n" || src[j] === " " || src[j] === "\t")) j++; push("", src.slice(i, j)); i = j; continue; }
      if (ch === "#") { var e = src.indexOf("\n", i); if (e === -1) e = n; push("cm", src.slice(i, e)); i = e; continue; }
      var pre = "", k = i;
      if (/[fFrRbBuU]/.test(ch) && i + 1 < n && /["']/.test(src[i + 1])) { pre = ch; k = i + 1; }
      if (src[k] === '"' || src[k] === "'") {
        var q = src[k], triple = src.slice(k, k + 3) === q + q + q, delim = triple ? q + q + q : q, p = k + delim.length;
        while (p < n) {
          if (src[p] === "\\") { p += 2; continue; }
          if (src.slice(p, p + delim.length) === delim) { p += delim.length; break; }
          if (!triple && src[p] === "\n") break;
          p++;
        }
        push(triple ? "doc" : "st", src.slice(i, p)); i = p; continue;
      }
      if (/[0-9]/.test(ch) || (ch === "." && /[0-9]/.test(src[i + 1] || ""))) { var m = /^[0-9][0-9_]*\.?[0-9_]*(e[-+]?[0-9]+)?j?|^\.[0-9]+/i.exec(src.slice(i)); var lit = m ? m[0] : ch; push("nu", lit); i += lit.length; continue; }
      if (ch === "@" && /[A-Za-z_]/.test(src[i + 1] || "")) { var d = /^@[A-Za-z_][\w.]*/.exec(src.slice(i))[0]; push("de", d); i += d.length; continue; }
      if (/[A-Za-z_]/.test(ch)) {
        var w = /^[A-Za-z_]\w*/.exec(src.slice(i))[0]; i += w.length;
        var prev = out.length ? out[out.length - 1] : null, prevWord = null;
        for (var z = out.length - 1; z >= 0; z--) { if (out[z].c !== "" ) { prevWord = out[z]; break; } if (/\S/.test(out[z].t)) { prevWord = out[z]; break; } }
        if (KW.test(w)) push("kw", w);
        else if (prevWord && (prevWord.t === "def" || prevWord.t === "class")) push("fn", w);
        else if (src[i] === "(") push("ca", w);
        else if (BUILTIN.test(w)) push("bi", w);
        else if (/^[A-Z][A-Z0-9_]*$/.test(w)) push("co", w);
        else push("", w);
        continue;
      }
      var op = /^[-+*/%=<>!&|^~]+/.exec(src.slice(i));
      if (op) { push("op", op[0]); i += op[0].length; continue; }
      push("pn", ch); i++;
    }
    return out;
  }

  /* split tokens into lines so the renderer can draw line numbers */
  function lines(src) {
    var res = [[]];
    tokenize(str(src)).forEach(function (tok) {
      var parts = tok.t.split("\n");
      parts.forEach(function (p, idx) {
        if (idx > 0) res.push([]);
        if (p) res[res.length - 1].push({ c: tok.c, t: p });
      });
    });
    return res;
  }
  function str(v) { return typeof v === "string" ? v : (v == null ? "" : String(v)); }

export { tokenize, lines };
