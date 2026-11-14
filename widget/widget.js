/* Persian RAG chat widget. Safe to embed with one script tag; no API secrets belong here. */
(() => {
  const script = document.currentScript;
  if (document.getElementById("psa-chat-launcher")) return;

  const hasApiBaseAttribute = Boolean(script && script.hasAttribute("data-api-url"));
  const configuredApiBase = hasApiBaseAttribute ? (script.dataset.apiUrl || "").trim() : "";
  const apiBase = (
    hasApiBaseAttribute
      ? configuredApiBase || window.location.origin
      : "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
  const chatUrl = apiBase + "/api/v1/chat";

  // Load the widget stylesheet relative to this script, so the embed stays portable.
  if (script && script.src) {
    const stylesheetUrl = new URL("./widget.css", script.src).href;
    const alreadyLoaded = Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
      .some((link) => link.href === stylesheetUrl);
    if (!alreadyLoaded) {
      const stylesheet = document.createElement("link");
      stylesheet.rel = "stylesheet";
      stylesheet.href = stylesheetUrl;
      document.head.appendChild(stylesheet);
    }
  }

  const launcher = document.createElement("button");
  launcher.id = "psa-chat-launcher";
  launcher.className = "psa-launcher";
  launcher.type = "button";
  launcher.setAttribute("aria-expanded", "false");
  launcher.setAttribute("aria-controls", "psa-chat-panel");
  launcher.innerHTML = '<span class="psa-launcher-mark" aria-hidden="true">ر</span><span class="psa-launcher-copy">گفت‌وگو با ما<small>دستیار راهکار نوین آریا</small></span>';

  const panel = document.createElement("section");
  panel.id = "psa-chat-panel";
  panel.className = "psa-panel";
  panel.hidden = true;
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-modal", "false");
  panel.setAttribute("aria-label", "دستیار هوشمند راهکار نوین آریا");
  panel.innerHTML = [
    '<div class="psa-header">',
      '<div class="psa-header-brand">',
        '<span class="psa-header-mark" aria-hidden="true">ر</span>',
        '<span class="psa-header-title"><strong>دستیار راهکار نوین آریا</strong><small><i class="psa-status-dot"></i> پاسخ‌گویی بر پایه اسناد</small></span>',
      '</div>',
      '<button class="psa-close" type="button" aria-label="بستن گفت‌وگو">×</button>',
    '</div>',
    '<div class="psa-intro"><strong>سلام، خوش آمدید.</strong><p>درباره خدمات، فرایند همکاری یا سناریوهای نمایشی سؤال کنید. پاسخ‌ها بر اساس اطلاعات موجود در اسناد هستند.</p></div>',
    '<div class="psa-messages" aria-live="polite" aria-relevant="additions text"></div>',
    '<div class="psa-form-wrap">',
      '<form class="psa-form">',
        '<input name="message" maxlength="4000" placeholder="سؤال خود را بنویسید…" autocomplete="off" aria-label="متن پرسش" required>',
        '<button class="psa-send" type="submit" aria-label="ارسال پرسش">←</button>',
      '</form>',
      '<div class="psa-footnote">نسخه نمایشی · اطلاعات حساس ارسال نکنید</div>',
    '</div>'
  ].join("");
  document.body.append(launcher, panel);

  const messages = panel.querySelector(".psa-messages");
  const form = panel.querySelector(".psa-form");
  const input = form.querySelector("input");
  const sendButton = form.querySelector("button");

  function addMessage(text, kind, extraClass) {
    const item = document.createElement("div");
    item.className = "psa-message " + (kind === "user" ? "psa-user" : "psa-assistant");
    if (extraClass) item.classList.add(extraClass);
    item.textContent = text;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
    return item;
  }

  function addSuggestions() {
    const wrap = document.createElement("div");
    wrap.className = "psa-suggestions";
    [
      "برای فروشگاه ۱۵۰ محصولی با بودجه ۵۰ تا ۶۵ میلیون تومان چه پیشنهادی دارید؟",
      "تفاوت پیگیر و جریان‌کار چیست؟",
      "برای جست‌وجو در اسناد PDF چه محصولی دارید؟"
    ].forEach((question) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "psa-suggestion";
      button.textContent = question;
      button.addEventListener("click", () => {
        input.value = question;
        form.requestSubmit();
      });
      wrap.appendChild(button);
    });
    messages.appendChild(wrap);
  }

  function openPanel() {
    panel.hidden = false;
    launcher.setAttribute("aria-expanded", "true");
    input.focus();
  }

  function closePanel() {
    panel.hidden = true;
    launcher.setAttribute("aria-expanded", "false");
    launcher.focus();
  }

  function appendSources(sources) {
    if (!Array.isArray(sources) || sources.length === 0) return;

    const list = document.createElement("div");
    list.className = "psa-sources";
    const label = document.createElement("div");
    label.className = "psa-sources-label";
    label.textContent = "اسناد مرتبط";
    list.appendChild(label);

    sources.slice(0, 5).forEach((source) => {
      if (!source || typeof source !== "object") return;

      let card;
      let safeUrl = null;
      if (typeof source.url === "string" && source.url.trim()) {
        try {
          const parsedUrl = new URL(source.url, window.location.href);
          if (parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:") safeUrl = parsedUrl.href;
        } catch (_) {
          safeUrl = null;
        }
      }

      card = document.createElement(safeUrl ? "a" : "div");
      card.className = "psa-source";
      if (safeUrl) {
        card.href = safeUrl;
        card.target = "_blank";
        card.rel = "noopener noreferrer";
      }

      const title = document.createElement("span");
      title.className = "psa-source-title";
      title.textContent = typeof source.title === "string" && source.title ? source.title : "سند مرتبط";
      card.appendChild(title);

      if (typeof source.excerpt === "string" && source.excerpt.trim()) {
        const excerpt = document.createElement("span");
        excerpt.className = "psa-source-excerpt";
        excerpt.textContent = source.excerpt;
        card.appendChild(excerpt);
      }

      if (typeof source.source_id === "string" && source.source_id) {
        const tag = document.createElement("span");
        tag.className = "psa-source-tag";
        tag.textContent = "شناسه سند: " + source.source_id;
        card.appendChild(tag);
      }
      list.appendChild(card);
    });

    if (list.children.length > 1) messages.appendChild(list);
  }

  async function readResponse(response) {
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      const body = await response.text();
      throw new Error(response.ok ? "پاسخ سرور در قالب JSON نبود." : "سرور پاسخ قابل پردازش ارسال نکرد.");
    }
    return response.json();
  }

  launcher.addEventListener("click", () => {
    if (panel.hidden) openPanel();
    else closePanel();
  });
  panel.querySelector(".psa-close").addEventListener("click", closePanel);
  window.addEventListener("psa:open", openPanel);
  window.addEventListener("psa:ask", (event) => {
    const question = event.detail && event.detail.question;
    if (typeof question !== "string" || !question.trim()) return;
    openPanel();
    input.value = question.trim();
    form.requestSubmit();
  });
  window.addEventListener("psa:ask", (event) => {
    const question = event.detail && event.detail.question;
    if (typeof question !== "string" || !question.trim()) return;
    openPanel();
    input.value = question.trim();
    form.requestSubmit();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) closePanel();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || sendButton.disabled) return;

    addMessage(message, "user");
    input.value = "";
    input.disabled = true;
    sendButton.disabled = true;
    const pending = addMessage("در حال جست‌وجو در اسناد…", "assistant", "psa-pending");
    pending.setAttribute("aria-busy", "true");

    try {
      const response = await fetch(chatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      });
      const data = await readResponse(response);

      if (!response.ok) {
        const detail = data && typeof data.detail === "string" ? data.detail : "در حال حاضر امکان پاسخ‌گویی وجود ندارد.";
        throw new Error(detail);
      }
      if (!data || typeof data.answer !== "string" || !data.answer.trim()) {
        throw new Error("پاسخی از سرویس دریافت نشد.");
      }

      pending.textContent = data.answer;
      pending.classList.remove("psa-pending");
      pending.removeAttribute("aria-busy");
      appendSources(data.sources);
    } catch (error) {
      pending.textContent = "متأسفیم؛ دریافت پاسخ با مشکل روبه‌رو شد. " +
        (error && error.message ? error.message : "اتصال به سرویس برقرار نشد.");
      pending.classList.remove("psa-pending");
      pending.removeAttribute("aria-busy");
    } finally {
      input.disabled = false;
      sendButton.disabled = false;
      input.focus();
      messages.scrollTop = messages.scrollHeight;
    }
  });

  addMessage("می‌توانم درباره محصولات، مقایسه راهکارها، خدمات و سناریوهای نمایشی راهنمایی کنم.", "assistant");
  addSuggestions();
})();