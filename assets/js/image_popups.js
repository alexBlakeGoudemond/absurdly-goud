(function () {
    'use strict';

    if (window.__absurdlyGoudImagePopupsInitialized__) {
        return;
    }
    window.__absurdlyGoudImagePopupsInitialized__ = true;

    function ensurePopupMarkup() {
        if (document.querySelector('.image-popup-backdrop')) {
            return;
        }

        var backdrop = document.createElement('div');
        backdrop.className = 'image-popup-backdrop';
        backdrop.setAttribute('aria-hidden', 'true');

        var panel = document.createElement('div');
        panel.className = 'image-popup-panel';
        panel.setAttribute('role', 'dialog');
        panel.setAttribute('aria-modal', 'true');

        var closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'image-popup-close';
        closeButton.setAttribute('aria-label', 'Close popup');
        closeButton.textContent = '×';

        var body = document.createElement('div');
        body.className = 'image-popup-body';

        var text = document.createElement('p');
        text.className = 'image-popup-text';

        var link = document.createElement('a');
        link.className = 'image-popup-link';
        link.target = '_blank';
        link.rel = 'noopener noreferrer';

        body.appendChild(text);
        body.appendChild(link);
        panel.appendChild(closeButton);
        panel.appendChild(body);
        backdrop.appendChild(panel);
        document.body.appendChild(backdrop);
    }

    function closePopup() {
        var backdrop = document.querySelector('.image-popup-backdrop');
        if (!backdrop) {
            return;
        }
        backdrop.classList.remove('is-open');
        backdrop.setAttribute('aria-hidden', 'true');
    }

    function openPopup(trigger) {
        ensurePopupMarkup();

        var backdrop = document.querySelector('.image-popup-backdrop');
        var text = document.querySelector('.image-popup-text');
        var link = document.querySelector('.image-popup-link');
        if (!backdrop || !text || !link) {
            return;
        }

        var popupSrc = trigger.getAttribute('data-popup-src') || '';
        var popupBlurb = trigger.getAttribute('data-popup-blurb') || 'No details yet';

        text.textContent = popupBlurb;
        link.href = popupSrc;
        link.textContent = popupSrc && popupSrc.indexOf('http') === 0 ? 'Learn more →' : 'View source →';

        backdrop.classList.add('is-open');
        backdrop.setAttribute('aria-hidden', 'false');
    }

    document.addEventListener('click', function (event) {
        var trigger = event.target.closest('.image-popup-trigger');
        if (trigger) {
            event.preventDefault();
            openPopup(trigger);
            return;
        }

        var closeButton = event.target.closest('.image-popup-close');
        if (closeButton) {
            closePopup();
            return;
        }

        var backdrop = event.target.closest('.image-popup-backdrop');
        if (backdrop && event.target === backdrop) {
            closePopup();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            closePopup();
        }
    });
})();
