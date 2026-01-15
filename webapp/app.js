const form = document.getElementById("pack-form");
const output = document.getElementById("output");
const salesCopy = document.getElementById("sales-copy");
const generateCta = document.getElementById("generate-cta");
const copyCta = document.getElementById("copy-cta");
const copySales = document.getElementById("copy-sales");
const downloadSales = document.getElementById("download-sales");

const toneMap = {
  friendly: {
    intro: "Friendly, welcoming, and community-first",
    emoji: "✨",
  },
  bold: {
    intro: "Direct, confident, and action-focused",
    emoji: "⚡",
  },
  luxury: {
    intro: "Premium, refined, and exclusive",
    emoji: "💎",
  },
  playful: {
    intro: "Playful, upbeat, and fun",
    emoji: "🎉",
  },
};

const goalMap = {
  bookings: "Book more appointments",
  "foot-traffic": "Drive foot traffic",
  memberships: "Sell memberships",
  reviews: "Collect 5-star reviews",
};

const templates = [
  "{emoji} {businessName} spotlight: {offer} — now in {location}.",
  "{emoji} Today only: {offer}. Tag a friend who should try {businessName}.",
  "{emoji} New here? Your first visit at {businessName} includes {offer}.",
  "{emoji} {businessType} tip of the week from {businessName}.",
  "{emoji} Local love: shoutout to our {location} community!", 
  "{emoji} Member moments: see why locals trust {businessName}.",
  "{emoji} Ask us about {offer} and we will save you a spot.",
  "{emoji} Weekend plans? {businessName} is ready for you.",
  "{emoji} Staff pick: the most-requested service this week.",
  "{emoji} Limited spots this week — book now.",
];

const hashtagSets = [
  "#{locationNoSpace} #{businessTypeNoSpace} #shoplocal #supportsmallbusiness",
  "#{businessTypeNoSpace} #{locationNoSpace} #localbusiness #discoverlocal",
  "#neighborhoodlove #{locationNoSpace} #{businessNameNoSpace}",
];

function normalizeHashtag(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "")
    .trim();
}

function createPack(data) {
  const tone = toneMap[data.tone];
  const hashtags = hashtagSets.map((set) =>
    set
      .replace("{locationNoSpace}", normalizeHashtag(data.location))
      .replace("{businessTypeNoSpace}", normalizeHashtag(data.businessType))
      .replace("{businessNameNoSpace}", normalizeHashtag(data.businessName))
  );

  const posts = Array.from({ length: 30 }, (_, index) => {
    const template = templates[index % templates.length];
    return template
      .replaceAll("{emoji}", tone.emoji)
      .replaceAll("{businessName}", data.businessName)
      .replaceAll("{businessType}", data.businessType)
      .replaceAll("{location}", data.location)
      .replaceAll("{offer}", data.offer)
      .concat("\n\n" + hashtags[index % hashtags.length]);
  });

  return {
    intro: tone.intro,
    goal: goalMap[data.goal],
    posts,
    hashtags,
  };
}

function buildOutput(pack, data) {
  const list = pack.posts
    .map((post, idx) => `<li><strong>Post ${idx + 1}:</strong><br />${post}</li>`)
    .join("");

  output.innerHTML = `
    <h3>${data.businessName} — Monthly Promo Pack</h3>
    <p class="muted">Tone: ${pack.intro} • Goal: ${pack.goal}</p>
    <ol>${list}</ol>
  `;

  const sales = `
PromoPack Studio for ${data.businessName}
\nHeadline:
"30 ready-to-post social promos every month for ${data.businessType} owners in ${data.location}."
\nSubhead:
We create the posts, you collect the bookings. Launch a full month of promos in 60 seconds.
\nWhat's included:
- 30 short-form posts written in a ${pack.intro} tone
- Weekly promo ideas & seasonal hooks
- Local hashtag sets + review prompts
- 48-hour delivery after payment
\nPricing:
$49/month for 30 posts (or $99/month for 60 posts)
\nGuarantee:
Love the first pack or get a full refund.
\nCTA:
"Claim your first month for ${data.businessName} →"
\nHow it works:
1. Pay online.
2. Receive your post pack in 48 hours.
3. Schedule posts and watch ${pack.goal.toLowerCase()}.
  `.trim();

  salesCopy.innerHTML = `<pre>${sales}</pre>`;

  return sales;
}

function collectFormData(formElement) {
  const data = Object.fromEntries(new FormData(formElement));
  return {
    businessName: data.businessName.trim(),
    businessType: data.businessType.trim(),
    location: data.location.trim(),
    offer: data.offer.trim(),
    tone: data.tone,
    goal: data.goal,
  };
}

function handleGenerate(event) {
  event?.preventDefault();
  const data = collectFormData(form);
  if (!data.businessName) {
    return;
  }
  const pack = createPack(data);
  const sales = buildOutput(pack, data);
  form.dataset.salesCopy = sales;
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(() => {
    alert("Copy failed. Please select and copy manually.");
  });
}

form.addEventListener("submit", handleGenerate);

generateCta.addEventListener("click", () => {
  form.scrollIntoView({ behavior: "smooth" });
});

copyCta.addEventListener("click", () => {
  const copyText = document.getElementById("sales-copy").innerText || "";
  copyToClipboard(copyText);
});

copySales.addEventListener("click", () => {
  const sales = form.dataset.salesCopy || "";
  copyToClipboard(sales);
});

downloadSales.addEventListener("click", () => {
  const sales = form.dataset.salesCopy || "";
  if (!sales) {
    return;
  }
  const blob = new Blob([sales], { type: "text/plain" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "sales-page-copy.txt";
  link.click();
  URL.revokeObjectURL(link.href);
});
