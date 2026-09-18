"use strict";

const RELEASE_FILE = "data/atlas_public_v1_1.json";

const EXPECTED = {
  accessions: 70,
  canonicalEntities: 64,
  publicFields: 25,
};

let DATA = [];
let METRICS = {};
let filteredData = [];
let charts = [];
let sortKey = "dataset_id";
let sortDirection = 1;
let lastFocusedElement = null;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, character => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[character]);
}

function displayValue(value) {
  return value ? escapeHtml(value) : '<span class="na">Not available</span>';
}

function formatInteger(value) {
  const number = Number.parseInt(value, 10);
  return Number.isNaN(number) ? value : number.toLocaleString("en-US");
}

function humanize(value) {
  const labels = {
    case_control: "Case-control",
    cross_sectional: "Cross-sectional",
    multi_amplicon: "Multi-amplicon",
    multi_assay: "Multi-assay",
    multi_omic: "Multi-omic",
    gut: "Gut",
    "gut;oral": "Gut and oral",
    oral: "Oral",
    stool: "Stool",
    included: "Included",
    included_partial_overlap: "Included, partial overlap",
    included_partial_public: "Included, partial public release",
    metadata_only: "Metadata only",
    repository_mirror_or_alternate_release: "Repository mirror / alternate release",
    yes: "Yes",
    no: "No",
    partial: "Partial",
    unknown: "Unknown",
  };
  return labels[value] || String(value || "Unknown").replaceAll("_", " ");
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`Could not load ${url}: HTTP ${response.status}`);
  return response.json();
}

function requireValue(condition, message) {
  if (!condition) throw new Error(message);
}

function validateRows(rows) {
  requireValue(rows.length === EXPECTED.accessions, `Expected 70 public rows; found ${rows.length}`);
  requireValue(Object.keys(rows[0] || {}).length === EXPECTED.publicFields, "Public schema must contain 25 fields");

  const datasetIds = rows.map(row => row.dataset_id);
  requireValue(new Set(datasetIds).size === rows.length, "Public dataset IDs must be unique");

  const canonicalCount = new Set(rows.map(row => row.canonical_dataset_id).filter(Boolean)).size;
  requireValue(canonicalCount === EXPECTED.canonicalEntities, `Expected 64 canonical entities; found ${canonicalCount}`);

  const byId = new Map(rows.map(row => [row.dataset_id, row]));
  const checks = {
    SCR00048: { raw_data_public: "no", record_status: "metadata_only" },
    SCR00124: { n_total: "82", raw_data_public: "yes", record_status: "included_partial_overlap" },
    SCR00158: { study_design: "intervention", sequencing_platform: "Illumina MiniSeq", record_status: "included" },
    SCR00180: { assay_type: "multi_omic", record_status: "included" },
  };
  Object.entries(checks).forEach(([datasetId, fields]) => {
    const row = byId.get(datasetId);
    requireValue(Boolean(row), `Missing critical record ${datasetId}`);
    Object.entries(fields).forEach(([field, expected]) => {
      requireValue(row[field] === expected, `${datasetId}.${field} failed the frozen-value check`);
    });
  });
}

function countBy(rows, key) {
  return rows.reduce((counts, row) => {
    const value = row[key] || "unknown";
    counts[value] = (counts[value] || 0) + 1;
    return counts;
  }, {});
}

