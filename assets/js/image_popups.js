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

        var mediaContainer = document.createElement('div');
        mediaContainer.className = 'image-popup-media';

        var text = document.createElement('p');
        text.className = 'image-popup-text';

        var link = document.createElement('a');
        link.className = 'image-popup-link';
        link.target = '_blank';
        link.rel = 'noopener noreferrer';

        body.appendChild(mediaContainer);
        body.appendChild(text);
        body.appendChild(link);
        panel.appendChild(closeButton);
        panel.appendChild(body);
        backdrop.appendChild(panel);
        document.body.appendChild(backdrop);
    }

    function buildMediaElement(previewType, src, alt, onReady) {
        if (previewType === 'youtube' || previewType === 'vimeo') {
            var iframe = document.createElement('iframe');
            iframe.className = 'image-popup-embed';
            iframe.src = src;
            iframe.title = alt || 'Video preview';
            iframe.setAttribute(
                'allow',
                'accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share'
            );
            iframe.setAttribute('allowfullscreen', '');
            iframe.referrerPolicy = 'strict-origin-when-cross-origin';
            iframe.addEventListener('load', onReady, { once: true });
            return iframe;
        }

        if (previewType === 'video') {
            var video = document.createElement('video');
            video.className = 'image-popup-video';
            video.src = src;
            video.controls = true;
            video.playsInline = true;
            video.addEventListener('loadeddata', onReady, { once: true });
            video.addEventListener('error', onReady, { once: true });
            return video;
        }

        var image = document.createElement('img');
        image.className = 'image-popup-image';
        image.src = src;
        image.alt = alt || '';
        image.addEventListener('load', onReady, { once: true });
        image.addEventListener('error', onReady, { once: true }); // don't spin forever on a broken link
        return image;
    }

    function closePopup() {
        var backdrop = document.querySelector('.image-popup-backdrop');
        if (!backdrop) {
            return;
        }
        backdrop.classList.remove('is-open');
        backdrop.setAttribute('aria-hidden', 'true');

        // Removing (not just hiding) the media element is what actually
        // stops a playing <video> or YouTube/Vimeo <iframe> — CSS display:
        // none alone leaves audio/video running invisibly in the background.
        var mediaContainer = document.querySelector('.image-popup-media');
        if (mediaContainer) {
            mediaContainer.innerHTML = '';
            mediaContainer.classList.remove('is-loading');
        }
    }

    function openPopup(trigger) {
        ensurePopupMarkup();

        var backdrop = document.querySelector('.image-popup-backdrop');
        var mediaContainer = document.querySelector('.image-popup-media');
        var text = document.querySelector('.image-popup-text');
        var link = document.querySelector('.image-popup-link');
        if (!backdrop || !mediaContainer || !text || !link) {
            return;
        }

        var popupSrc = trigger.getAttribute('data-popup-src') || '';
        var popupBlurb = trigger.getAttribute('data-popup-blurb') || 'No details yet';
        var popupRedirectText = trigger.getAttribute('data-popup-redirect-text') || 'Learn more';
        var popupImage = trigger.getAttribute('data-popup-image') || '';
        var popupPreviewType = trigger.getAttribute('data-popup-preview-type') || 'image';
        var triggerImage = trigger.querySelector('img');
        var triggerAlt = triggerImage ? triggerImage.alt : '';

        mediaContainer.innerHTML = '';
        if (popupImage) {
            mediaContainer.classList.add('is-loading');
            var mediaElement = buildMediaElement(popupPreviewType, popupImage, triggerAlt, function () {
                mediaContainer.classList.remove('is-loading');
            });
            mediaContainer.appendChild(mediaElement);
        } else {
            mediaContainer.classList.remove('is-loading');
        }

        text.textContent = popupBlurb;
        link.href = popupSrc;
        link.textContent = popupRedirectText + ' →';

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