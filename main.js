document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('registration-form');
  if (!form) return;

  form.addEventListener('submit', (event) => {
    event.preventDefault();

    const fullName = document.getElementById('fullName').value.trim();
    const phoneInput = document.getElementById('phone');
    const phoneRaw = phoneInput.value.replace(/\D/g, '');

    if (!fullName) {
      alert('Пожалуйста, укажите ФИО.');
      return;
    }

    if (phoneRaw.length !== 10) {
      alert('Введите 10 цифр после +7.');
      phoneInput.focus();
      return;
    }

    const stored = JSON.parse(localStorage.getItem('registrations') || '[]');
    stored.push({
      fullName,
      phone: `+7${phoneRaw}`,
      submittedAt: Date.now(),
    });

    localStorage.setItem('registrations', JSON.stringify(stored));
    window.location.href = 'submissions.html';
  });
});
