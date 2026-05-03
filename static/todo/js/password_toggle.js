function enhancePasswordFields() {
    document.querySelectorAll('input[type="password"]').forEach((input) => {
        if (input.dataset.passwordEnhanced === 'true') return;

        const wrapper = document.createElement('div');
        const button = document.createElement('button');

        wrapper.className = 'password-field';
        button.className = 'password-toggle';
        button.type = 'button';
        button.textContent = 'Показать';
        button.setAttribute('aria-label', 'Показать пароль');

        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        wrapper.appendChild(button);
        input.dataset.passwordEnhanced = 'true';

        button.addEventListener('click', () => {
            const isHidden = input.type === 'password';
            input.type = isHidden ? 'text' : 'password';
            button.textContent = isHidden ? 'Скрыть' : 'Показать';
            button.setAttribute(
                'aria-label',
                isHidden ? 'Скрыть пароль' : 'Показать пароль'
            );
        });
    });
}

enhancePasswordFields();
