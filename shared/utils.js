function timestampUtc() {
  return new Date().toISOString();
}

function safeParseJson(str) {
  try {
    return JSON.parse(str);
  } catch (e) {
    return null;
  }
}

module.exports = {
  timestampUtc,
  safeParseJson,
};