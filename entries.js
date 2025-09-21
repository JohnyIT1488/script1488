(function () {
  const STORAGE_KEY = "futuresign_registrations";
  const list = document.getElementById("entries-list");

  const readEntries = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const data = JSON.parse(raw);
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error("Cannot read saved entries", error);
      return [];
    }
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  };

  const render = () => {
    const entries = readEntries();
    if (!entries.length) {
      list.innerHTML = '<li class="glitch-list__item">Пока никто не зарегистрировался. Система ждёт...</li>';
      return;
    }

    list.innerHTML = entries
      .map(
        (entry) => `
          <li class="glitch-list__item">
            <span class="glitch-list__name">${entry.fullName}</span>
            <span class="glitch-list__phone">${entry.phone}</span>
            <span class="glitch-list__time">${formatDate(entry.createdAt)}</span>
          </li>
        `
      )
      .join("");
  };

  render();
})();
