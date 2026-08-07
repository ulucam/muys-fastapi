document.addEventListener("DOMContentLoaded", function () {
    const layout = document.getElementById("chatLayout");
    const content = document.getElementById("chatContent");
    const title = document.getElementById("chatTitle");
    const topic = document.getElementById("chatTopic");
    const back = document.getElementById("chatBack");
    if (!layout || !content) return;

    function openChat(button, updateHash) {
        const source = document.getElementById(button.dataset.chatOpen);
        if (!source) return;
        document.querySelectorAll("[data-chat-open]").forEach(function (item) { item.classList.toggle("is-active", item === button); });
        title.textContent = source.dataset.chatTitle || "Sohbet";
        topic.textContent = source.dataset.chatTopic || "";
        content.innerHTML = source.innerHTML;
        layout.classList.add("chat-open");
        content.scrollTop = content.scrollHeight;
        if (updateHash) history.replaceState(null, "", "#" + button.id);
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
