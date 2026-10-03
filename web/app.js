"use strict";

const PUBLIC_IP_URL = "https://api.ipify.org/?format=json";
const DNS_URL = "https://dns.google/resolve";
const REQUEST_TIMEOUT_MS = 6500;

const elements = {
  updateStatus: document.querySelector("#update-status"),
  refreshButton: document.querySelector("#refresh-button"),
  copyButton: document.querySelector("#copy-button"),
  copyStatus: document.querySelector("#copy-status"),
  connectionDot: document.querySelector("#connection-dot"),
  connectionValue: document.querySelector("#connection-value"),
  latencyValue: document.querySelector("#latency-value"),
  connectionType: document.querySelector("#connection-type"),
  browser: document.querySelector("#browser-value"),
  platform: document.querySelector("#platform-value"),
  screen: document.querySelector("#screen-value"),
  language: document.querySelector("#language-value"),
  timezone: document.querySelector("#timezone-value"),
  publicIp: document.querySelector("#public-ip-value"),
  publicIpNote: document.querySelector("#public-ip-note"),
  dnsForm: document.querySelector("#dns-form"),
  domainInput: document.querySelector("#domain-input"),
  dnsButton: document.querySelector("#dns-button"),
  dnsMessage: document.querySelector("#dns-message"),
  dnsDomain: document.querySelector("#dns-domain"),
  dnsIpv4: document.querySelector("#dns-ipv4"),
  dnsIpv6: document.querySelector("#dns-ipv6"),
};

let lastIpLatency = "Not available";
let refreshInProgress = false;

function setText(element, value) {
  element.textContent = value;
}

