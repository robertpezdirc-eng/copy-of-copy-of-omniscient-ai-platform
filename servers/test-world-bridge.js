// Test Omni World Bridge povezav
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const OmniBridge = require('../modules/omni-world-bridge');

// Fallback: preberi OpenAI ključ iz 'openai key.txt' če OPENAI_API_KEY ni nastavljen
let openAIKey = process.env.OPENAI_API_KEY;
if (!openAIKey) {
  try {
    const p = path.join(__dirname, '..', 'openai key.txt');
    openAIKey = fs.readFileSync(p, 'utf8').trim();
  } catch (e) {
    // ignore if file not found
  }
}

const cfg = {
  ibmToken: process.env.IBM_QUANTUM_TOKEN,
  ibmInstanceCrn: process.env.IBM_QUANTUM_INSTANCE_CRN,
  openAIKey,
  youtube: {
    clientId: process.env.YOUTUBE_CLIENT_ID,
    clientSecret: process.env.YOUTUBE_CLIENT_SECRET
  },
  tiktok: process.env.TIKTOK_API_KEY,
  googleDrive: {
    clientId: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET
  }
};

OmniBridge.init(cfg);

(async () => {
  console.log('\n🌉 Omni World Bridge – Test povezav\n');
  const results = await OmniBridge.activate();

  // IBM Quantum
  console.log('IBM Quantum:', JSON.stringify(results.ibmQuantum, null, 2));

  // OpenAI
  console.log('OpenAI:', JSON.stringify(results.openAI, null, 2));

  // OAuth URL-ji
  if (results.oauth) {
    console.log('\nOAuth URL-ji (odpri v brskalniku za avtorizacijo):');
    if (results.oauth.youtubeAuthUrl) console.log('YouTube:', results.oauth.youtubeAuthUrl);
    if (results.oauth.googleDriveAuthUrl) console.log('Google Drive:', results.oauth.googleDriveAuthUrl);
    if (results.oauth.tiktokAuthUrl) console.log('TikTok:', results.oauth.tiktokAuthUrl);
  }

  console.log('\n✔ Test zaključen. Če je kaj "missing_*" ali 401/403, izpolni .env vrednosti in poskusi znova.');
})();