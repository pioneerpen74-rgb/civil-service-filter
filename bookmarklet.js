(function () {
  if (document.getElementById("cs-ranker-panel")) {
    document.getElementById("cs-ranker-panel").remove();
  }

  // --- FLOATING UI ---
  const panel = document.createElement("div");
  panel.id = "cs-ranker-panel";
  panel.style.cssText =
    "position:fixed;top:20px;right:20px;z-index:999999;width:340px;padding:16px;" +
    "background:#1f2937;color:#f9fafb;border-radius:8px;box-shadow:0 10px 25px rgba(0,0,0,0.4);" +
    "font-family:sans-serif;font-size:13px;";

  panel.innerHTML = `
    <div style="font-weight:bold;font-size:15px;margin-bottom:10px;display:flex;justify-content:space-between;">
      <span>CS Job Ranker</span>
      <span id="cs-close" style="cursor:pointer;opacity:0.7;">✕</span>
    </div>
    <label style="display:block;margin-bottom:4px;">High Priority (+25 pts each):</label>
    <input id="cs-high" type="text" value="strategy, policy, transformation, delivery" style="width:100%;margin-bottom:8px;padding:6px;border-radius:4px;border:none;box-sizing:border-box;">
    
    <label style="display:block;margin-bottom:4px;">Nice-to-Have (+10 pts each):</label>
    <input id="cs-nice" type="text" value="stakeholder, agile, hybrid, governance" style="width:100%;margin-bottom:8px;padding:6px;border-radius:4px;border:none;box-sizing:border-box;">
    
    <label style="display:block;margin-bottom:4px;">Exclusions (Drop role):</label>
    <input id="cs-exclude" type="text" value="veterinary, clinical, prison" style="width:100%;margin-bottom:12px;padding:6px;border-radius:4px;border:none;box-sizing:border-box;">
    
    <button id="cs-start-btn" style="width:100%;padding:10px;background:#2563eb;color:#fff;font-weight:bold;border:none;border-radius:4px;cursor:pointer;">Scan & Rank This Page</button>
    <div id="cs-status" style="margin-top:10px;font-size:12px;color:#9ca3af;">Ready to scan.</div>
  `;

  document.body.appendChild(panel);
  document.getElementById("cs-close").onclick = () => panel.remove();

  // --- PARSE & SCORE ---
  document.getElementById("cs-start-btn").onclick = function () {
    const status = document.getElementById("cs-status");
    const highWords = document.getElementById("cs-high").value.toLowerCase().split(",").map(s => s.trim()).filter(Boolean);
    const niceWords = document.getElementById("cs-nice").value.toLowerCase().split(",").map(s => s.trim()).filter(Boolean);
    const exWords = document.getElementById("cs-exclude").value.toLowerCase().split(",").map(s => s.trim()).filter(Boolean);

    status.innerText = "Analyzing vacancies...";

    const rows = Array.from(document.querySelectorAll("li.search-results-job-box, .search-result, table tr, a[href*='pageaction=viewjob']"));
    const seenUrls = new Set();
    const rankedJobs = [];

    rows.forEach(row => {
      const linkElem = row.tagName === "A" ? row : row.querySelector("a[href*='pageaction=viewjob'], a[href*='job_details']");
      if (!linkElem) return;

      const title = (linkElem.innerText || "").trim();
      const href = linkElem.href;
      if (!title || seenUrls.has(href)) return;
      seenUrls.add(href);

      const blockText = (row.innerText || "").toLowerCase();

      // Disqualify exclusions
      if (exWords.some(bad => blockText.includes(bad))) return;

      // Calculate score
      let score = 0;
      let breakdown = [];

      highWords.forEach(w => {
        if (blockText.includes(w)) {
          score += 25;
          breakdown.push(`+25 ${w}`);
        }
      });

      niceWords.forEach(w => {
        if (blockText.includes(w)) {
          score += 10;
          breakdown.push(`+10 ${w}`);
        }
      });

      rankedJobs.push({
        title,
        score,
        reasons: breakdown.join("; ") || "Base match",
        link: href
      });
    });

    rankedJobs.sort((a, b) => b.score - a.score);

    if (rankedJobs.length === 0) {
      status.innerText = "No jobs matched your criteria on this page.";
      return;
    }

    status.innerText = `Found ${rankedJobs.length} matches! Downloading CSV...`;

    // --- CSV EXPORT ---
    let csv = "Score,Title,Reasons,Link\n";
    rankedJobs.forEach(j => {
      const cleanTitle = `"${j.title.replace(/"/g, '""')}"`;
      const cleanReasons = `"${j.reasons.replace(/"/g, '""')}"`;
      csv += `${j.score},${cleanTitle},${cleanReasons},"${j.link}"\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cs_matched_jobs_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };
})();
