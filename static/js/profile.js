// Wait for DOM to load
window.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('profileForm');
  if (!form) return;
  const saveBtn = document.getElementById('saveBtn');
  const saveBtnText = document.getElementById('saveBtnText');
  const saveBtnSpinner = document.getElementById('saveBtnSpinner');
  const msgDiv = document.getElementById('profileMsg');

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    saveBtn.disabled = true;
    saveBtnText.textContent = 'Saving...';
    saveBtnSpinner.classList.remove('d-none');
    msgDiv.textContent = '';
    msgDiv.className = 'mt-3';

    const name = form.elements['name'].value;
    const phone = form.elements['phone'].value;
    const address = form.elements['address'].value;
    const gender = form.elements['gender'].value;
    const dob = form.elements['dob'].value;
    try {
      const response = await fetch('/profile', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, phone, address, gender, dob})
      });
      const result = await response.json();
      msgDiv.textContent = result.message;
      msgDiv.classList.add(result.success ? 'text-success' : 'text-danger');
    } catch (err) {
      msgDiv.textContent = 'An error occurred. Please try again.';
      msgDiv.classList.add('text-danger');
    } finally {
      saveBtn.disabled = false;
      saveBtnText.textContent = 'Save';
      saveBtnSpinner.classList.add('d-none');
    }
  });
}); 