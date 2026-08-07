document.addEventListener("DOMContentLoaded", function () {
    const layout = document.getElementById("chatLayout");
    const content = document.getElementById("chatContent");
    const title = document.getElementById("chatTitle");
    const topic = document.getElementById("chatTopic");
    const back = document.getElementById("chatBack");
    const deleteForm = document.getElementById("chatDeleteForm");
    if (!layout || !content) return;

    function openChat(button, updateHash) {
        const source = document.getElementById(button.dataset.chatOpen);
        if (!source) return;
        document.querySelectorAll("[data-chat-open]").forEach(function (item) { item.classList.toggle("is-active", item === button); });
        title.textContent = source.dataset.chatTitle || "Sohbet";
        topic.textContent = source.dataset.chatTopic || "";
        if (deleteForm && source.dataset.conversationId) {
            deleteForm.action = "/mesajlar/konusma/" + source.dataset.conversationId + "/sil";
            deleteForm.classList.remove("d-none");
        }
        content.innerHTML = source.innerHTML;
        layout.classList.add("chat-open");
        content.scrollTop = content.scrollHeight;
        if (updateHash) history.replaceState(null, "", "#" + button.id);
        if (source.dataset.lastMessageId) {
            fetch("/api/mesajlar/" + source.dataset.lastMessageId + "/okundu", {method: "POST", headers: {"Accept": "application/json"}}).then(function (response) {
                if (!response.ok) return;
                button.classList.remove("is-unread");
                const unread = button.querySelector(".chat-unread");
                if (unread) unread.remove();
                document.dispatchEvent(new CustomEvent("muys:notifications-refresh"));
            }).catch(function () {});
        }
    }
    document.querySelectorAll("[data-chat-open]").forEach(function (button) {
        button.addEventListener("click", function () { openChat(button, true); });
    });
    if (back) back.addEventListener("click", function () { layout.classList.remove("chat-open"); });
    const selected = location.hash ? document.getElementById(location.hash.slice(1)) : null;
    if (selected && selected.matches("[data-chat-open]")) openChat(selected, false);
    else {
        const first = document.querySelector("[data-chat-open]");
        if (first && window.matchMedia("(min-width: 769px)").matches) openChat(first, false);
    }
});