function uniqueValues(key) {
  return [...new Set(DATA.map(row => row[key]).filter(Boolean))].sort((a, b) => a.localeCompare(b));
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function updateSummary() {
  const publicationLinked = DATA.filter(row => row.paper_verified === "yes").length;
  const repositoryOnly = DATA.length - publicationLinked;
  const canonical = new Set(DATA.map(row => row.canonical_dataset_id).filter(Boolean)).size;
  const countries = uniqueValues("country").length;
  const downloadable = DATA.filter(row => row.downloadable_asd_control_pair === "yes").length;

  setText("sc-identified", formatInteger(METRICS.records_identified));
  setText("sc-screened", formatInteger(METRICS.records_screened));
  setText("sc-accessions", String(DATA.length));
  setText("sc-canonical", String(canonical));
  setText("sc-countries", String(countries));
  setText("sc-paper", String(publicationLinked));
  setText("sc-downloadable", String(downloadable));
  setText("hb-accessions", `${DATA.length} accession records`);
  setText("hb-canonical", `${canonical} provisional canonical entities`);
  setText("hb-paper", `${publicationLinked} records with verified publication linkage`);
  setText("hb-repo", `${repositoryOnly} repository-only records`);

  const contributionTotal = Number(METRICS.overlap_adjusted_asd) + Number(METRICS.overlap_adjusted_controls);
  setText(
    "contribution-total",
    `${formatInteger(METRICS.overlap_adjusted_asd)} ASD + ${formatInteger(METRICS.overlap_adjusted_controls)} controls = ${formatInteger(contributionTotal)}`,
  );
}

function chartData(counts, order = []) {
  const entries = Object.entries(counts);
  if (order.length) {
    entries.sort((a, b) => {
      const aIndex = order.indexOf(a[0]);
      const bIndex = order.indexOf(b[0]);
      if (aIndex === -1 && bIndex === -1) return b[1] - a[1];
      if (aIndex === -1) return 1;
      if (bIndex === -1) return -1;
      return aIndex - bIndex;
    });
  } else {
    entries.sort((a, b) => b[1] - a[1]);
  }
  return {
    labels: entries.map(([label]) => humanize(label)),
    values: entries.map(([, value]) => value),
  };
}

function makeChart(canvasId, type, data, options = {}) {
  const palette = ["#1c6eaa", "#168b87", "#d8902e", "#7b6aa7", "#ba4b3e", "#58a36d", "#557589", "#d06d4e", "#7698c7", "#a8a85d"];
  return new Chart(document.getElementById(canvasId), {
    type,
    data: {
      labels: data.labels,
      datasets: [{ data: data.values, backgroundColor: palette, borderColor: "#fffdf8", borderWidth: type === "doughnut" ? 2 : 0, borderRadius: type === "bar" ? 4 : 0 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: type === "doughnut", position: "bottom", labels: { boxWidth: 12, usePointStyle: true } },
        tooltip: { callbacks: { label: context => `${context.label}: ${context.raw} records` } },
      },
      scales: type === "bar" ? { x: { beginAtZero: true, ticks: { precision: 0 } }, y: { grid: { display: false } } } : {},
      ...options,
    },
  });
}

function buildCharts() {
  charts.forEach(chart => chart.destroy());
  charts = [];

  const countryEntries = Object.entries(countBy(DATA, "country")).sort((a, b) => b[1] - a[1]).slice(0, 10);
  charts.push(makeChart("cCountry", "bar", {
    labels: countryEntries.map(([country]) => country),
    values: countryEntries.map(([, count]) => count),
  }, { indexAxis: "y", plugins: { legend: { display: false } } }));

  charts.push(makeChart("cSite", "doughnut", chartData(countBy(DATA, "body_site"), ["stool", "oral", "gut", "gut;oral"])));
  charts.push(makeChart("cAssay", "doughnut", chartData(countBy(DATA, "assay_type"), ["16S", "metagenome", "multi_amplicon", "multi_assay", "multi_omic", "shotgun"])));
  charts.push(makeChart("cDesign", "doughnut", chartData(countBy(DATA, "study_design"), ["case_control", "intervention", "cross_sectional"])));
  charts.push(makeChart("cSource", "doughnut", chartData(countBy(DATA, "source_db"), ["BioProject", "Qiita", "ENA"])));
}

function setSelectOptions(id, values) {
  const select = document.getElementById(id);
  const defaultOption = select.options[0].cloneNode(true);
  select.replaceChildren(defaultOption);
  values.forEach(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = humanize(value);
    select.appendChild(option);
  });
}

function setupFilters() {
  setSelectOptions("fAssay", uniqueValues("assay_type"));
  setSelectOptions("fSite", uniqueValues("body_site"));
  setSelectOptions("fDesign", uniqueValues("study_design"));
  setSelectOptions("fStatus", uniqueValues("record_status"));
  setSelectOptions("fCountry", uniqueValues("country"));
  setSelectOptions("fRaw", uniqueValues("raw_data_public"));
  setSelectOptions("fPair", uniqueValues("downloadable_asd_control_pair"));

  ["q", "fAssay", "fSite", "fDesign", "fStatus", "fCountry", "fRaw", "fPair"].forEach(id => {
    document.getElementById(id).addEventListener(id === "q" ? "input" : "change", applyFilters);
  });
  document.getElementById("clearFilters").addEventListener("click", () => {
    document.getElementById("q").value = "";
    ["fAssay", "fSite", "fDesign", "fStatus", "fCountry", "fRaw", "fPair"].forEach(id => {
      document.getElementById(id).value = "";
    });
    applyFilters();
  });
}

