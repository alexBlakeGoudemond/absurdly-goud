(function () {
    let cleanup = null;

    function init() {
        if (cleanup) {
            cleanup();
            cleanup = null;
        }

        const toast = document.getElementById("guestbook-toast");
        const closeBtn = document.getElementById("guestbook-toast-close");

        if (closeBtn && toast) {
            closeBtn.addEventListener("click", function () {
                toast.hidden = true;
            });
        }

        const params = new URLSearchParams(window.location.search);
        if (params.get("signed") === "1") {
            if (toast) toast.hidden = false;
            // Clean the ?signed=1 out of the URL so a refresh doesn't re-show it
            params.delete("signed");
            const newSearch = params.toString();
            const newUrl = window.location.pathname + (newSearch ? "?" + newSearch : "") + window.location.hash;
            window.history.replaceState({}, "", newUrl);
        }

        // The CSS `.guestbook-layout` row uses align-items: flex-start (not
        // stretch), so the form's rendered height stays intrinsic to its own
        // content -- it will never grow just because the entries panel is
        // tall. That's what makes it safe to read form.offsetHeight here and
        // apply it as a cap on the entries panel below (which is what makes
        // the entries panel's overflow-y: auto scrollbar actually kick in).
        const form = document.querySelector(".guestbook-form");
        const entries = document.querySelector(".guestbook-entries");
        const mobileQuery = window.matchMedia("(max-width: 700px)");

        function syncEntriesHeight() {
            if (!form || !entries) return;

            if (mobileQuery.matches) {
                // Stacked layout: let the CSS max-height rule handle it instead.
                entries.style.height = "";
                entries.style.maxHeight = "";
                return;
            }

            const targetHeight = form.offsetHeight + "px";
            if (entries.style.height === targetHeight) return; // no-op guard: avoids any risk of a resize feedback loop

            // Override the CSS fallback max-height so it can't clamp us back
            // down if the form is taller than that fallback value.
            entries.style.maxHeight = "none";
            entries.style.height = targetHeight;
        }

        if (form && entries) {
            syncEntriesHeight();
            window.addEventListener("resize", syncEntriesHeight);
            // Catches cases where webfonts or other late-loading content shift
            // the form's rendered height after our first measurement.
            window.addEventListener("load", syncEntriesHeight);

            let observer = null;
            if (window.ResizeObserver) {
                observer = new ResizeObserver(syncEntriesHeight);
                observer.observe(form);
            }

            cleanup = function () {
                window.removeEventListener("resize", syncEntriesHeight);
                window.removeEventListener("load", syncEntriesHeight);
                if (observer) {
                    observer.disconnect();
                }
            };
        }
    }

    // Runs safely regardless of where/how this script tag is included in
    // the page (head vs body, with or without defer) -- if the DOM isn't
    // parsed yet, wait for it instead of silently finding nothing.
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    document.addEventListener("navigation:loaded", init);
})();