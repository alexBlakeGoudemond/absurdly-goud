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
 * Known limitation: Obsidian's `[!type]+` / `[!type]-` syntax distinguishes
 * "starts expanded" from "starts collapsed", but that distinction isn't
 * carried through the current pipeline (callouts.py only ever emits a
 * boolean `collapsible`, not an initial state) -- every collapsible callout
 * starts expanded here. Supporting a collapsed default would mean adding
 * e.g. a `data-initial-state` attribute all the way through Python ->
 * Liquid -> HTML -> here.
 */
(function () {
    'use strict';

    var CHEVRON_SVG =
        '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" ' +
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
        'stroke-linejoin="round" aria-hidden="true">' +
        '<polyline points="6 9 12 15 18 9"></polyline></svg>';

    var TITLE_SELECTOR = '.callout.is-collapsible > .callout-title';

    function decorateCollapsibleCallouts() {
        var titles = document.querySelectorAll(TITLE_SELECTOR);

        titles.forEach(function (title) {
            // Keyboard + screen-reader affordances only get added once JS has
            // confirmed it actually runs -- a role="button" with no handler
            // behind it would be worse than no ARIA at all.
            title.setAttribute('role', 'button');
            title.setAttribute('tabindex', '0');
            title.setAttribute('aria-expanded', 'true');

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