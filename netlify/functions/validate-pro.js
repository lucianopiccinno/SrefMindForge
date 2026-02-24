// validate-pro.js — verifica codici PRO SrefMindForge
// Ritorna {valid: true, token: "..."} o {valid: false, reason: "..."}

const EXPIRY = "2027-02-22";

// 99 codici attivi (blacklistati esclusi)
const PRO_CODES = new Set([
  "smf-2we5-rdb8-xhe9ex",
  "smf-2x2b-t7f5-kdktpe",
  "smf-3a9y-sd2h-2zdgk8",
  "smf-3kzf-872d-nx96ca",
  "smf-3wm8-462w-hwe2m7",
  "smf-432h-dd2p-yhuhbx",
  "smf-4vpz-gvf6-xsxr3d",
  "smf-4wzk-6hyf-3ntr2e",
  "smf-5b3v-uppy-urdxn8",
  "smf-5qnc-pecw-d95gp2",
  "smf-5s9k-new9-48dun8",
  "smf-5yjq-xtz2-tghs9z",
  "smf-63p7-gwst-skvwq7",
  "smf-68pd-7t27-qwjapx",
  "smf-6ekv-as8d-f28xdv",
  "smf-6qau-dcxd-xcsjp2",
  "smf-7mjp-86c9-3543a6",
  "smf-7y7s-py62-g79pru",
  "smf-89fu-5ju6-z95t56",
  "smf-89nu-xxck-wmetbs",
  "smf-8ner-bw92-guyzsc",
  "smf-8pxx-m328-d8qgxq",
  "smf-8yb4-fcgr-nsrkgp",
  "smf-8ysu-m7qt-sb7xyb",
  "smf-99pu-ev6t-d494fr",
  "smf-9fft-2q27-emkatr",
  "smf-9mse-wbfr-x9atz6",
  "smf-9wx4-2bkn-rufdkw",
  "smf-9zby-6zs3-u5fpah",
  "smf-a2t5-hpga-tnjdzs",
  "smf-a3dz-nwfb-r4ewmr",
  "smf-b4jj-zjqy-nkyas3",
  "smf-b4mu-z22r-byrp7n",
  "smf-be5r-8bxp-zv342a",
  "smf-bpdj-9g95-e9vbhk",
  "smf-bsxp-65bh-nppva7",
  "smf-c8bt-knt8-nvq7hk",
  "smf-ccrp-xmmv-efc8w7",
  "smf-cnjw-6hjz-jg7e4p",
  "smf-deya-pq3p-ta3dw6",
  "smf-drcg-xhqy-6pp7w6",
  "smf-e8au-223k-55k6k2",
  "smf-ecy4-bbrn-f53adc",
  "smf-enfq-5ngn-ma375e",
  "smf-f7ut-jnjr-jmbv2y",
  "smf-gh45-5sve-jyu33g",
  "smf-gm82-hezz-junn5n",
  "smf-grxf-qb64-g9bejj",
  "smf-hf82-7dz7-7z7k66",
  "smf-huz5-5bd3-frhs2e",
  "smf-j26w-dtqh-q8qz43",
  "smf-jn8p-vrk4-czuzbx",
  "smf-jpjm-6ayb-6dby9f",
  "smf-kpfg-28fg-5vsj9u",
  "smf-kpnk-z5za-pfqqac",
  "smf-kvb5-but8-f39tzq",
  "smf-mabm-6phz-9uxbgx",
  "smf-mcyp-s4qu-2ftvdc",
  "smf-mg65-qz34-bc6rs7",
  "smf-mq6a-u9n7-6cj4v2",
  "smf-ms29-4wuq-9fky4j",
  "smf-nehe-tfz9-9bpuu5",
  "smf-nrra-zwu9-tjku5p",
  "smf-ntxs-ay8r-e8xvvt",
  "smf-nyfu-75y2-3mv9tb",
  "smf-p84h-547e-unv3td",
  "smf-pbg4-9353-8wkex2",
  "smf-pms3-vysw-juskmh",
  "smf-pp92-gur7-7v89g2",
  "smf-pycd-j3zw-rtxs9y",
  "smf-q4e9-mgh2-48huve",
  "smf-qv7h-ssu9-jy9557",
  "smf-r792-mkva-zeg8h6",
  "smf-rk73-ehrc-4876sv",
  "smf-rmhc-hsfp-gbaf6w",
  "smf-rmrr-nay8-cftstp",
  "smf-rmtq-4sbx-p85sgg",
  "smf-ru5r-h7xa-w8turf",
  "smf-t3q2-razu-utv9x3",
  "smf-tmjg-d8d5-depkau",
  "smf-tndb-ax7t-d59ycj",
  "smf-tuw2-afzu-qdxyhp",
  "smf-ub5h-dyyv-vrsk8t",
  "smf-upky-penz-qepgb7",
  "smf-vedt-j3xt-jtmvjv",
  "smf-vuqf-dxhq-45djum",
  "smf-w64j-2trd-2b2ed7",
  "smf-x4wk-mxw9-2hauhq",
  "smf-x64g-2266-ctypna",
  "smf-xwx3-89kr-wwky2g",
  "smf-xzq8-5njn-2dkbeq",
  "smf-y299-mdjz-pyzdya",
  "smf-y5ye-dz2p-fw7dvv",
  "smf-y9v6-p5b4-vnx425",
  "smf-yant-hrae-y99t3h",
  "smf-z3kz-h54f-52agqp",
  "smf-z4gf-mzns-7zjdkk",
  "smf-zwkp-56qe-a8rgvc",
  "smf-zzgt-tzze-56cayt",
]);

exports.handler = async function(event) {
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json",
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 204, headers };
  }

  if (event.httpMethod !== "POST") {
    return { statusCode: 405, headers, body: JSON.stringify({ valid: false, reason: "Method not allowed" }) };
  }

  let code;
  try {
    const body = JSON.parse(event.body || "{}");
    code = (body.code || "").trim().toLowerCase();
  } catch {
    return { statusCode: 400, headers, body: JSON.stringify({ valid: false, reason: "Invalid request" }) };
  }

  if (!code) {
    return { statusCode: 400, headers, body: JSON.stringify({ valid: false, reason: "No code provided" }) };
  }

  // Verifica scadenza
  const now = new Date();
  const expiry = new Date(EXPIRY);
  if (now > expiry) {
    return { statusCode: 200, headers, body: JSON.stringify({ valid: false, reason: "All codes expired" }) };
  }

  if (!PRO_CODES.has(code)) {
    return { statusCode: 200, headers, body: JSON.stringify({ valid: false, reason: "Invalid code" }) };
  }

  // Token base64: payload JSON con codice e scadenza
  const payload = Buffer.from(JSON.stringify({ code, expiry: EXPIRY, ts: now.toISOString() })).toString("base64");

  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({ valid: true, token: payload }),
  };
};
