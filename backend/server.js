require("dotenv").config();   

const express = require("express");
const cors = require("cors");
const axios = require("axios");
const app = express();

app.use(cors());
app.use(express.json());

let contador = 0;

app.post("/chat", async (req, res) => {

    const userMessage = req.body.message;

    if (!userMessage) {
        return res.json({ reply: "Mensaje vacío ❌" });
    }

    contador++;
    if (contador > 10) {
        return res.json({ reply: "Has alcanzado el límite de preguntas 😅" });
    }

    try {
        const response = await axios.post(
            "https://api.groq.com/openai/v1/chat/completions",
            {
                model: "llama-3.1-8b-instant", // ✅ modelo actualizado
                messages: [
                    { role: "system", content: "Eres un asistente que ayuda con oposiciones en España." },
                    { role: "user", content: userMessage }
                ]
            },
            {
                headers: {
                    Authorization: `Bearer ${process.env.GROQ_API_KEY}`,
                    "Content-Type": "application/json"
                }
            }
        );

        const reply = response.data.choices[0].message.content;

        res.json({ reply });

    } catch (error) {
        console.error("🔥 ERROR REAL:");
        console.error(error.response?.data);
        console.error(error.message);

        res.status(500).json({ reply: "Error con la IA 😢" });
    }
});

app.listen(3000, () => {
    console.log("Servidor funcionando en http://localhost:3000");
});