function applyFilters() {
  const query = document.getElementById("q").value.trim().toLowerCase();
  const filters = {
    assay_type: document.getElementById("fAssay").value,
    body_site: document.getElementById("fSite").value,
    study_design: document.getElementById("fDesign").value,
    record_status: document.getElementById("fStatus").value,
    country: document.getElementById("fCountry").value,
    raw_data_public: document.getElementById("fRaw").value,
    downloadable_asd_control_pair: document.getElementById("fPair").value,
  };

  filteredData = DATA.filter(row => {
    if (Object.entries(filters).some(([key, value]) => value && row[key] !== value)) return false;
    if (!query) return true;
    const haystack = [
      row.dataset_id,
      row.accession,
      row.dataset_title,
      row.linked_accessions,
      row.linked_publications,
      row.publication_title,
      row.doi,
      row.pmid,
      row.country,
      row.source_db,
      row.canonical_dataset_id,
    ].join(" ").toLowerCase();
    return haystack.includes(query);
  });
  renderTable();
}

function tag(value, tone = "neutral", label = null) {
  return `<span class="tag ${tone}">${escapeHtml(label || humanize(value))}</span>`;
}

function stateTag(value) {
  if (value === "yes") return tag(value, "ok");
  if (value === "no") return tag(value, "warn");
  return tag(value, "neutral");
}

function recordStatusTag(value) {
  if (value === "included") return tag(value, "ok");
  if (value === "metadata_only") return tag(value, "danger");
  return tag(value, "warn");
}

function accessionUrl(accession, sourceDb) {
  if (!accession) return null;
  if (sourceDb === "Qiita") return `https://qiita.ucsd.edu/study/description/${encodeURIComponent(accession)}`;
  if (sourceDb === "ENA" || accession.startsWith("PRJEB") || accession.startsWith("ERP") || accession.startsWith("SRP")) return `https://www.ebi.ac.uk/ena/browser/view/${encodeURIComponent(accession)}`;
  if (accession.startsWith("PRJ")) return `https://www.ncbi.nlm.nih.gov/bioproject/${encodeURIComponent(accession)}`;
  if (accession.startsWith("GSE")) return `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=${encodeURIComponent(accession)}`;
  return null;
}

function accessionLink(row) {
  const url = row.url || accessionUrl(row.accession, row.source_db);
  if (!row.accession) return '<span class="na">Not available</span>';
  return `<a class="accession-link" href="${escapeHtml(url || "#")}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">${escapeHtml(row.accession)}</a>`;
}

function renderTable() {
  const rows = [...filteredData].sort((left, right) => {
    const leftValue = left[sortKey] || "";
    const rightValue = right[sortKey] || "";
    const leftNumber = Number.parseFloat(leftValue);
    const rightNumber = Number.parseFloat(rightValue);
    if (!Number.isNaN(leftNumber) && !Number.isNaN(rightNumber)) return sortDirection * (leftNumber - rightNumber);
    return sortDirection * leftValue.localeCompare(rightValue);
  });

  setText("tcnt", `${rows.length} of ${DATA.length} accession records`);
  document.getElementById("tbody").innerHTML = rows.map(row => {
    return `<tr tabindex="0" data-record="${escapeHtml(row.dataset_id)}">
      <td>${escapeHtml(row.dataset_id)}</td>
      <td>${accessionLink(row)}</td>
      <td>${displayValue(row.canonical_dataset_id)}</td>
      <td>${escapeHtml(row.dataset_title)}</td>
      <td>${displayValue(row.country)}</td>
      <td>${displayValue(humanize(row.body_site))}</td>
      <td>${tag(row.assay_type, "info")}</td>
      <td>${displayValue(humanize(row.study_design))}</td>
      <td>${displayValue(formatInteger(row.n_total))}</td>
      <td>${stateTag(row.paper_verified)}</td>
      <td>${stateTag(row.raw_data_public)}</td>
      <td>${stateTag(row.downloadable_asd_control_pair)}</td>
      <td>${recordStatusTag(row.record_status)}</td>
    </tr>`;
  }).join("");
}

function field(label, value, full = false) {
  if (!value) return "";
  return `<div class="field${full ? " full" : ""}"><div class="field-key">${escapeHtml(label)}</div><div class="field-value">${escapeHtml(value)}</div></div>`;
}

function modalLinks(row) {
  const links = [];
  const mainUrl = row.url || accessionUrl(row.accession, row.source_db);
  if (row.accession && mainUrl) links.push(`<a href="${escapeHtml(mainUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(row.accession)}</a>`);
  (row.linked_accessions || "").split(/[;|]/).map(value => value.trim()).filter(Boolean).forEach(accession => {
    const url = accessionUrl(accession, row.source_db);
    if (url) links.push(`<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(accession)}</a>`);
  });
  if (row.pmid) links.push(`<a href="https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(row.pmid)}/" target="_blank" rel="noopener noreferrer">PubMed ${escapeHtml(row.pmid)}</a>`);
  if (row.doi) links.push(`<a href="https://doi.org/${encodeURIComponent(row.doi)}" target="_blank" rel="noopener noreferrer">DOI</a>`);
  return links.join("");
}

