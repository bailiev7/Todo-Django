const amountInput = document.querySelector('input[name="amount"]');
const presetButtons = document.querySelectorAll('[data-donation-amount]');
const donationForm = document.querySelector('.donation-form');
const paymentInputs = document.querySelectorAll('input[name="payment_method"]');
const paymentDetails = document.querySelectorAll('[data-payment-detail]');
const sbpBankButtons = document.querySelectorAll('[data-sbp-bank]');
const cardNumberInput = document.querySelector('[data-card-number]');
const cardExpiryInput = document.querySelector('[data-card-expiry]');
const cardCvcInput = document.querySelector('[data-card-cvc]');

presetButtons.forEach((button) => {
    button.addEventListener('click', () => {
        if (!amountInput) return;

        amountInput.value = button.dataset.donationAmount;
        presetButtons.forEach((item) => item.classList.remove('active'));
        button.classList.add('active');
        amountInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
});

const getSelectedPaymentMethod = () => {
    const selected = Array.from(paymentInputs).find((input) => input.checked);
    return selected ? selected.value : 'bank_card';
};

const updatePaymentDetails = () => {
    const selectedMethod = getSelectedPaymentMethod();

    paymentDetails.forEach((detail) => {
        const isActive = detail.dataset.paymentDetail === selectedMethod;
        detail.hidden = !isActive;
    });
};

paymentInputs.forEach((input) => {
    input.addEventListener('change', updatePaymentDetails);
});

sbpBankButtons.forEach((button) => {
    button.addEventListener('click', () => {
        sbpBankButtons.forEach((item) => {
            item.classList.remove('active');
            item.setAttribute('aria-pressed', 'false');
        });
        button.classList.add('active');
        button.setAttribute('aria-pressed', 'true');
    });
});

if (donationForm) {
    donationForm.addEventListener('submit', (event) => {
        if (getSelectedPaymentMethod() !== 'sbp') return;

        const selectedBank = Array.from(sbpBankButtons).find((button) => (
            button.classList.contains('active')
        ));
        const bankUrl = selectedBank ? selectedBank.dataset.bankUrl : '';

        if (!bankUrl) return;

        event.preventDefault();
        window.location.assign(bankUrl);
    });
}

const onlyDigits = (value) => value.replace(/\D/g, '');

if (cardNumberInput) {
    cardNumberInput.addEventListener('input', () => {
        const digits = onlyDigits(cardNumberInput.value).slice(0, 16);
        cardNumberInput.value = digits.replace(/(\d{4})(?=\d)/g, '$1 ');
    });
}

if (cardExpiryInput) {
    cardExpiryInput.addEventListener('input', () => {
        const digits = onlyDigits(cardExpiryInput.value).slice(0, 4);
        cardExpiryInput.value = digits.length > 2
            ? `${digits.slice(0, 2)} / ${digits.slice(2)}`
            : digits;
    });
}

if (cardCvcInput) {
    cardCvcInput.addEventListener('input', () => {
        cardCvcInput.value = onlyDigits(cardCvcInput.value).slice(0, 3);
    });
}

updatePaymentDetails();
