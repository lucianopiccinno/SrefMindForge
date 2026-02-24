// get-sref-data.js — placeholder: verifica token PRO, ritorna dataset
// In futuro: ritorna i dati SREF completi per utenti PRO autenticati

const EXPIRY = "2027-02-22";

exports.handler = async function(event) {
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json",
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 204, headers };
  }

  if (event.httpMethod !== "POST") {
    return { statusCode: 405, headers, body: JSON.stringify({ ok: false, reason: "Method not allowed" }) };
  }

  let token;
  try {
    const body = JSON.parse(event.body || "{}");
    token = (body.token || "").trim();
  } catch {
    return { statusCode: 400, headers, body: JSON.stringify({ ok: false, reason: "Invalid request" }) };
  }

  if (!token) {
    return { statusCode: 401, headers, body: JSON.stringify({ ok: false, reason: "No token" }) };
  }

  // Decodifica e verifica token
  let payload;
  try {
    payload = JSON.parse(Buffer.from(token, "base64").toString("utf-8"));
  } catch {
    return { statusCode: 401, headers, body: JSON.stringify({ ok: false, reason: "Invalid token" }) };
  }

  const expiry = new Date(payload.expiry || EXPIRY);
  if (new Date() > expiry) {
    return { statusCode: 401, headers, body: JSON.stringify({ ok: false, reason: "Token expired" }) };
  }

  // Placeholder: dataset vuoto (da espandere con dati SREF completi)
  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({ ok: true, sref: [] }),
  };
};
