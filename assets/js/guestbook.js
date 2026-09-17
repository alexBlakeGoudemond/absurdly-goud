(function () {
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

    // Flexbox `align-items: stretch` only equalizes height to whichever
    // side is taller -- if the entries list has more content than the
    // form, the form grows to match it instead of the entries panel being
    // capped and scrolling. So we measure the form's real rendered height
    // and apply that as an explicit cap on the entries panel, which is
    // what actually makes its internal overflow-y: auto kick in.
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

        // Override the CSS fallback max-height so it can't clamp us back
        // down if the form is taller than that fallback value.
        entries.style.maxHeight = "none";
        entries.style.height = form.offsetHeight + "px";
    }

    if (form && entries) {
        syncEntriesHeight();
        window.addEventListener("resize", syncEntriesHeight);

        if (window.ResizeObserver) {
            new ResizeObserver(syncEntriesHeight).observe(form);
        }
    }
})();