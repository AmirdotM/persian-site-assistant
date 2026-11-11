/* Standalone Persian chat widget. No API secrets belong in this file. */
(() => {
  const script = document.currentScript;
  const apiBase = (script?.dataset.apiUrl || "").replace(/\/$/, "");
  const chatUrl = `${apiBase}/api/v1/chat`;

  const styles = `
    .psa-launcher { position:fixed; right:22px; bottom:22px; z-index:99999; border:0; border-radius:999px; padding:14px 20px; background:#173b70; color:#fff; font:600 14px Tahoma,Arial,sans-serif; cursor:pointer; box-shadow:0 8px 28px #10254435; }
    .psa-panel { position:fixed; right:22px; bottom:84px; z-index:99999; width:min(360px,calc(100vw - 32px)); height:480px; max-height:calc(100vh - 120px); display:none; flex-direction:column; overflow:hidden; border:1px solid #dce2eb; border-radius:18px; background:#fff; box-shadow:0 16px 50px #10254430; font-family:Tahoma,Arial,sans-serif; direction:rtl; }
    .psa-panel.psa-open { display:flex; }
    .psa-header { display:flex; justify-content:space-between; align-items:center; padding:14px 16px; background:#173b70; color:#fff; }
    .psa-header button { border:0; background:transparent; color:#fff; font-size:20px; cursor:pointer; }
    .psa-messages { flex:1; overflow:auto; padding:14px; background:#f7f9fc; }
    .psa-message { max-width:88%; margin:0 0 10px; padding:10px 12px; border-radius:12px; white-space:pre-wrap; overflow-wrap:anywhere; line-height:1.8; font-size:13px; }
    .psa-user { margin-right:auto; background:#dceafe; }
    .psa-assistant { margin-left:auto; background:#fff; border:1px solid #e5eaf1; }
    .psa-sources { margin:2px 0 12px; font-size:11px; }
    .psa-sources a { color:#174b91; display:block; margin-top:4px; }
    .psa-form { display:flex; gap:8px; padding:12px; border-top:1px solid #e6eaf0; }
    .psa-form input { min-width:0; flex:1; border:1px solid #d7deea; border-radius:10px; padding:10px; font:13px Tahoma,Arial,sans-serif; direction:rtl; }
    .psa-form button { border:0; border-radius:10px; padding:0 14px; background:#173b70; color:white; cursor:pointer; }
    .psa-form button:disabled { opacity:.5; cursor:wait; }
  `;
  const style = document.createElement("style");
  style.textContent = styles;
  document.head.appendChild(style);

  const launcher = document.createElement("button");
  launcher.className = "psa-launcher";
  launcher.type = "button";
  launcher.textContent = "گفت‌وگو با ما";
  launcher.setAttribute("aria-expanded", "false");

  const panel = document.createElement("section");
  panel.className = "psa-panel";
  panel.setAttribute("aria-label", "دستیار هوشمند وب‌سایت");
  panel.innerHTML = `
    <div class="psa-header"><strong>دستیار هوشمند</strong><button type="button" aria-label="بستن">×</button></div>
    <div class="psa-messages" aria-live="polite"><div class="psa-message psa-assistant">سلام! درباره خدمات مجموعه چه سؤالی دارید؟</div></div>
    <form class="psa-form"><input name="message" maxlength="1000" placeholder="سؤال خود را بنویسید…" autocomplete="off" required><button type="submit">ارسال</button></form>
  `;
  document.body.append(launcher, panel);

  const messages = panel.querySelector(".psa-messages");
  const form = panel.querySelector("form");
  const input = form.querySelector("input");
  const sendButton = form.querySelector("button");

  function addMessage(text, kind) {
    const item = document.createElement("div");
    item.className = `psa-message ${kind === "user" ? "psa-user" : "psa-assistant"}`;
    item.textContent = text;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
    return item;
  }

  launcher.addEventListener("click", () => {
    const isOpen = panel.classList.toggle("psa-open");
    launcher.setAttribute("aria-expanded", String(isOpen));
    if (isOpen) input.focus();
  });
  panel.querySelector(".psa-header button").addEventListener("click", () => {
    panel.classList.remove("psa-open");
    launcher.setAttribute("aria-expanded", "false");
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    addMessage(message, "user");
    input.value = "";
    sendButton.disabled = true;
    const pending = addMessage("در حال بررسی…", "assistant");

    try {
      const response = await fetch(chatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `خطای سرور (${response.status})`);
      }
      pending.textContent = data.answer || "پاسخی دریافت نشد.";
      if (Array.isArray(data.sources) && data.sources.length) {
        const sources = document.createElement("div");
        sources.className = "psa-sources";
        data.sources.forEach((source) => {
          if (!source.url) return;
          const link = document.createElement("a");
          link.href = source.url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          link.textContent = `منبع: ${source.title}`;
          sources.appendChild(link);
        });
        pending.appendChild(sources);
      }
    } catch (error) {
      pending.textContent = `فعلاً امکان دریافت پاسخ وجود ندارد. ${error.message}`;
    } finally {
      sendButton.disabled = false;
      input.focus();
      messages.scrollTop = messages.scrollHeight;
    }
  });
})();
