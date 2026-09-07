/**
 * Adds click-to-collapse behaviour to Obsidian-style callouts.
 *
 * Markup produced by _includes/callout.html:
 *
 *   <div class="callout is-collapsible" data-callout="tip" data-collapsible="true">
 *     <div class="callout-title">...</div>
 *     <div class="callout-content">...</div>
 *   </div>
 *
 * Without this script, every callout renders fully expanded and stays that
 * way -- `.is-collapsible` / `data-collapsible="true"` are hooks that were
 * deliberately left inert until now (see callout.html's own comments), so
 * content was never hidden behind a toggle that didn't actually work.
 *
 * Requires the small CSS addition shipped alongside this in callouts.css:
 *   .callout.is-collapsed .callout-content { display: none; }
 *   .callout-fold-icon { ... }
 *   .callout.is-collapsed .callout-fold-icon { transform: rotate(-90deg); }
 *
 * The fold marker is preserved throughout the pipeline: the Python parser,
 * Liquid include, and rendered HTML all carry the initial state, so
 * `[!type]+` starts expanded and `[!type]-` starts collapsed.
 */
(function () {
    'use strict';

    // prevent the script from wiring listeners multiple times
    if (window.__absurdlyGoudCalloutsInitialized__) {
        return;
    }
    window.__absurdlyGoudCalloutsInitialized__ = true;

    var CHEVRON_SVG =
        '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" ' +
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
        'stroke-linejoin="round" aria-hidden="true">' +
        '<polyline points="6 9 12 15 18 9"></polyline></svg>';

    var TITLE_SELECTOR = '.callout[data-collapsible="true"] > .callout-title';

    function decorateCollapsibleCallouts() {
        var callouts = document.querySelectorAll('.callout[data-collapsible="true"]');

        callouts.forEach(function (callout) {
            callout.classList.add('is-collapsible');

            var shouldStartCollapsed = callout.getAttribute('data-initial-state') === 'collapsed';
            if (shouldStartCollapsed) {
                callout.classList.add('is-collapsed');
            } else {
                callout.classList.remove('is-collapsed');
            }

            var title = callout.querySelector('.callout-title');
            if (!title) {
                return;
            }

            // Keyboard + screen-reader affordances only get added once JS has
            // confirmed it actually runs -- a role="button" with no handler
            // behind it would be worse than no ARIA at all.
            title.setAttribute('role', 'button');
            title.setAttribute('tabindex', '0');
            title.setAttribute('aria-expanded', shouldStartCollapsed ? 'false' : 'true');

            if (!title.querySelector('.callout-fold-icon')) {
                var foldIcon = document.createElement('div');
                foldIcon.className = 'callout-fold-icon';
                foldIcon.innerHTML = CHEVRON_SVG;
                title.appendChild(foldIcon);
            }
        });
    }

    function toggleCallout(title) {
        var callout = title.closest('.callout');
        if (!callout) {
            return;
        }
        var collapsed = callout.classList.toggle('is-collapsed');
        title.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    }

    // Delegated listeners: no per-element binding needed, and this keeps
    // working even if callouts are inserted into the page after this script
    // has already run.
    document.addEventListener('click', function (event) {
        var title = event.target.closest(TITLE_SELECTOR);
        if (title) {
            toggleCallout(title);
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key !== 'Enter' && event.key !== ' ') {
            return;
        }
        var title = event.target.closest(TITLE_SELECTOR);
        if (title) {
            event.preventDefault(); // stop the page from scrolling on Space
            toggleCallout(title);
        }
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', decorateCollapsibleCallouts);
    } else {
        decorateCollapsibleCallouts();
    }
})();