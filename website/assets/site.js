(() => {
  const toggle = document.querySelector("[data-menu-toggle]");
  const nav = document.querySelector("[data-main-nav]");

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(isOpen));
      toggle.textContent = isOpen ? "×" : "☰";
    });

    nav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.textContent = "☰";
      });
    });
  }

  document.querySelectorAll("[data-open-assistant]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      window.dispatchEvent(new CustomEvent("psa:open"));
    });
  });

  document.querySelectorAll("[data-ask-assistant]").forEach((control) => {
    control.addEventListener("click", (event) => {
      event.preventDefault();
      const question = control.dataset.askAssistant || "";
      if (question.trim()) {
        window.dispatchEvent(new CustomEvent("psa:ask", { detail: { question } }));
      }
    });
  });

  const search = document.querySelector("[data-product-search]");
  const cards = Array.from(document.querySelectorAll("[data-product-grid] .product-card"));
  const filterButtons = Array.from(document.querySelectorAll("[data-product-filter]"));
  const emptyState = document.querySelector("[data-product-empty]");
  let activeFilter = "all";

  function updateProductView() {
    if (!cards.length) return;
    const query = search ? search.value.trim().toLocaleLowerCase("fa") : "";
    let visibleCount = 0;

    cards.forEach((card) => {
      const category = card.dataset.category || "";
      const searchable = (card.dataset.search || card.textContent).toLocaleLowerCase("fa");
      const matchesFilter =
        activeFilter === "all" ||
        (activeFilter === "web" && ["web", "commerce"].includes(category)) ||
        category === activeFilter;
      const matchesQuery = !query || searchable.includes(query);
      const visible = matchesFilter && matchesQuery;
      card.hidden = !visible;
      if (visible) visibleCount += 1;
    });

    if (emptyState) emptyState.hidden = visibleCount > 0;
  }

  if (search) search.addEventListener("input", updateProductView);
  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeFilter = button.dataset.productFilter || "all";
      filterButtons.forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
      updateProductView();
    });
  });
  updateProductView();
})();