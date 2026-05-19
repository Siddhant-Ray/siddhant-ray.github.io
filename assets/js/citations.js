document.addEventListener("DOMContentLoaded", async () => {
  const buttons = document.querySelectorAll(".citation-btn[data-bibkey]");
  if (!buttons.length) return;

  try {
    const response = await fetch("/assets/data/citations.json", {
      cache: "no-store",
    });

    if (!response.ok) return;

    const citations = await response.json();

    buttons.forEach((button) => {
      const key = button.dataset.bibkey;
      const countEl = button.querySelector(".citation-count");

      if (!key || !countEl || !citations[key]) return;

      const count = citations[key].cited_by;

      if (Number.isInteger(count)) {
        countEl.textContent = count;
      } else {
        countEl.textContent = "–";
      }

      if (citations[key].scholar_link) {
        button.href = citations[key].scholar_link;
      }

      const method = citations[key].counting_method || "Google Scholar";
      const updatedAt = citations[key].updated_at || "";

      if (updatedAt) {
        button.title = `${method}. Last updated: ${updatedAt}`;
      }
    });
  } catch (error) {
    console.warn("Could not load citation counts:", error);
  }
});