function openModal(datasetId) {
  const row = DATA.find(item => item.dataset_id === datasetId);
  if (!row) return;
  lastFocusedElement = document.activeElement;
  setText("modalTitle", row.dataset_title);
  document.getElementById("modalLinks").innerHTML = modalLinks(row);
  document.getElementById("modalFields").innerHTML = [
    field("Dataset ID", row.dataset_id),
    field("Accession", row.accession),
    field("Canonical dataset ID", row.canonical_dataset_id),
    field("Source database", row.source_db),
    field("Study country", row.country),
    field("Study design", humanize(row.study_design)),
    field("Study-reported total", row.n_total),
    field("Study-reported ASD", row.n_asd),
    field("Study-reported controls", row.n_control),
    field("Body site", humanize(row.body_site)),
    field("Assay type", humanize(row.assay_type)),
    field("Sequencing platform", row.sequencing_platform),
    field("Raw data public", humanize(row.raw_data_public)),
    field("Downloadable ASD/control pair", humanize(row.downloadable_asd_control_pair)),
    field("Record status", humanize(row.record_status)),
    field("Linked publication", row.linked_publications, true),
    field("Publication title", row.publication_title, true),
  ].join("");
  const overlay = document.getElementById("modalOverlay");
  overlay.hidden = false;
  document.body.style.overflow = "hidden";
  document.getElementById("modalClose").focus();
}

function closeModal() {
  document.getElementById("modalOverlay").hidden = true;
  document.body.style.overflow = "";
  if (lastFocusedElement) lastFocusedElement.focus();
}

function setupInteraction() {
  document.querySelectorAll(".nav-link").forEach(button => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".nav-link").forEach(item => {
        const active = item === button;
        item.classList.toggle("active", active);
        if (active) item.setAttribute("aria-current", "page");
        else item.removeAttribute("aria-current");
      });
      document.querySelectorAll(".page-section").forEach(section => {
        const active = section.id === `s-${button.dataset.section}`;
        section.hidden = !active;
        section.classList.toggle("active", active);
      });
      if (button.dataset.section === "overview") {
        requestAnimationFrame(() => charts.forEach(chart => chart.resize()));
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  document.querySelectorAll("th button[data-sort]").forEach(button => {
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      if (sortKey === key) sortDirection *= -1;
      else { sortKey = key; sortDirection = 1; }
      document.querySelectorAll("th button[data-sort]").forEach(item => item.classList.remove("asc", "desc"));
      button.classList.add(sortDirection === 1 ? "asc" : "desc");
      renderTable();
    });
  });

  document.getElementById("tbody").addEventListener("click", event => {
    const row = event.target.closest("tr[data-record]");
    if (row) openModal(row.dataset.record);
  });
  document.getElementById("tbody").addEventListener("keydown", event => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const row = event.target.closest("tr[data-record]");
    if (row) {
      event.preventDefault();
      openModal(row.dataset.record);
    }
  });
  document.getElementById("modalClose").addEventListener("click", closeModal);
  document.getElementById("modalOverlay").addEventListener("click", event => {
    if (event.target.id === "modalOverlay") closeModal();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !document.getElementById("modalOverlay").hidden) closeModal();
  });
}

async function init() {
  const payload = await fetchJson(RELEASE_FILE);
  requireValue(payload.release_version === "v1.1-rc1", "Unexpected release version");
  requireValue(payload.release_status === "release_candidate", "Unexpected release status");
  requireValue(payload.metrics && typeof payload.metrics === "object", "Public release metrics are missing");
  requireValue(Array.isArray(payload.records), "Public release records are missing");
  validateRows(payload.records);

  DATA = payload.records;
  METRICS = payload.metrics;
  filteredData = [...DATA];

  updateSummary();
  buildCharts();
  setupFilters();
  setupInteraction();
  applyFilters();

  const loadState = document.getElementById("load-state");
  loadState.className = "load-state pass";
  loadState.textContent = "Loaded curated release view: 70 accession records and 64 provisional canonical entities.";
}

init().catch(error => {
  console.error(error);
  const loadState = document.getElementById("load-state");
  loadState.className = "load-state fail";
  loadState.textContent = `Release data failed to load: ${error.message}`;
  document.getElementById("tbody").innerHTML = '<tr><td colspan="13">Release data could not be loaded safely.</td></tr>';
});
