const body = document.body;
const tabs = document.querySelectorAll('[data-tab-target]');
const panels = document.querySelectorAll('.form-panel');
const progressValue = document.getElementById('progress-value');
const progressFill = document.getElementById('progress-fill');
const progressLabel = document.getElementById('progress-label');
const blurTextNodes = document.querySelectorAll('[data-blur-text]');
const rotatingTextNodes = document.querySelectorAll('[data-rotating-text]');

function splitIntoCharacters(text) {
    if (typeof Intl !== 'undefined' && Intl.Segmenter) {
        const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
        return Array.from(segmenter.segment(text), (segment) => segment.segment);
    }

    return Array.from(text);
}

function getStaggerDelay(index, total, staggerFrom, staggerDuration) {
    if (staggerFrom === 'last') return (total - 1 - index) * staggerDuration;
    if (staggerFrom === 'center') {
        const center = Math.floor(total / 2);
        return Math.abs(center - index) * staggerDuration;
    }
    if (staggerFrom === 'random') {
        const randomIndex = Math.floor(Math.random() * total);
        return Math.abs(randomIndex - index) * staggerDuration;
    }

    const numericStart = Number(staggerFrom);
    if (!Number.isNaN(numericStart)) return Math.abs(numericStart - index) * staggerDuration;

    return index * staggerDuration;
}

function buildRotatingLine(text, staggerFrom, staggerDuration) {
    const line = document.createElement('span');
    const word = document.createElement('span');
    const characters = splitIntoCharacters(text);

    line.className = 'rotating-text-line';
    word.className = 'rotating-text-word';

    characters.forEach((character, index) => {
        const element = document.createElement('span');
        element.className = 'rotating-text-element';
        element.textContent = character;
        element.style.setProperty(
            '--rotate-delay',
            `${getStaggerDelay(index, characters.length, staggerFrom, staggerDuration)}ms`
        );
        word.appendChild(element);
    });

    line.appendChild(word);
    return line;
}

function initRotatingText(node) {
    const words = (node.dataset.rotatingWords || node.textContent || '')
        .split(',')
        .map((word) => word.trim())
        .filter(Boolean);
    const stage = node.querySelector('.rotating-text-stage') || node;
    const srOnly = node.querySelector('.rotating-text-sr-only');
    const interval = Number(node.dataset.rotationInterval || 2000);
    const staggerFrom = node.dataset.staggerFrom || 'first';
    const staggerDuration = Number(node.dataset.staggerDuration || 28);
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let currentIndex = 0;
    let currentLine = null;

    if (!words.length) return;

    node.style.setProperty('--rotating-width', `${Math.max(...words.map((word) => word.length)) * 0.64}em`);
    stage.textContent = '';

    function render(index, exitingLine = null) {
        const line = buildRotatingLine(words[index], staggerFrom, staggerDuration);
        if (srOnly) srOnly.textContent = words[index];

        if (exitingLine) {
            exitingLine.classList.add('is-exiting');
            window.setTimeout(() => exitingLine.remove(), 560);
        }

        stage.appendChild(line);
        currentLine = line;
    }

    render(currentIndex);

    if (reduceMotion || words.length === 1) return;

    window.setInterval(() => {
        const previousLine = currentLine;
        currentIndex = currentIndex === words.length - 1 ? 0 : currentIndex + 1;
        render(currentIndex, previousLine);
    }, interval);
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
rotatingTextNodes.forEach(initRotatingText);
setActiveTab(getActiveKind());
