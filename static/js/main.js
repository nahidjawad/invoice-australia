// static/js/main.js

function resetForm() {
  const form = document.querySelector('form');
  if (form) {
    form.reset();

    // Manually clear values
    form.querySelectorAll('input').forEach(input => {
      if (input.type !== 'submit' && input.type !== 'button' && input.type !== 'checkbox') {
        input.value = '';
      }
      if (input.type === 'checkbox') {
        input.checked = false;
      }
    });
  }
}
