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
})();