function getBrowserName(userAgent) {
  if (/Edg\//.test(userAgent)) return "Microsoft Edge";
  if (/OPR\//.test(userAgent)) return "Opera";
  if (/Firefox\//.test(userAgent)) return "Mozilla Firefox";
  if (/Chrome\//.test(userAgent) && !/Chromium\//.test(userAgent)) return "Google Chrome or Chromium-based browser";
  if (/Safari\//.test(userAgent) && !/Chrome\//.test(userAgent)) return "Safari";
  return "Browser (name not identified)";
}

function getPlatform() {
  const exposedPlatform = navigator.userAgentData?.platform || navigator.platform;
  return typeof exposedPlatform === "string" && exposedPlatform.trim()
    ? exposedPlatform
    : "Not available in browser";
}

function readBrowserInformation() {
  setText(elements.browser, getBrowserName(navigator.userAgent || ""));
  setText(elements.platform, getPlatform());
  setText(
    elements.screen,
    Number.isFinite(screen.width) && Number.isFinite(screen.height)
      ? `${screen.width} × ${screen.height}`
      : "Not available in browser",
  );
  setText(elements.language, navigator.language || "Not available in browser");
  try {
    setText(elements.timezone, Intl.DateTimeFormat().resolvedOptions().timeZone || "Not available in browser");
  } catch {
    setText(elements.timezone, "Not available in browser");
  }

  const reportedType = navigator.connection?.type;
  const allowedTypes = { wifi: "Wi-Fi", ethernet: "Ethernet", cellular: "Cellular", bluetooth: "Bluetooth", wimax: "WiMAX", other: "Other" };
  setText(
    elements.connectionType,
    typeof reportedType === "string" && allowedTypes[reportedType.toLowerCase()]
      ? allowedTypes[reportedType.toLowerCase()]
      : "Not available in browser",
  );
}

function setConnectionStatus(kind, message) {
  elements.connectionDot.classList.remove("connected", "offline", "checking");
  if (kind === "connected") elements.connectionDot.classList.add("connected");
  else if (kind === "offline") elements.connectionDot.classList.add("offline");
  else elements.connectionDot.classList.add("checking");
  setText(elements.connectionValue, message);
}

function isValidIpAddress(value) {
  const address = String(value || "").trim();
  const octets = address.split(".");
  if (octets.length === 4 && octets.every((part) => /^\d{1,3}$/.test(part) && Number(part) <= 255)) return true;
  if (!address.includes(":")) return false;
  try {
    const parsed = new URL(`http://[${address}]/`);
    return parsed.hostname.length > 2;
  } catch {
    return false;
  }
}

async function fetchWithTimeout(url, options = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
      credentials: "omit",
      cache: "no-store",
      referrerPolicy: "no-referrer",
    });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function checkPublicConnection() {
  if (navigator.onLine === false) {
    setConnectionStatus("offline", "🔴 Offline");
    setText(elements.latencyValue, "Not available");
    setText(elements.publicIp, "Unavailable");
    setText(elements.publicIpNote, "The browser reports that it is offline.");
    lastIpLatency = "Not available";
    return;
  }

  setConnectionStatus("checking", "🟡 Checking...");
  setText(elements.latencyValue, "Checking...");
  setText(elements.publicIp, "Checking...");
  setText(elements.publicIpNote, "Retrieved over HTTPS from the public-IP service.");

  const startedAt = performance.now();
  try {
    const response = await fetchWithTimeout(PUBLIC_IP_URL, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("The public-IP service returned an error.");
    const payload = await response.json();
    if (!payload || typeof payload.ip !== "string" || !isValidIpAddress(payload.ip)) {
      throw new Error("The public-IP response was not valid.");
    }
    const elapsed = Math.max(0, Math.round(performance.now() - startedAt));
    lastIpLatency = `${elapsed} ms`;
    setText(elements.publicIp, payload.ip.trim());
    setText(elements.latencyValue, lastIpLatency);
    setConnectionStatus("connected", "🟢 Connected");
  } catch (error) {
    lastIpLatency = "Not available";
    setText(elements.latencyValue, "Not available");
    setText(elements.publicIp, "Unavailable");
    const reason = error?.name === "AbortError" ? "The request timed out." : "The public-IP service could not be reached.";
    setText(elements.publicIpNote, reason);
    if (navigator.onLine === false) setConnectionStatus("offline", "🔴 Offline");
    else setConnectionStatus("checking", "Connection check unavailable");
  }
}

async function refreshDashboard() {
  if (refreshInProgress) return;
  refreshInProgress = true;
  elements.refreshButton.disabled = true;
  setText(elements.updateStatus, "Checking...");
  readBrowserInformation();
  try {
    await checkPublicConnection();
  } finally {
    setText(elements.updateStatus, "Updated just now");
    elements.refreshButton.disabled = false;
    refreshInProgress = false;
  }
}

function normalizeDomain(input) {
  const domain = input.trim().replace(/\.$/, "").toLowerCase();
  if (!domain || domain.length > 253 || domain.includes("://") || domain.includes("/") || domain.includes("\\") || domain.includes("@")) return null;
  const labels = domain.split(".");
  if (labels.length < 2 || labels.some((label) => label.length < 1 || label.length > 63 || !/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/.test(label))) return null;
  return domain;
}

async function resolveRecord(domain, type) {
  const url = new URL(DNS_URL);
  url.searchParams.set("name", domain);
  url.searchParams.set("type", type);
  const response = await fetchWithTimeout(url.toString(), { headers: { Accept: "application/dns-json" } });
  if (!response.ok) throw new Error("The DNS service could not complete the lookup.");
  const data = await response.json();
  if (!data || !Number.isInteger(data.Status) || !Array.isArray(data.Answer || [])) {
    throw new Error("The DNS service returned an unexpected response.");
  }
  if (data.Status !== 0) return [];
  const expectedType = type === "A" ? 1 : 28;
  return (data.Answer || [])
    .filter((record) => record && record.type === expectedType && typeof record.data === "string" && isValidIpAddress(record.data))
    .map((record) => record.data);
}

async function performDnsLookup(event) {
  event.preventDefault();
  const domain = normalizeDomain(elements.domainInput.value);
  if (!domain) {
    setText(elements.dnsMessage, "Enter a valid domain name, such as example.com.");
    elements.dnsMessage.classList.add("error");
    elements.dnsDomain.textContent = "Not looked up";
    elements.dnsIpv4.textContent = "Not looked up";
    elements.dnsIpv6.textContent = "Not looked up";
    return;
  }

  elements.dnsButton.disabled = true;
  elements.dnsMessage.classList.remove("error");
  setText(elements.dnsMessage, "Looking up public DNS records...");
  setText(elements.dnsDomain, domain);
  setText(elements.dnsIpv4, "Checking...");
  setText(elements.dnsIpv6, "Checking...");
  try {
    const [ipv4, ipv6] = await Promise.all([resolveRecord(domain, "A"), resolveRecord(domain, "AAAA")]);
    setText(elements.dnsIpv4, ipv4.length ? [...new Set(ipv4)].join(", ") : "No DNS result available");
    setText(elements.dnsIpv6, ipv6.length ? [...new Set(ipv6)].join(", ") : "No DNS result available");
    setText(elements.dnsMessage, "Public DNS lookup complete.");
  } catch (error) {
    setText(elements.dnsIpv4, "No DNS result available");
    setText(elements.dnsIpv6, "No DNS result available");
    setText(elements.dnsMessage, error?.name === "AbortError" ? "The DNS request timed out. Try again." : "DNS lookup failed. Check the domain or try again later.");
    elements.dnsMessage.classList.add("error");
  } finally {
    elements.dnsButton.disabled = false;
  }
}

function createPlainTextReport() {
  const value = (selector) => document.querySelector(selector).textContent.trim();
  return [
    "NetScope Web Report",
    "===================",
    "",
    "Connection",
    `Status: ${value("#connection-value")}`,
    `Latency: ${value("#latency-value")}`,
    `Connection type: ${value("#connection-type")}`,
    "",
    "Browser",
    `Browser: ${value("#browser-value")}`,
    `Platform: ${value("#platform-value")}`,
    `Screen resolution: ${value("#screen-value")}`,
    `Language: ${value("#language-value")}`,
    `Time Zone: ${value("#timezone-value")}`,
    "",
    "Public Network",
    `Public IP: ${value("#public-ip-value")}`,
    "",
    "IP Information",
    "Country: Not available",
    "Region: Not available",
    "City: Not available",
    "Organization: Not available",
    "",
    "DNS Lookup",
    `Domain: ${value("#dns-domain")}`,
    `IPv4: ${value("#dns-ipv4")}`,
    `IPv6: ${value("#dns-ipv6")}`,
  ].join("\n");
}

async function copyReport() {
  const report = createPlainTextReport();
  try {
    if (navigator.clipboard?.writeText && window.isSecureContext) {
      await navigator.clipboard.writeText(report);
    } else {
      const temporary = document.createElement("textarea");
      temporary.value = report;
      temporary.setAttribute("readonly", "");
      temporary.style.position = "fixed";
      temporary.style.opacity = "0";
      document.body.append(temporary);
      temporary.select();
      const copied = document.execCommand("copy");
      temporary.remove();
      if (!copied) throw new Error("Clipboard access is unavailable.");
    }
    setText(elements.copyStatus, "Report copied.");
  } catch {
    setText(elements.copyStatus, "Clipboard unavailable. Copy is supported on HTTPS or localhost.");
  }
  window.setTimeout(() => setText(elements.copyStatus, ""), 4500);
}

elements.refreshButton.addEventListener("click", refreshDashboard);
elements.copyButton.addEventListener("click", copyReport);
elements.dnsForm.addEventListener("submit", performDnsLookup);
window.addEventListener("online", () => {
  if (!refreshInProgress) setConnectionStatus("checking", "🟡 Online — refresh to verify");
});
window.addEventListener("offline", () => {
  setConnectionStatus("offline", "🔴 Offline");
  setText(elements.latencyValue, "Not available");
});

refreshDashboard();
