const container = document.getElementById("entries");

const formatDate = (iso) => {
  const date = new Date(iso);
  return new Intl.DateTimeFormat("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
};

const renderEntries = () => {
  if (!container) return;
  const entries = JSON.parse(localStorage.getItem("registrations") || "[]");
  if (!entries.length) {
    container.innerHTML =
      '<p class="entry-empty">данные не получены. ожидание сигнала...</p>';
    return;
  }

  const fragment = document.createDocumentFragment();

  entries.forEach((entry) => {
    const card = document.createElement("article");
    card.className = "entry-card";

    const name = document.createElement("h3");
    name.className = "entry-name";
    name.textContent = entry.fullName;

    const phone = document.createElement("p");
    phone.className = "entry-phone";
    phone.textContent = entry.phone;

    const time = document.createElement("p");
    time.className = "entry-time";
    time.textContent = formatDate(entry.submittedAt);

    card.append(name, phone, time);
    fragment.appendChild(card);
  });

  container.innerHTML = "";
  container.appendChild(fragment);
};

renderEntries();

setInterval(() => {
  container?.classList.toggle("glitch");
}, 1200);
