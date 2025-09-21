const form = document.getElementById("registration-form");
const fullNameInput = document.getElementById("fullName");
const phoneInput = document.getElementById("phone");

const normalizePhone = (value) => {
  const digits = value.replace(/\D/g, "");
  if (!digits.startsWith("7")) {
    return "+7" + digits.replace(/^\d/, "");
  }
  return "+" + digits;
};

const saveEntry = (entry) => {
  const key = "registrations";
  const existing = JSON.parse(localStorage.getItem(key) || "[]");
  existing.unshift(entry);
  localStorage.setItem(key, JSON.stringify(existing));
};

form?.addEventListener("submit", (event) => {
  event.preventDefault();

  const fullName = fullNameInput.value.trim();
  const phone = normalizePhone(phoneInput.value.trim());

  if (!fullName || !phone) {
    form.classList.add("shake");
    setTimeout(() => form.classList.remove("shake"), 600);
    return;
  }

  saveEntry({
    fullName,
    phone,
    submittedAt: new Date().toISOString(),
  });

  window.location.href = "glitch.html";
});

phoneInput?.addEventListener("input", () => {
  const digits = phoneInput.value.replace(/\D/g, "");
  const maxDigits = 11;
  const trimmed = digits.slice(0, maxDigits);

  let formatted = "+7";
  if (trimmed.length > 1) {
    formatted += ` (${trimmed.slice(1, 4)}`;
  }
  if (trimmed.length >= 4) {
    formatted += ")";
  }
  if (trimmed.length >= 4) {
    formatted += ` ${trimmed.slice(4, 7)}`;
  }
  if (trimmed.length >= 7) {
    formatted += `-${trimmed.slice(7, 9)}`;
  }
  if (trimmed.length >= 9) {
    formatted += `-${trimmed.slice(9, 11)}`;
  }

  phoneInput.value = formatted;
});
