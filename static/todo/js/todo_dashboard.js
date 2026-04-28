const blurTextNodes = document.querySelectorAll('[data-blur-text]');

function initBlurText(node) {
    const text = node.textContent.trim();
    const delay = Number(node.dataset.delay || 110);
    const animateBy = node.dataset.animateBy || 'words';
    const direction = node.dataset.direction || 'top';
    const runBlur = node.dataset.runBlur === 'true';

    node.textContent = '';

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

    if (!runBlur) {
        node.classList.add('static-visible');
        return;
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

blurTextNodes.forEach(initBlurText);
