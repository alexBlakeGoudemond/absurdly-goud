(function () {
    const params = new URLSearchParams(window.location.search);
    if (params.get("signed") === "1") {
        const toast = document.getElementById("guestbook-toast");
        if (toast) toast.hidden = false;
        // Clean the ?signed=1 out of the URL so a refresh doesn't re-show it
        params.delete("signed");
        const newSearch = params.toString();
        const newUrl = window.location.pathname + (newSearch ? "?" + newSearch : "") + window.location.hash;
        window.history.replaceState({}, "", newUrl);
    }
})();
