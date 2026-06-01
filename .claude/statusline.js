#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const readline = require("readline");
const { execSync } = require("child_process");

// Pricing per million tokens (USD)
const MODEL_PRICING = {
  opus:   { input: 15,  output: 75, cache_write: 18.75, cache_read: 1.5  },
  sonnet: { input: 3,   output: 15, cache_write: 3.75,  cache_read: 0.3  },
  haiku:  { input: 0.8, output: 4,  cache_write: 1,     cache_read: 0.08 },
};

// ANSI colors
const C = {
  reset:  "\x1b[0m",
  dim:    "\x1b[2m",
  green:  "\x1b[32m",
  yellow: "\x1b[33m",
  red:    "\x1b[31m",
  cyan:   "\x1b[36m",
  bold:   "\x1b[1m",
};

// Read JSON from stdin
let input = "";
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", async () => {
  try {
    const data = JSON.parse(input);

    // --- 1. Current directory (basename) ---
    const cwd = data.workspace?.current_dir || data.cwd || ".";
    const currentDir = path.basename(cwd);

    // --- 2. Git branch (skip if not a repo) ---
    let gitBranch = null;
    try {
      const branch = execSync(
        `git --no-optional-locks -C ${JSON.stringify(cwd)} rev-parse --abbrev-ref HEAD`,
        { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], timeout: 2000 }
      ).trim();
      if (branch && branch !== "HEAD") {
        gitBranch = branch;
      } else if (branch === "HEAD") {
        // detached HEAD: show short SHA instead
        const sha = execSync(
          `git --no-optional-locks -C ${JSON.stringify(cwd)} rev-parse --short HEAD`,
          { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], timeout: 2000 }
        ).trim();
        gitBranch = sha ? `(${sha})` : null;
      }
    } catch (_) {
      // Not a git repo or git unavailable — silently skip
    }

    // --- 3. Model name ---
    const model = data.model?.display_name || data.model?.id || "Unknown";

    // --- 4 & 5. Token count and cumulative session cost from transcript ---
    const sessionId = data.session_id;
    let tokenData = { total: 0, cost: { input: 0, output: 0, cache_write: 0, cache_read: 0 } };

    if (sessionId) {
      const projectsDir = path.join(process.env.HOME, ".claude", "projects");
      if (fs.existsSync(projectsDir)) {
        const projectDirs = fs
          .readdirSync(projectsDir)
          .map((d) => path.join(projectsDir, d))
          .filter((d) => fs.statSync(d).isDirectory());

        for (const projectDir of projectDirs) {
          const transcriptFile = path.join(projectDir, `${sessionId}.jsonl`);
          if (fs.existsSync(transcriptFile)) {
            tokenData = await calculateTokensFromTranscript(transcriptFile);
            break;
          }
        }
      }
    }

    const tokenDisplay = formatTokenCount(tokenData.total);
    const cost = calculateCost(tokenData.cost, model);
    const costDisplay = formatCost(cost);

    // --- 6. Context window usage % ---
    // Prefer pre-calculated field; fall back to manual ratio
    let percentage;
    if (data.context_window?.used_percentage != null) {
      percentage = Math.round(data.context_window.used_percentage);
    } else {
      const windowSize = data.context_window?.context_window_size || 200000;
      percentage = tokenData.total > 0
        ? Math.min(100, Math.round((tokenData.total / windowSize) * 100))
        : 0;
    }

    let pctColor = C.green;
    if (percentage >= 70) pctColor = C.yellow;
    if (percentage >= 90) pctColor = C.red;

    // --- Assemble status line ---
    // Icons: emoji for dir/git, ANSI bold cyan "T" for tokens
    const ICON_TOKEN = `${C.bold}${C.cyan}T${C.reset}`;
    // ICON_DIR    = "";  // replaced with emoji
    // ICON_BRANCH = "";  // replaced with emoji

    const parts = [
      `📁 ${C.bold}${currentDir}${C.reset}`,
    ];

    if (gitBranch) {
      parts.push(`🎋 ${C.cyan}${gitBranch}${C.reset}`);
    }

    parts.push(`🤖 ${C.dim}${model}${C.reset}`);
    parts.push(`${ICON_TOKEN} ${tokenDisplay} 💰 ${costDisplay}`);
    parts.push(`${pctColor}🧠 ${percentage}%${C.reset}`);

    console.log(parts.join(` ${C.dim}|${C.reset} `));
  } catch (error) {
    console.log(". | Unknown | 0 ($0.0000) | ctx:0%");
  }
});

async function calculateTokensFromTranscript(filePath) {
  return new Promise((resolve, reject) => {
    let lastUsage = null;
    const accumulated = { input: 0, output: 0, cache_write: 0, cache_read: 0 };

    const fileStream = fs.createReadStream(filePath);
    const rl = readline.createInterface({ input: fileStream, crlfDelay: Infinity });

    rl.on("line", (line) => {
      try {
        const entry = JSON.parse(line);
        if (entry.type === "assistant" && entry.message?.usage) {
          const u = entry.message.usage;
          lastUsage = u;
          accumulated.input       += u.input_tokens                  || 0;
          accumulated.output      += u.output_tokens                 || 0;
          accumulated.cache_write += u.cache_creation_input_tokens   || 0;
          accumulated.cache_read  += u.cache_read_input_tokens       || 0;
        }
      } catch (_) { /* skip invalid lines */ }
    });

    rl.on("close", () => {
      if (lastUsage) {
        const lastTotal =
          (lastUsage.input_tokens                || 0) +
          (lastUsage.output_tokens               || 0) +
          (lastUsage.cache_creation_input_tokens || 0) +
          (lastUsage.cache_read_input_tokens     || 0);
        resolve({ total: lastTotal, cost: accumulated });
      } else {
        resolve({ total: 0, cost: { input: 0, output: 0, cache_write: 0, cache_read: 0 } });
      }
    });

    rl.on("error", reject);
  });
}

function getPricing(modelName) {
  const name = modelName.toLowerCase();
  if (name.includes("opus"))  return MODEL_PRICING.opus;
  if (name.includes("haiku")) return MODEL_PRICING.haiku;
  return MODEL_PRICING.sonnet;
}

function calculateCost(usage, modelName) {
  const p = getPricing(modelName);
  return (
    (usage.input       / 1_000_000) * p.input       +
    (usage.output      / 1_000_000) * p.output      +
    (usage.cache_write / 1_000_000) * p.cache_write +
    (usage.cache_read  / 1_000_000) * p.cache_read
  );
}

function formatCost(cost) {
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  if (cost < 1)    return `$${cost.toFixed(3)}`;
  return `$${cost.toFixed(2)}`;
}

function formatTokenCount(tokens) {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`;
  if (tokens >= 1_000)     return `${(tokens / 1_000).toFixed(1)}K`;
  return tokens.toString();
}
