// noinspection DuplicatedCode

function linkIsNotARedirect(link) {
    return link.target === "_blank" ||
        link.hasAttribute("download") ||
        link.origin !== window.location.origin;
}

function modifierKeyIsPressed(event) {
    return event.ctrlKey ||
        event.metaKey ||
        event.shiftKey ||
        event.altKey;
}

function loadNewPageContent(currentMainContent, nextMainContent, nextDocument, link, updateHistory = true) {
    // Replace the main content.
    currentMainContent.innerHTML = nextMainContent.innerHTML;

    // Update the header navigation so the active state updates immediately.
    const currentHeader = document.querySelector("header.site-header, header");
    const nextHeader = nextDocument.querySelector("header.site-header, header");
    if (currentHeader && nextHeader) {
        currentHeader.innerHTML = nextHeader.innerHTML;
    }

    // Update the aside if present.
    const currentAside = document.querySelector(".page-wrapper aside");
    const nextAside = nextDocument.querySelector(".page-wrapper aside");
    if (currentAside && nextAside) {
        currentAside.innerHTML = nextAside.innerHTML;
    }

    const url = typeof link === "string" ? new URL(link, window.location.origin) : link;

    // Update the browser URL.
    if (updateHistory) {
        history.pushState({}, "", url.href);
    }
    // Update the page title.
    document.title = nextDocument.title;
    // Scroll to the top of the new page.
    if (url.hash) {
        const target = document.querySelector(url.hash);
        if (target) {
            target.scrollIntoView({ behavior: "smooth" });
            document.dispatchEvent(new CustomEvent("navigation:loaded", { detail: { url } }));
            return;
        }
    }
    window.scrollTo({top: 0, behavior: "smooth"});
    document.dispatchEvent(new CustomEvent("navigation:loaded", { detail: { url } }));
}

document.addEventListener("click", async event => {
    // Find the link that was clicked.
    const link = event.target.closest("a");
    if (!link) {
        return;
    }
    if (linkIsNotARedirect(link)) {
        return;
    }
    if (modifierKeyIsPressed(event)) {
        return;
    }
    event.preventDefault();

    try {
        const response = await fetch(link.href);
        if (!response.ok) {
            throw new Error(`Unable to fetch page: HTTP ${response.status}`);
        }
        const html = await response.text();
        const parser = new DOMParser();
        const nextDocument = parser.parseFromString(html, "text/html");

        const nextMainContent = nextDocument.querySelector(".page-wrapper main");
        const currentMainContent = document.querySelector(".page-wrapper main");

        // If the page doesn't have the expected structure, fall back to normal navigation.
        if (!nextMainContent || !currentMainContent) {
            window.location.href = link.href;
            return;
        }

        loadNewPageContent(currentMainContent, nextMainContent, nextDocument, link);
    } catch (error) {
        console.error("JS Navigation failed, reverting to normal navigation:", error);
        window.location.href = link.href;
    }
});


// Handle browser back/forward buttons.
window.addEventListener(
    "popstate",
    async () => {
        try {
            const response = await fetch(window.location.href);
            let link = window.location.href;
            if (!response.ok) {
                throw new Error(`Unable to fetch page after 'popstate': HTTP ${response.status}`);
            }
            const html = await response.text();
            const parser = new DOMParser();
            const nextDocument = parser.parseFromString(html, "text/html");

            const nextMainContent = nextDocument.querySelector(".page-wrapper main");
            const currentMainContent = document.querySelector(".page-wrapper main");

            // If the page doesn't have the expected structure, fall back to normal navigation.
            if (!nextMainContent || !currentMainContent) {
                window.location.reload();
                return;
            }

            loadNewPageContent(currentMainContent, nextMainContent, nextDocument, window.location, false);
        } catch (error) {
            console.error("Back/forward navigation failed:", error);
            window.location.reload();
        }
    }
);