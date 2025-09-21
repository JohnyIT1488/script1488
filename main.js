(function () {
  const form = document.getElementById("registration-form");
  const STORAGE_KEY = "futuresign_registrations";

  const readEntries = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const data = JSON.parse(raw);
      if (Array.isArray(data)) {
        return data;
      }
      return [];
    } catch (error) {
      console.error("Cannot read saved entries", error);
      return [];
    }
  };

  const writeEntries = (entries) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const fullName = formData.get("fullName").trim();
    const phone = formData.get("phone").trim();

    if (!fullName || !/^\d{10}$/.test(phone)) {
      form.reportValidity();
      return;
    }

    const entries = readEntries();
    const normalizedPhone = `+7 ${phone.slice(0, 3)} ${phone.slice(3, 6)} ${phone.slice(6)}`;
    const newEntry = {
      id: Date.now(),
      fullName,
      phone: normalizedPhone,
      createdAt: new Date().toISOString(),
    };

    const updatedEntries = [newEntry, ...entries].sort(
      (a, b) => new Date(b.createdAt) - new Date(a.createdAt)
    );

    writeEntries(updatedEntries);
    form.reset();
    window.location.href = "entries.html";
  });
})();
