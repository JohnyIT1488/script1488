document.addEventListener('DOMContentLoaded', () => {
  const entriesContainer = document.getElementById('entries');
  if (!entriesContainer) return;

  const stored = JSON.parse(localStorage.getItem('registrations') || '[]');
  if (!stored.length) {
    entriesContainer.innerHTML = `
      <p class="broken__empty">Пока никто не оставил заявку. Возможно, сервер снова завис...</p>
    `;
    return;
  }

  stored
    .sort((a, b) => b.submittedAt - a.submittedAt)
    .forEach((entry, index) => {
      const card = document.createElement('article');
      card.className = 'broken__entry';
      card.style.setProperty('--i', index);

      const name = document.createElement('h3');
      name.className = 'broken__entry-name';
      name.textContent = entry.fullName;

      const phone = document.createElement('p');
      phone.className = 'broken__entry-phone';
      phone.textContent = entry.phone;

      const date = document.createElement('p');
      date.className = 'broken__entry-date';
      date.textContent = new Date(entry.submittedAt).toLocaleString('ru-RU');

      card.append(name, phone, date);
      entriesContainer.appendChild(card);
    });
});
