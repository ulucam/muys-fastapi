document.addEventListener("DOMContentLoaded", function () {
    const modalElement = document.getElementById("conversationModal");
    const modalBody = document.getElementById("conversationModalBody");
    const modalTitle = document.getElementById("conversationModalTitle");
    if (!modalElement || !window.bootstrap) return;
    const modal = window.bootstrap.Modal.getOrCreateInstance(modalElement);

    function openConversation(button) {
        const source = document.getElementById(button.dataset.conversationOpen);
        if (!source) return;
        modalTitle.textContent = button.dataset.conversationTitle || "Konuşma";
        modalBody.innerHTML = source.innerHTML;
        modal.show();
    }
    document.querySelectorAll("[data-conversation-open]").forEach(function (button) {
        button.addEventListener("click", function () { openConversation(button); });
    });
    const hashTarget = location.hash ? document.getElementById(location.hash.slice(1)) : null;
    if (hashTarget && hashTarget.matches("[data-conversation-open]")) openConversation(hashTarget);
});
