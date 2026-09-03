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

function loadNewPageContent(currentMainContent, nextMainContent, nextDocument, link) {
    // Replace only the main content.
    currentMainContent.innerHTML = nextMainContent.innerHTML;
    // Update the browser URL.
    history.pushState({}, "", link.href);
    // Update the page title.
    document.title = nextDocument.title;
    // Scroll to the top of the new page.
    window.scrollTo({top: 0, behavior: "smooth"});
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

            loadNewPageContent(currentMainContent, nextMainContent, nextDocument, link);
        } catch (error) {
            console.error("Back/forward navigation failed:", error);
            window.location.reload();
        }
    }
);