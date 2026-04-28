const body = document.body;
const tabs = document.querySelectorAll('[data-tab-target]');
const panels = document.querySelectorAll('.form-panel');
const progressValue = document.getElementById('progress-value');
const progressFill = document.getElementById('progress-fill');
const progressLabel = document.getElementById('progress-label');
const blurTextNodes = document.querySelectorAll('[data-blur-text]');

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

function initBlurText(node) {
    const text = node.dataset.text || node.textContent || '';
    const delay = Number(node.dataset.delay || 110);
    const animateBy = node.dataset.animateBy || 'letters';
    const direction = node.dataset.direction || 'top';

    node.textContent = '';
    node.style.flexWrap = 'wrap';

    if (animateBy === 'words') {
        const words = text.split(' ');

        words.forEach((word, wordIndex) => {
            const wordSpan = document.createElement('span');
            wordSpan.className = 'blur-word';

            [...word].forEach((letter, letterIndex) => {
                const span = document.createElement('span');
                span.className = 'blur-segment';
                span.style.setProperty('--blur-delay', `${(wordIndex * delay) + (letterIndex * 22)}ms`);

                if (direction === 'bottom') {
                    span.style.transform = 'translateY(50px)';
                }

                span.textContent = letter;
                wordSpan.appendChild(span);
            });

            node.appendChild(wordSpan);
        });
    } else {
        [...text].forEach((segment, index) => {
            const span = document.createElement('span');
            span.className = 'blur-segment';
            span.style.setProperty('--blur-delay', `${index * delay}ms`);

            if (direction === 'bottom') {
                span.style.transform = 'translateY(50px)';
            }

            span.textContent = segment === ' ' ? '\u00A0' : segment;
            node.appendChild(span);
        });
    }

    const observer = new IntersectionObserver(
        ([entry], obs) => {
            if (entry.isIntersecting) {
                node.classList.add('is-visible');
                obs.unobserve(node);
            }
        },
        { threshold: 0.1, rootMargin: '0px' }
    );

    observer.observe(node);
}

function getActiveKind() {
    return body.dataset.activeForm || 'login';
}

function setActiveTab(kind) {
    body.dataset.activeForm = kind;

    tabs.forEach((tab) => {
        tab.classList.toggle('active', tab.dataset.tabTarget === kind);
    });

    panels.forEach((panel) => {
        panel.classList.toggle('active', panel.dataset.panel === kind);
    });

    updateProgress();
}

function updateProgress() {
    const kind = getActiveKind();
    const activeForm = document.querySelector(`form[data-form-kind="${kind}"]`);
    if (!activeForm || !progressLabel || !progressValue || !progressFill) return;

    const fields = [...activeForm.querySelectorAll('input:not([type="hidden"])')];
    const filled = fields.filter((field) => field.value.trim().length > 0).length;
    const percent = fields.length ? Math.round((filled / fields.length) * 100) : 0;

    progressLabel.textContent = kind === 'register' ? 'Прогресс регистрации' : 'Прогресс входа';
    progressValue.textContent = `${percent}%`;
    progressFill.style.width = `${percent}%`;
}

tabs.forEach((tab) => {
    tab.addEventListener('click', () => setActiveTab(tab.dataset.tabTarget));
});

document.querySelectorAll('form input').forEach((input) => {
    input.addEventListener('input', updateProgress);
});

blurTextNodes.forEach(initBlurText);
enhancePasswordFields();
setActiveTab(getActiveKind());
