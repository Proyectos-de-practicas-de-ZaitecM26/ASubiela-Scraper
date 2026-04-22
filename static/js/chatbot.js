document.addEventListener("DOMContentLoaded", () => {

    const toggle = document.getElementById("chat-toggle");
    const chatbot = document.getElementById("chatbot");
    const sendBtn = document.getElementById("send-btn");
    const input = document.getElementById("input");
    const messages = document.getElementById("messages");

    // ===== ABRIR / CERRAR =====
    toggle.addEventListener("click", () => {
        chatbot.classList.toggle("hidden");
    });

    // ===== ENVIAR =====
    sendBtn.addEventListener("click", sendMessage);

    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    async function sendMessage() {

        const text = input.value.trim();
        if (!text) return;

        addMessage("Tú", text);
        input.value = "";

        const typing = addMessage("IA", "Escribiendo...");

        try {
            const res = await fetch("http://localhost:3000/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: text })
            });

            const data = await res.json();

            typing.textContent = "";
            typeEffect(typing, data.reply);

        } catch (err) {
            typing.textContent = "Error al conectar 😢";
            console.error(err);
        }
    }

    function addMessage(sender, text) {
        const div = document.createElement("div");
        div.innerHTML = `<strong>${sender}:</strong> ${text}`;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
    }

    function typeEffect(el, text) {
        let i = 0;

        const interval = setInterval(() => {
            el.textContent += text[i];
            i++;
            messages.scrollTop = messages.scrollHeight;

            if (i >= text.length) clearInterval(interval);
        }, 20);
    }

});