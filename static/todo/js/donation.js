const amountInput = document.querySelector('input[name="amount"]');
const presetButtons = document.querySelectorAll('[data-donation-amount]');

presetButtons.forEach((button) => {
    button.addEventListener('click', () => {
        if (!amountInput) return;

        amountInput.value = button.dataset.donationAmount;
        presetButtons.forEach((item) => item.classList.remove('active'));
        button.classList.add('active');
        amountInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
});
