function normalizeText(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim();
}

function slugify(value) {
  return normalizeText(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function extractBrand(title) {
  const normalized = normalizeText(title);
  const [firstWord] = normalized.split(" ");
  return firstWord || null;
}

function normalizeProductIdentity({ retailer, title }) {
  const cleanTitle = normalizeText(title);
  return {
    title: cleanTitle,
    normalizedBrand: extractBrand(cleanTitle),
    normalizedModel: slugify(cleanTitle),
    canonicalKey: `${retailer}:${slugify(cleanTitle)}`
  };
}

module.exports = {
  normalizeProductIdentity,
  normalizeText,
  slugify
};
