// brainActivity.js
require('dotenv').config();
const { Configuration, OpenAIApi } = require("openai");

// Preveri, da imamo OpenAI ključ
if (!process.env.OPENAI_API_KEY) {
    console.error("⚠️ NIMA nastavljenega OpenAI ključa v .env!");
    process.exit(1);
}

const configuration = new Configuration({
    apiKey: process.env.OPENAI_API_KEY,
});

const openai = new OpenAIApi(configuration);

/**
 * Pošlje prompt na OpenAI in vrne odgovor
 * @param {string} prompt - vprašanje za AI
 * @returns {Promise<string>} - AI odgovor
 */
async function askOpenAI(prompt) {
    try {
        const response = await openai.createChatCompletion({
            model: "gpt-5-mini",
            messages: [
                { role: "system", content: "Ti si Omni Brain, inteligentni pomočnik." },
                { role: "user", content: prompt }
            ],
            temperature: 0.7,
        });

        const answer = response.data.choices[0].message.content.trim();
        return answer;

    } catch (error) {
        console.error("Napaka pri klicu OpenAI:", error);
        return "Oprostite, prišlo je do napake pri komunikaciji z OpenAI.";
    }
}

module.exports = { askOpenAI };
