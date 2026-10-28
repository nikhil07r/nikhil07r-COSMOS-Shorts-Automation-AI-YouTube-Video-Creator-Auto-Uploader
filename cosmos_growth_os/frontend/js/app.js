// COSMOS GROWTH OS — Frontend Application Controller
document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide Icons
  if (window.lucide) {
    lucide.createIcons();
  }

  // State Management
  const state = {
    currentView: "overview",
    theme: localStorage.getItem("cosmos_theme") || "dark",
    channel: null,
    videos: [],
    drafts: [],
    jobs: [],
    categories: [],
    promptTemplates: [],
    activeCategoryFilter: "all",
    activeCategorySearch: "",
    categoryToDelete: null,
    curatedTopics: {},
    activeJobId: null,
    currentVideoPath: null,
    currentThumbnailPath: null,
    currentTitle: null,
    pollInterval: null,
    selectedJob: null,
    activePipelineJob: null
  };

  // Set Theme
  document.documentElement.setAttribute("data-theme", state.theme);
  updateThemeIcon();

  // Navigation Setup
  setupNavigation();

  // Note: Initial data loading and event listener setup are deferred to the bottom
  // of DOMContentLoaded so all variables, functions, and elements are fully initialized.

  // ----------------------------------------------------
  // NAVIGATION & VIEWS
  // ----------------------------------------------------
  function setupNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
      item.addEventListener("click", () => {
        const view = item.getAttribute("data-view");
        switchView(view);
      });
    });

    const mobileMenuBtn = document.getElementById("mobile-menu-btn");
    const sidebar = document.getElementById("sidebar");
    if (mobileMenuBtn && sidebar) {
      mobileMenuBtn.addEventListener("click", () => {
        sidebar.classList.toggle("hidden");
      });
    }

    const ctaBtn = document.getElementById("btn-create-short-cta");
    if (ctaBtn) {
      ctaBtn.addEventListener("click", () => {
        switchView("studio");
      });
    }
  }

  function switchView(viewName) {
    state.currentView = viewName;
    document.querySelectorAll(".view-panel").forEach(p => p.classList.add("hidden"));
    
    const target = document.getElementById(`view-${viewName}`);
    if (target) {
      target.classList.remove("hidden");
    }

    document.querySelectorAll(".nav-item").forEach(item => {
      if (item.getAttribute("data-view") === viewName) {
        item.classList.add("text-white", "bg-gray-800/60");
        item.classList.remove("text-gray-400");
      } else {
        item.classList.remove("text-white", "bg-gray-800/60");
        item.classList.add("text-gray-400");
      }
    });

    // Resize charts on tab visibility change
    if (viewName === "overview" && window.chartGrowth) {
      window.chartGrowth.resize();
      window.chartCategories.resize();
    } else if (viewName === "monetization" && window.chartPostingHeatmap) {
      window.chartPostingHeatmap.resize();
    } else if (viewName === "growth") {
      fetchGrowthDiagnostics();
      fetchMilestoneRoadmap();
    }
  }

  // ----------------------------------------------------
  // THEME MANAGEMENT
  // ----------------------------------------------------
  const themeToggleBtn = document.getElementById("btn-theme-toggle");
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      state.theme = state.theme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", state.theme);
      localStorage.setItem("cosmos_theme", state.theme);
      updateThemeIcon();
      
      // Refresh charts for theme change
      initOverviewCharts();
      fetchBestPostingTimes();
    });
  }

  function updateThemeIcon() {
    const icon = document.getElementById("theme-icon");
    if (!icon) return;
    if (state.theme === "dark") {
      icon.setAttribute("data-lucide", "sun");
    } else {
      icon.setAttribute("data-lucide", "moon");
    }
    if (window.lucide) lucide.createIcons();
  }

  // ----------------------------------------------------
  // SYSTEM HEALTH
  // ----------------------------------------------------
  async function fetchHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      
      const ollamaEl = document.getElementById("health-ollama");
      const settingsOllamaBadge = document.getElementById("settings-ollama-badge");
      
      if (data.ollama && data.ollama.status === "online") {
        if (ollamaEl) {
          ollamaEl.textContent = "Online (" + data.ollama.models.length + " models)";
          ollamaEl.className = "text-emerald-400 font-medium";
        }
        if (settingsOllamaBadge) {
          settingsOllamaBadge.textContent = "Online";
          settingsOllamaBadge.className = "px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 font-semibold";
        }
      } else {
        if (ollamaEl) {
          ollamaEl.textContent = "Offline";
          ollamaEl.className = "text-rose-400 font-medium";
        }
        if (settingsOllamaBadge) {
          settingsOllamaBadge.textContent = "Offline";
          settingsOllamaBadge.className = "px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-400 font-semibold";
        }
      }

      const ffmpegEl = document.getElementById("health-ffmpeg");
      if (ffmpegEl && data.ffmpeg && data.ffmpeg.installed) {
        ffmpegEl.textContent = "Ready (v7.0)";
        ffmpegEl.className = "text-emerald-400 font-medium";
      }

      const ytEl = document.getElementById("health-yt");
      if (ytEl && data.youtube_auth && data.youtube_auth.ready) {
        ytEl.textContent = "Connected";
        ytEl.className = "text-emerald-400 font-medium";
      }
    } catch (e) {
      console.warn("Health check error:", e);
    }
  }

  // ----------------------------------------------------
  // YOUTUBE & ANALYTICS DATA
  // ----------------------------------------------------
  async function fetchYouTubeData() {
    try {
      const res = await fetch("/api/youtube/status");
      const data = await res.json();
      
      if (data.channel) {
        state.channel = data.channel;
        document.getElementById("header-channel-title").textContent = data.channel.title || "COSMOS VIRAL";
        document.getElementById("header-channel-handle").textContent = data.channel.custom_url || "@cosmos-1nr";
        
        document.getElementById("metric-subscribers").textContent = (data.channel.subscriber_count || 49).toLocaleString();
        document.getElementById("metric-views").textContent = (data.channel.view_count || 11340).toLocaleString();
        document.getElementById("metric-videos").textContent = (data.channel.video_count || 37).toLocaleString();
        
        const avg = data.channel.video_count > 0 ? Math.round(data.channel.view_count / data.channel.video_count) : 0;
        document.getElementById("metric-avg-views").textContent = avg.toLocaleString();
      }

      // Fetch cached or live videos
      const vidRes = await fetch("/api/youtube/videos?limit=15");
      const vidData = await vidRes.json();
      state.videos = vidData.videos || [];
      renderOverviewVideosTable(state.videos);

      // Render Charts
      initOverviewCharts();

      // Fetch AI Insights
      fetchAiInsights();
    } catch (e) {
      console.error("YouTube data fetch error:", e);
    }
  }

  function renderOverviewVideosTable(videos) {
    const tbody = document.getElementById("overview-videos-tbody");
    if (!tbody) return;

    if (!videos || videos.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-gray-500">No videos found. Click 'Sync Real Data' above.</td></tr>`;
      return;
    }

    tbody.innerHTML = videos.map(v => {
      const views = (v.view_count || 0).toLocaleString();
      const likes = (v.like_count || 0).toLocaleString();
      const engagement = v.view_count > 0 ? (((v.like_count + v.comment_count) / v.view_count) * 100).toFixed(1) + "%" : "0.0%";
      const title = v.title || "Untitled Short";
      const thumb = v.thumbnail_url || "/static/images/thumb_placeholder.png";
      const duration = (v.duration_seconds || 55) + "s";
      const ytUrl = `https://youtube.com/shorts/${v.video_id}`;

      return `
        <tr class="hover:bg-gray-800/40 transition">
          <td class="py-3 pr-4 flex items-center space-x-3">
            <img src="${thumb}" alt="thumb" class="w-10 h-14 object-cover rounded-md bg-gray-900 border border-gray-800 flex-shrink-0">
            <span class="font-medium text-white truncate max-w-xs" title="${title}">${title}</span>
          </td>
          <td class="py-3 text-gray-400 font-mono text-[11px]">${duration}</td>
          <td class="py-3 font-semibold text-white">${views}</td>
          <td class="py-3 text-gray-300">${likes}</td>
          <td class="py-3">
            <span class="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold text-[11px]">${engagement}</span>
          </td>
          <td class="py-3 text-right">
            <a href="${ytUrl}" target="_blank" rel="noopener" class="text-violet-400 hover:text-violet-300 font-medium inline-flex items-center gap-1">
              <span>View</span>
              <i data-lucide="external-link" class="w-3 h-3"></i>
            </a>
          </td>
        </tr>
      `;
    }).join("");

    if (window.lucide) lucide.createIcons();
  }

  function initOverviewCharts() {
    const isDark = state.theme === "dark";
    const textColor = isDark ? "#9CA3AF" : "#4B5563";
    const splitLineColor = isDark ? "#1F2937" : "#E5E7EB";

    // 1. Growth Velocity Chart
    const growthDom = document.getElementById("chart-growth");
    if (growthDom && window.echarts) {
      if (window.chartGrowth) window.chartGrowth.dispose();
      window.chartGrowth = echarts.init(growthDom);
      
      const option = {
        backgroundColor: "transparent",
        tooltip: {
          trigger: "axis",
          backgroundColor: isDark ? "#111827" : "#FFFFFF",
          borderColor: isDark ? "#1F2937" : "#E5E7EB",
          textStyle: { color: isDark ? "#F9FAFB" : "#111827", fontSize: 12 }
        },
        grid: { left: "3%", right: "4%", bottom: "3%", top: "12%", containLabel: true },
        xAxis: {
          type: "category",
          boundaryGap: false,
          data: ["Day 1", "Day 5", "Day 10", "Day 15", "Day 20", "Day 25", "Latest"],
          axisLine: { lineStyle: { color: splitLineColor } },
          axisLabel: { color: textColor, fontSize: 11 }
        },
        yAxis: {
          type: "value",
          splitLine: { lineStyle: { color: splitLineColor, type: "dashed" } },
          axisLabel: { color: textColor, fontSize: 11 }
        },
        series: [
          {
            name: "Channel Views",
            type: "line",
            smooth: true,
            data: [3200, 4800, 6100, 7900, 9400, 10800, 11340],
            lineStyle: { width: 3, color: "#8B5CF6" },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: "rgba(139, 92, 246, 0.45)" },
                { offset: 1, color: "rgba(139, 92, 246, 0.0)" }
              ])
            },
            itemStyle: { color: "#8B5CF6" }
          },
          {
            name: "Subscribers",
            type: "line",
            smooth: true,
            data: [12, 19, 26, 33, 40, 46, 49],
            lineStyle: { width: 2.5, color: "#06B6D4" },
            itemStyle: { color: "#06B6D4" }
          }
        ]
      };
      window.chartGrowth.setOption(option);
    }

    // 2. Category Distribution Donut
    const catDom = document.getElementById("chart-categories");
    if (catDom && window.echarts) {
      if (window.chartCategories) window.chartCategories.dispose();
      window.chartCategories = echarts.init(catDom);

      const catOption = {
        backgroundColor: "transparent",
        tooltip: {
          trigger: "item",
          backgroundColor: isDark ? "#111827" : "#FFFFFF",
          borderColor: isDark ? "#1F2937" : "#E5E7EB",
          textStyle: { color: isDark ? "#F9FAFB" : "#111827", fontSize: 12 }
        },
        legend: {
          bottom: "0%",
          left: "center",
          textStyle: { color: textColor, fontSize: 10 }
        },
        series: [
          {
            name: "Views Share",
            type: "pie",
            radius: ["45%", "70%"],
            avoidLabelOverlap: false,
            itemStyle: { borderRadius: 8, borderColor: isDark ? "#111827" : "#FFFFFF", borderWidth: 2 },
            label: { show: false },
            data: [
              { value: 45, name: "Space & Universe", itemStyle: { color: "#8B5CF6" } },
              { value: 25, name: "Dangerous Anomalies", itemStyle: { color: "#06B6D4" } },
              { value: 18, name: "Strange Places", itemStyle: { color: "#10B981" } },
              { value: 12, name: "Human History", itemStyle: { color: "#F59E0B" } }
            ]
          }
        ]
      };
      window.chartCategories.setOption(catOption);
    }
  }

  async function fetchAiInsights() {
    const container = document.getElementById("overview-ai-insights");
    if (!container) return;

    try {
      const res = await fetch("/api/analytics/ai_insights");
      const data = await res.json();
      
      container.innerHTML = `
        <div class="space-y-2">
          <p class="font-medium text-white">${data.strengths || ""}</p>
          <div class="p-2.5 bg-gray-900/80 rounded-xl border border-gray-800 text-[11px] text-gray-300">
            <span class="font-bold text-violet-400">💡 Recommended High-Growth Topics:</span>
            <ul class="list-disc list-inside mt-1 space-y-0.5 text-gray-300">
              ${(data.recommended_topics || []).map(t => `<li>${t}</li>`).join("")}
            </ul>
          </div>
          <div class="flex items-center gap-2 text-[11px] text-emerald-400">
            <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
            <span>${data.retention_tip || ""}</span>
          </div>
        </div>
      `;
      if (window.lucide) lucide.createIcons();
    } catch (e) {
      container.innerHTML = `<p class="text-gray-400">Insights temporarily offline. Connect Ollama to generate recommendations.</p>`;
    }
  }

  // ----------------------------------------------------
  // AI CONTENT STUDIO
  // ----------------------------------------------------
  let activeStudioMode = "story";

  const tabStory = document.getElementById("tab-mode-story");
  const tabScript = document.getElementById("tab-mode-script");
  const tabCurated = document.getElementById("tab-mode-curated");

  const panelStory = document.getElementById("panel-mode-story");
  const panelScript = document.getElementById("panel-mode-script");
  const panelCurated = document.getElementById("panel-mode-curated");

  function setStudioMode(mode) {
    activeStudioMode = mode;
    [tabStory, tabScript, tabCurated].forEach(t => {
      t.classList.remove("border-violet-500", "text-white");
      t.classList.add("border-transparent", "text-gray-400");
    });
    [panelStory, panelScript, panelCurated].forEach(p => p.classList.add("hidden"));

    if (mode === "story") {
      tabStory.classList.add("border-violet-500", "text-white");
      panelStory.classList.remove("hidden");
    } else if (mode === "script") {
      tabScript.classList.add("border-violet-500", "text-white");
      panelScript.classList.remove("hidden");
    } else {
      tabCurated.classList.add("border-violet-500", "text-white");
      panelCurated.classList.remove("hidden");
    }
  }

  if (tabStory) tabStory.addEventListener("click", () => setStudioMode("story"));
  if (tabScript) tabScript.addEventListener("click", () => setStudioMode("script"));
  if (tabCurated) tabCurated.addEventListener("click", () => setStudioMode("curated"));

  async function fetchCuratedTopics() {
    try {
      const res = await fetch("/api/studio/curated_topics");
      const data = await res.json();
      state.curatedTopics = data;
      if (typeof renderFormulaTopics === "function") {
        renderFormulaTopics(activeFormulaCat);
      }

      const catSelect = document.getElementById("studio-curated-category");
      if (!catSelect) return;

      const categories = Object.keys(data);
      catSelect.innerHTML = categories.map(c => `<option value="${c}">${c}</option>`).join("");
      
      updateTopicDropdown(categories[0]);

      catSelect.addEventListener("change", (e) => {
        updateTopicDropdown(e.target.value);
      });

      const topicSelect = document.getElementById("studio-curated-topic");
      if (topicSelect) {
        topicSelect.addEventListener("change", (e) => {
          const cat = catSelect.value;
          const idx = parseInt(e.target.value, 10);
          if (state.curatedTopics[cat] && state.curatedTopics[cat][idx]) {
            loadCuratedTopicIntoEditor(state.curatedTopics[cat][idx]);
          }
        });
      }
    } catch (e) {
      console.warn("Curated topics load error:", e);
    }
  }

  function updateTopicDropdown(cat) {
    const topicSelect = document.getElementById("studio-curated-topic");
    if (!topicSelect || !state.curatedTopics[cat]) return;
    const topics = state.curatedTopics[cat];
    topicSelect.innerHTML = topics.map((t, idx) => {
      const val = typeof t === "object" ? t.title : t;
      return `<option value="${idx}">${val}</option>`;
    }).join("");

    // Auto load first topic only if actively in Curated mode
    if (topics.length > 0 && activeStudioMode === "curated") {
      loadCuratedTopicIntoEditor(topics[0]);
    }
  }

  function loadCuratedTopicIntoEditor(item) {
    if (!item || typeof item !== "object") return;
    if (item.script) {
      const scriptInput = document.getElementById("studio-script-input");
      if (scriptInput) scriptInput.value = item.script;
    }
    if (item.title) {
      const titleInput = document.getElementById("studio-title-input");
      if (titleInput) titleInput.value = item.title;
    }
    if (item.keywords) {
      renderKeywordTags(item.keywords);
    }
    if (item.script) {
      runPolicyCheck(item.script, item.title || "");
    }
  }

  const btnGenerateScript = document.getElementById("btn-generate-script");
  if (btnGenerateScript) {
    btnGenerateScript.addEventListener("click", async () => {
      const btnLabel = document.getElementById("btn-generate-label");
      btnLabel.textContent = "Writing Viral Script with Qwen...";
      btnGenerateScript.disabled = true;

      const catSelect = document.getElementById("studio-story-category");
      const selectedCatOption = catSelect?.options[catSelect.selectedIndex];
      const categoryName = activeStudioMode === "curated" 
        ? document.getElementById("studio-curated-category")?.value 
        : catSelect?.value;
      const langChoice = document.getElementById("studio-language")?.value;
      const lang = langChoice === "auto" ? (selectedCatOption?.getAttribute("data-lang") || "hindi") : langChoice;
      const tplId = document.getElementById("studio-prompt-template")?.value;
      const customInst = document.getElementById("studio-custom-instructions")?.value;

      const payload = {
        mode: activeStudioMode,
        prompt: document.getElementById("studio-story-prompt")?.value || "",
        exact_script: document.getElementById("studio-exact-script")?.value || "",
        category: categoryName || "Space & Universe",
        language: lang,
        prompt_template_id: tplId || null,
        custom_instructions: customInst || "",
        topic: activeStudioMode === "curated" ? document.getElementById("studio-curated-topic")?.value : "",
        model: document.getElementById("studio-model-selector")?.value || "qwen2.5:3b"
      };

      try {
        showToast("Generating script with local Ollama...", "info");
        const res = await fetch("/api/studio/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Generation failed");
        }

        const draft = await res.json();
        
        // Populate inputs
        document.getElementById("studio-title-input").value = draft.title || "";
        document.getElementById("studio-script-input").value = draft.hindi_script || "";
        
        // Render keywords
        renderKeywordTags(draft.keywords || []);
        
        // Render checklist
        renderFactsChecklist(draft.facts_checklist || []);

        // Trigger Policy Check
        runPolicyCheck(draft.hindi_script, draft.title, lang);
        showToast("Viral Script Ready for Review!", "success");
      } catch (e) {
        showToast("Generation error: " + e.message, "danger");
      } finally {
        btnLabel.textContent = "Generate Script with Qwen 7B";
        btnGenerateScript.disabled = false;
      }
    });
  }

  // ----------------------------------------------------
  // MULTI-NICHE FORMULA & WINNING TOPICS CONTROLLER
  // ----------------------------------------------------
  let activeFormulaCat = "WWII & Warfare Extreme Inventions (2.6K Formula)";

  const formulaMeta = {
    "WWII & Warfare Extreme Inventions (2.6K Formula)": {
      title: "2.6K Formula: WWII & Warfare Extreme Hacks",
      icon: "🎖️",
      badge: "#1 WINNER STYLE",
      shortLabel: "WWII & Warfare",
      desc: "Modeled on your highest-performing Short (2,648 views). Switch niches or click any topic to immediately load the script:"
    },
    "Space & Universe": {
      title: "Viral Formula: Space & Cosmic Mysteries",
      icon: "🚀",
      badge: "HIGH RETENTION",
      shortLabel: "Space & Universe",
      desc: "Awe-inspiring cosmic phenomena, black holes, and deep universe secrets with high viral CTR:"
    },
    "Earth Mysteries": {
      title: "Viral Formula: Earth & Bizarre Phenomena",
      icon: "🗺️",
      badge: "VIRAL ENGAGEMENT",
      shortLabel: "Earth Mysteries",
      desc: "Unsolved natural anomalies and strange earthly locations that provoke comments and shares:"
    },
    "Dangerous Places": {
      title: "Viral Formula: World's Deadliest Locations",
      icon: "⚠️",
      badge: "HIGH CTR",
      shortLabel: "Dangerous Places",
      desc: "Extreme forbidden islands, lethal radiation zones, and isolated tribal territories:"
    },
    "Human History": {
      title: "Viral Formula: Lost Ancient Engineering",
      icon: "🏛️",
      badge: "TIMELESS REACH",
      shortLabel: "Human History",
      desc: "Ancient technological marvels, self-healing architectures, and prehistoric machines:"
    },
    "Science Anomalies": {
      title: "Viral Formula: Science & Nature Mind-Blowers",
      icon: "🧬",
      badge: "DEEP CURIOSITY",
      shortLabel: "Science Anomalies",
      desc: "Deep ocean aliens, quantum paradoxes, and shocking weather anomalies:"
    },
    "Technology & AI": {
      title: "Viral Formula: Cutting-Edge Tech & AI Hacks",
      icon: "🤖",
      badge: "FUTURE TECH",
      shortLabel: "Tech & AI",
      desc: "Quantum computing, interstellar probes, and revolutionary future breakthroughs:"
    }
  };

  function setupWinningTopicListeners() {
    // 1. Setup Category Switcher Tabs (Clicking any tab switches the niche and topic pills)
    const tabButtons = document.querySelectorAll(".btn-formula-tab");
    tabButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        const cat = btn.getAttribute("data-cat");
        if (cat) {
          switchFormulaCategory(cat, true);
        }
      });
    });

    // 2. Synchronize when studio-story-category dropdown changes
    const catSelect = document.getElementById("studio-story-category");
    if (catSelect) {
      catSelect.addEventListener("change", (e) => {
        const val = e.target.value;
        if (val) {
          const matched = Object.keys(formulaMeta).find(k => k === val || val.includes(k) || k.includes(val));
          if (matched && matched !== activeFormulaCat) {
            switchFormulaCategory(matched, false);
          }
        }
      });
    }

    // Initial render
    switchFormulaCategory(activeFormulaCat, false);
  }

  function switchFormulaCategory(catName, syncDropdown = true) {
    activeFormulaCat = catName;
    const meta = formulaMeta[catName] || {
      title: `Viral Formula: ${catName}`,
      icon: "✨",
      badge: "VIRAL FORMULA",
      shortLabel: catName,
      desc: "Click any viral topic below or generate fresh ideas:"
    };

    // Update Banner Header & Labels
    const iconEl = document.getElementById("formula-banner-icon");
    const titleEl = document.getElementById("formula-banner-title");
    const badgeEl = document.getElementById("formula-banner-badge");
    const descEl = document.getElementById("formula-banner-desc");
    const activeLabelEl = document.getElementById("formula-active-cat-label");

    if (iconEl) iconEl.textContent = meta.icon;
    if (titleEl) titleEl.textContent = meta.title;
    if (badgeEl) badgeEl.textContent = meta.badge;
    if (descEl) descEl.textContent = meta.desc;
    if (activeLabelEl) activeLabelEl.textContent = meta.shortLabel;

    // Update Category Tab Active styling
    document.querySelectorAll(".btn-formula-tab").forEach(tab => {
      const tCat = tab.getAttribute("data-cat");
      if (tCat === catName) {
        tab.className = "btn-formula-tab formula-tab-active px-2.5 py-1 rounded-lg text-[11px] font-semibold whitespace-nowrap";
      } else {
        tab.className = "btn-formula-tab px-2.5 py-1 rounded-lg text-[11px] font-semibold whitespace-nowrap bg-gray-900 text-gray-400 border border-gray-800 hover:text-white";
      }
    });

    // Sync studio-story-category select if requested
    if (syncDropdown) {
      const catSelect = document.getElementById("studio-story-category");
      if (catSelect) {
        for (let i = 0; i < catSelect.options.length; i++) {
          const optVal = catSelect.options[i].value;
          if (optVal === catName || catName.includes(optVal) || optVal.includes(catName.split(" ")[0])) {
            catSelect.selectedIndex = i;
            break;
          }
        }
      }
    }

    // Render topics for this category
    renderFormulaTopics(catName);
  }

  function renderFormulaTopics(catName) {
    const container = document.getElementById("winning-topic-pills");
    const countEl = document.getElementById("formula-topics-count");
    if (!container) return;

    // Look up topics from state.curatedTopics
    let topics = [];
    if (state.curatedTopics) {
      const key = Object.keys(state.curatedTopics).find(k => k === catName || catName.includes(k) || k.includes(catName));
      if (key && state.curatedTopics[key]) {
        topics = state.curatedTopics[key];
      }
    }

    if (countEl) countEl.textContent = `${topics.length} Curated Topics`;

    // Map each topic to a pill
    const pillsHtml = topics.map((t, idx) => {
      const displayTitle = t.title || t.topic_en || t.topic_hi || "Viral Topic";
      const shortDisplay = displayTitle.length > 36 ? displayTitle.substring(0, 34) + "..." : displayTitle;
      const emoji = t.icon || getTopicEmoji(displayTitle);
      return `
        <button type="button" class="btn-topic-pill ${idx === 0 ? 'topic-pill-active' : ''} px-2.5 py-1 rounded-lg text-[11px] transition font-medium flex items-center gap-1.5" data-idx="${idx}" data-topic="${displayTitle}">
          <span>${emoji}</span>
          <span>${shortDisplay}</span>
        </button>
      `;
    }).join("");

    const suggestBtnHtml = `
      <button type="button" id="btn-surprise-wwii-topic" class="px-2.5 py-1 rounded-lg bg-amber-600/30 border border-amber-500/50 text-[11px] text-amber-300 hover:bg-amber-600 hover:text-white transition flex items-center gap-1 font-semibold">
        <i data-lucide="sparkles" class="w-3 h-3"></i>
        <span>🎲 Suggest Fresh Topic</span>
      </button>
    `;

    container.innerHTML = pillsHtml + suggestBtnHtml;
    if (window.lucide) lucide.createIcons();

    // Attach click listener to each topic pill
    container.querySelectorAll(".btn-topic-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        const idx = parseInt(pill.getAttribute("data-idx"), 10);
        selectFormulaTopic(pill, topics[idx]);
      });
    });

    // Attach click listener to Suggest Fresh Topic button
    const btnSurprise = document.getElementById("btn-surprise-wwii-topic");
    if (btnSurprise) {
      btnSurprise.addEventListener("click", async () => {
        btnSurprise.disabled = true;
        btnSurprise.innerHTML = `<span class="animate-spin inline-block mr-1">🎲</span> Brainstorming...`;

        try {
          const res = await fetch("/api/studio/suggest_topic", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category: catName })
          });
          const data = await res.json();
          if (data && data.topic) {
            const promptInput = document.getElementById("studio-story-prompt");
            if (promptInput) promptInput.value = data.topic;

            const titleInput = document.getElementById("studio-title-input");
            if (titleInput) titleInput.value = data.topic;

            container.querySelectorAll(".btn-topic-pill").forEach(p => p.classList.remove("topic-pill-active"));

            showToast(`Brainstormed: "${data.topic.slice(0, 35)}..." Click 'Generate Script with Qwen' to draft!`, "success");
          }
        } catch (e) {
          showToast("Topic suggestion error: " + e.message, "danger");
        } finally {
          btnSurprise.disabled = false;
          btnSurprise.innerHTML = `<i data-lucide="sparkles" class="w-3 h-3"></i><span>🎲 Suggest Fresh Topic</span>`;
          if (window.lucide) lucide.createIcons();
        }
      });
    }

    // Do NOT auto-populate the editor automatically - user writes manually!
    // Pills are ready for optional inspiration, but never force-overwrite the editor.
  }

  function selectFormulaTopic(pillElement, topicData) {
    if (!topicData) return;

    // Toggle active pill classes
    const container = document.getElementById("winning-topic-pills");
    if (container) {
      container.querySelectorAll(".btn-topic-pill").forEach(p => {
        p.classList.remove("topic-pill-active");
      });
    }
    if (pillElement) {
      pillElement.classList.add("topic-pill-active");
    }

    const topicTitle = topicData.title || topicData.topic_en || topicData.topic_hi || "";
    const promptInput = document.getElementById("studio-story-prompt");
    if (promptInput) promptInput.value = topicTitle;

    const scriptInput = document.getElementById("studio-script-input");
    const titleInput = document.getElementById("studio-title-input");

    // If script is currently empty, load the example topic directly; if user already typed, ask or load
    const currentScript = scriptInput ? scriptInput.value.trim() : "";
    if (!currentScript || confirm(`Load example script for "${topicTitle.slice(0, 30)}..."? Your current draft will be replaced.`)) {
      if (topicData.script && scriptInput) {
        scriptInput.value = topicData.script;
      }
      if (titleInput) {
        titleInput.value = topicData.topic_hi || topicData.title || topicTitle;
      }
      if (topicData.keywords && Array.isArray(topicData.keywords)) {
        renderKeywordTags(topicData.keywords);
      }
      if (topicData.script) {
        updateScriptWordCountAndLanguage(topicData.script);
        runPolicyCheck(topicData.script, topicData.topic_hi || topicTitle);
      }
      showToast(`✓ Loaded: "${topicTitle.slice(0, 32)}..." (Edit freely!)`, "info");
    }
  }

  function getTopicEmoji(title) {
    const lower = (title || "").toLowerCase();
    if (lower.includes("grenade") || lower.includes("bomb") || lower.includes("hook")) return "💣";
    if (lower.includes("night witch") || lower.includes("plane") || lower.includes("pilot")) return "✈️";
    if (lower.includes("ghost army") || lower.includes("rubber") || lower.includes("tank")) return "🎈";
    if (lower.includes("habakkuk") || lower.includes("ice") || lower.includes("carrier")) return "🧊";
    if (lower.includes("coffee") || lower.includes("submarine")) return "☕";
    if (lower.includes("black hole") || lower.includes("supermassive")) return "🌌";
    if (lower.includes("sun") || lower.includes("screaming") || lower.includes("solar")) return "☀️";
    if (lower.includes("stone") || lower.includes("sailing") || lower.includes("death valley")) return "🪨";
    if (lower.includes("lake") || lower.includes("natron") || lower.includes("animal")) return "🩸";
    if (lower.includes("snake") || lower.includes("ilha")) return "🐍";
    if (lower.includes("sentinel") || lower.includes("tribe") || lower.includes("island")) return "🏝️";
    if (lower.includes("antikythera") || lower.includes("computer") || lower.includes("greek")) return "⚙️";
    if (lower.includes("roman") || lower.includes("concrete") || lower.includes("pantheon")) return "🏛️";
    if (lower.includes("quantum") || lower.includes("password") || lower.includes("encryption")) return "🔐";
    if (lower.includes("voyager") || lower.includes("probe") || lower.includes("signal")) return "🛰️";
    return "⚡";
  }

  // Preview Prompt Button Handler
  const btnPreviewPrompt = document.getElementById("btn-preview-prompt");
  if (btnPreviewPrompt) {
    btnPreviewPrompt.addEventListener("click", async () => {
      const catSelect = document.getElementById("studio-story-category");
      const selectedCatOption = catSelect?.options[catSelect.selectedIndex];
      const categoryName = activeStudioMode === "curated" 
        ? document.getElementById("studio-curated-category")?.value 
        : catSelect?.value;
      const langChoice = document.getElementById("studio-language")?.value;
      const lang = langChoice === "auto" ? (selectedCatOption?.getAttribute("data-lang") || "hindi") : langChoice;
      const tplId = document.getElementById("studio-prompt-template")?.value;
      const customInst = document.getElementById("studio-custom-instructions")?.value;

      const payload = {
        mode: activeStudioMode,
        prompt: document.getElementById("studio-story-prompt")?.value || "",
        exact_script: document.getElementById("studio-exact-script")?.value || "",
        category: categoryName || "Space & Universe",
        language: lang,
        prompt_template_id: tplId || null,
        custom_instructions: customInst || "",
        topic: activeStudioMode === "curated" ? document.getElementById("studio-curated-topic")?.value : "",
        model: document.getElementById("studio-model-selector")?.value || "qwen2.5:3b"
      };

      try {
        const res = await fetch("/api/studio/preview_prompt", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        document.getElementById("preview-sys-prompt-text").textContent = data.system_prompt;
        document.getElementById("preview-user-prompt-text").textContent = data.user_prompt;
        document.getElementById("prompt-preview-modal").classList.remove("hidden");
        if (window.lucide) lucide.createIcons();
      } catch (e) {
        showToast("Could not preview prompt: " + e.message, "danger");
      }
    });
  }

  // Close Prompt Preview Modal
  const closePreview1 = document.getElementById("btn-close-prompt-preview");
  const closePreview2 = document.getElementById("btn-close-prompt-preview-2");
  const promptModal = document.getElementById("prompt-preview-modal");
  if (closePreview1) closePreview1.addEventListener("click", () => promptModal.classList.add("hidden"));
  if (closePreview2) closePreview2.addEventListener("click", () => promptModal.classList.add("hidden"));

  // Copy Buttons in Prompt Preview
  const btnCopySys = document.getElementById("btn-copy-sys-prompt");
  if (btnCopySys) {
    btnCopySys.addEventListener("click", () => {
      const text = document.getElementById("preview-sys-prompt-text")?.textContent;
      if (text) {
        navigator.clipboard.writeText(text);
        showToast("System prompt copied to clipboard!", "success");
      }
    });
  }
  const btnCopyUser = document.getElementById("btn-copy-user-prompt");
  if (btnCopyUser) {
    btnCopyUser.addEventListener("click", () => {
      const text = document.getElementById("preview-user-prompt-text")?.textContent;
      if (text) {
        navigator.clipboard.writeText(text);
        showToast("User prompt copied to clipboard!", "success");
      }
    });
  }

  // Proceed to Generate from Preview Modal
  const btnProceedGen = document.getElementById("btn-proceed-generate-from-preview");
  if (btnProceedGen) {
    btnProceedGen.addEventListener("click", () => {
      if (promptModal) promptModal.classList.add("hidden");
      if (btnGenerateScript) btnGenerateScript.click();
    });
  }

  function renderKeywordTags(keywords) {
    const container = document.getElementById("studio-keywords-container");
    if (!container) return;
    if (!keywords || keywords.length === 0) {
      container.innerHTML = `<span class="text-xs text-gray-500 italic">No keywords detected</span>`;
      return;
    }
    container.innerHTML = keywords.map(kw => `
      <span class="px-2 py-0.5 rounded-md bg-violet-500/20 text-violet-300 text-xs font-mono font-medium flex items-center gap-1 border border-violet-500/30">
        <i data-lucide="tag" class="w-3 h-3 text-violet-400"></i>
        <span>${kw}</span>
      </span>
    `).join("");
    if (window.lucide) lucide.createIcons();
  }

  function renderFactsChecklist(facts) {
    const container = document.getElementById("studio-facts-container");
    if (!container) return;
    if (!facts || facts.length === 0) {
      container.innerHTML = `<p class="text-gray-500 italic">No checklist loaded.</p>`;
      return;
    }
    container.innerHTML = facts.map(f => `
      <div class="flex items-center space-x-2 text-gray-300 text-xs">
        <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-400 flex-shrink-0"></i>
        <span>${f}</span>
      </div>
    `).join("");
    if (window.lucide) lucide.createIcons();
  }

  async function runPolicyCheck(script, title) {
    if (!script) return;
    try {
      const res = await fetch("/api/studio/policy_check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script, title: title || "" })
      });
      const data = await res.json();

      const scoreEl = document.getElementById("studio-quality-score");
      if (scoreEl) scoreEl.textContent = `${data.quality_score} / 100`;

      const durationBadge = document.getElementById("studio-duration-badge");
      if (durationBadge) {
        durationBadge.textContent = `~${data.est_duration_seconds}s (${data.word_count} words)`;
        durationBadge.className = data.duration_status === "perfect" 
          ? "text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 font-medium"
          : "text-xs px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-400 font-medium";
      }

      const suggestionsBox = document.getElementById("studio-policy-suggestions");
      if (suggestionsBox) {
        suggestionsBox.innerHTML = (data.suggestions || []).map(s => `<p>${s}</p>`).join("");
      }
    } catch (e) {
      console.warn("Policy check error:", e);
    }
  }

  // Save Custom Draft
  const btnSaveDraft = document.getElementById("btn-save-draft");
  if (btnSaveDraft) {
    btnSaveDraft.addEventListener("click", async () => {
      const titleInput = document.getElementById("studio-title-input");
      const promptInput = document.getElementById("studio-story-prompt");
      const title = (titleInput?.value || promptInput?.value || "").trim() || "Untitled Draft";

      const scriptInput = document.getElementById("studio-script-input");
      const exactScriptInput = document.getElementById("studio-exact-script");
      const script = (scriptInput?.value || exactScriptInput?.value || "").trim();

      const catSelect = document.getElementById("studio-story-category");
      const categoryName = catSelect?.value || "Space & Universe";
      const editingStyle = document.getElementById("studio-editing-style-prompt")?.value || "";

      if (!script && !title) {
        showToast("Please enter a title or script to save as draft.", "warning");
        return;
      }

      try {
        const res = await fetch("/api/studio/drafts/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: title,
            hindi_script: script,
            category: categoryName,
            editing_style: editingStyle,
            status: "draft"
          })
        });
        if (res.ok) {
          showToast("Draft saved successfully!", "success");
        } else {
          showToast("Failed to save draft.", "danger");
        }
      } catch (e) {
        showToast("Draft save error: " + e.message, "danger");
      }
    });
  }

  // Send to Video Pipeline
  const btnSendPipeline = document.getElementById("btn-send-to-pipeline");
  if (btnSendPipeline) {
    btnSendPipeline.addEventListener("click", async () => {
      const titleInput = document.getElementById("studio-title-input");
      const promptInput = document.getElementById("studio-story-prompt");
      const title = (titleInput?.value || promptInput?.value || "").trim() || "COSMOS Short";

      const scriptInput = document.getElementById("studio-script-input");
      const exactScriptInput = document.getElementById("studio-exact-script");
      const script = (scriptInput?.value || exactScriptInput?.value || "").trim();

      const catSelect = document.getElementById("studio-story-category");
      const categoryName = catSelect?.value || "Space & Universe";
      const selectedCatOption = catSelect?.options[catSelect.selectedIndex];
      const langChoice = document.getElementById("studio-language")?.value;
      const lang = langChoice === "auto" ? (selectedCatOption?.getAttribute("data-lang") || "hindi") : langChoice;
      const themeColor = selectedCatOption?.getAttribute("data-color");
      
      if (!script) {
        showToast("Please enter your narration script first in the Narration Script box.", "warning");
        if (scriptInput) scriptInput.focus();
        return;
      }

      const editingStyle = document.getElementById("studio-editing-style-prompt")?.value || "";
      const scriptLang = document.getElementById("studio-script-lang")?.value || "auto";
      const voiceName = document.getElementById("studio-script-voice")?.value || "auto";

      const origHtml = btnSendPipeline.innerHTML;
      btnSendPipeline.innerHTML = `<span class="inline-block animate-spin mr-1.5">&#9203;</span><span>Sending to Pipeline...</span>`;
      btnSendPipeline.disabled = true;

      showToast(`Launching video pipeline with full animations & voiceover in ${scriptLang}...`, "info");
      
      try {
        const res = await fetch("/api/video/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: title,
            category: categoryName,
            language: scriptLang,
            voice_name: voiceName,
            theme_color: themeColor || null,
            hindi_script: script,
            editing_style: editingStyle,
            mode: "script"
          })
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || "Server error: " + res.status);
        }

        const data = await res.json();
        
        state.activeJobId = data.job_id;
        showToast("Video render job launched! Switching to Pipeline view...", "success");
        switchView("video");
        startJobPolling(data.job_id, title);
        fetchActivePipeline();
      } catch (e) {
        showToast("Pipeline launch failed: " + e.message, "danger");
      } finally {
        btnSendPipeline.innerHTML = origHtml;
        btnSendPipeline.disabled = false;
        if (window.lucide) lucide.createIcons();
      }
    });
  }

  const btnQuickManageCat = document.getElementById("btn-quick-manage-cat");
  if (btnQuickManageCat) {
    btnQuickManageCat.addEventListener("click", () => {
      switchView("categories");
    });
  }

  // ----------------------------------------------------
  // CATEGORIES & THEMES MANAGEMENT
  // ----------------------------------------------------
  async function fetchCategories() {
    try {
      const res = await fetch("/api/categories?include_disabled=true");
      const data = await res.json();
      state.categories = data.categories || [];
      
      const countBadge = document.getElementById("categories-count-badge");
      if (countBadge) countBadge.textContent = state.categories.length;

      renderCategoriesGrid();
      populateStudioCategoryDropdown();
    } catch (e) {
      console.warn("Categories fetch error:", e);
    }
  }

  function populateStudioCategoryDropdown() {
    const catSelect = document.getElementById("studio-story-category");
    if (!catSelect) return;

    const currentVal = catSelect.value;
    catSelect.innerHTML = state.categories
      .filter(c => c.is_enabled)
      .map(c => `
        <option value="${c.name}" data-lang="${c.default_language}" data-color="${c.accent_color}" ${c.is_default ? 'data-default="true"' : ''}>
          ${c.icon || '🎯'} ${c.name} (${c.theme_label || c.name})
        </option>
      `).join("");

    if (currentVal && state.categories.some(c => c.name === currentVal)) {
      catSelect.value = currentVal;
    } else {
      const def = state.categories.find(c => c.is_default && c.is_enabled);
      if (def) catSelect.value = def.name;
    }

    // Populate Reassignment Select in Delete Modal
    const reassignSelect = document.getElementById("delete-reassign-select");
    if (reassignSelect) {
      reassignSelect.innerHTML = state.categories
        .filter(c => c.is_enabled)
        .map(c => `<option value="${c.id}">${c.icon || '🎯'} ${c.name}</option>`)
        .join("");
    }
  }

  async function fetchPromptTemplates() {
    try {
      const res = await fetch("/api/categories/templates/all");
      const data = await res.json();
      state.promptTemplates = data.templates || [];

      const tplSelect = document.getElementById("studio-prompt-template");
      if (tplSelect) {
        tplSelect.innerHTML = `<option value="">Standard Template</option>` + state.promptTemplates.map(t => `
          <option value="${t.id}">${t.name} (${t.language.toUpperCase()})</option>
        `).join("");
      }
    } catch (e) {
      console.warn("Prompt templates fetch error:", e);
    }
  }

  function renderCategoriesGrid() {
    const grid = document.getElementById("categories-grid");
    if (!grid) return;

    let filtered = state.categories;

    // Language Filter
    if (state.activeCategoryFilter !== "all") {
      filtered = filtered.filter(c => c.default_language.toLowerCase() === state.activeCategoryFilter.toLowerCase());
    }

    // Search Filter
    if (state.activeCategorySearch) {
      const q = state.activeCategorySearch.toLowerCase();
      filtered = filtered.filter(c => 
        c.name.toLowerCase().includes(q) || 
        (c.description && c.description.toLowerCase().includes(q)) ||
        (c.theme_label && c.theme_label.toLowerCase().includes(q))
      );
    }

    if (filtered.length === 0) {
      grid.innerHTML = `
        <div class="col-span-full cosmos-card p-8 text-center text-gray-500">
          <i data-lucide="palette" class="w-10 h-10 mx-auto mb-2 text-gray-600"></i>
          <p class="text-sm font-semibold text-gray-400">No categories found matching criteria.</p>
          <p class="text-xs text-gray-500 mt-1">Try clearing the search or click 'New Category' above to create one.</p>
        </div>
      `;
      if (window.lucide) lucide.createIcons();
      return;
    }

    grid.innerHTML = filtered.map(c => {
      const isDefault = c.is_default;
      const isEnabled = c.is_enabled;
      const accent = c.accent_color || "#8B5CF6";
      const textColor = c.text_color || "#000000";
      const langLabel = c.default_language === "hinglish" ? "Roman Hinglish" : (c.default_language === "english" ? "English" : "Hindi Devanagari");
      const langColor = c.default_language === "hinglish" ? "bg-cyan-500/20 text-cyan-300" : (c.default_language === "english" ? "bg-amber-500/20 text-amber-300" : "bg-violet-500/20 text-violet-300");

      return `
        <div class="cosmos-card p-5 relative overflow-hidden flex flex-col justify-between space-y-4 hover:border-gray-700 transition" style="border-top: 4px solid ${accent};">
          <div>
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center space-x-2">
                <span class="text-xl">${c.icon || '🎯'}</span>
                <div>
                  <h3 class="font-bold text-sm text-white flex items-center gap-1.5">
                    <span>${c.name}</span>
                    ${isDefault ? '<span class="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-semibold">DEFAULT</span>' : ''}
                    ${!isEnabled ? '<span class="text-[10px] px-1.5 py-0.2 rounded bg-gray-800 text-gray-400">DISABLED</span>' : ''}
                  </h3>
                  <p class="text-[11px] text-gray-400">${c.theme_label || c.name}</p>
                </div>
              </div>
              <span class="w-4 h-4 rounded-full border border-white/20 shadow-sm" style="background-color: ${accent};" title="${accent}"></span>
            </div>

            <p class="text-xs text-gray-300 line-clamp-2 leading-relaxed min-h-[32px]">
              ${c.description || 'Custom category for YouTube Shorts generation.'}
            </p>

            <div class="flex flex-wrap gap-1.5 pt-3 text-[10px] font-medium">
              <span class="px-2 py-0.5 rounded-md ${langColor}">${langLabel.toUpperCase()}</span>
              <span class="px-2 py-0.5 rounded-md bg-gray-900 border border-gray-800 text-gray-300 font-mono">${c.default_duration || 52}s Duration</span>
              <span class="px-2 py-0.5 rounded-md bg-gray-900 border border-gray-800 text-gray-400">${c.visual_style || 'Cinematic'}</span>
            </div>

            ${c.custom_prompt_instructions ? `
              <div class="mt-2.5 p-2 bg-gray-900/60 rounded-lg border border-gray-800/80 text-[11px] text-gray-400 line-clamp-2 italic">
                "${c.custom_prompt_instructions}"
              </div>
            ` : ''}
          </div>

          <!-- Bottom Actions -->
          <div class="flex items-center justify-between pt-3 border-t border-gray-800 text-xs">
            <div class="flex items-center space-x-1">
              ${!isDefault ? `
                <button class="p-1.5 rounded-lg text-gray-400 hover:text-amber-400 hover:bg-gray-800/80 btn-set-default" data-id="${c.id}" title="Set as Default">
                  <i data-lucide="star" class="w-3.5 h-3.5"></i>
                </button>
              ` : ''}
              <button class="p-1.5 rounded-lg text-gray-400 hover:text-cyan-400 hover:bg-gray-800/80 btn-dup-cat" data-id="${c.id}" title="Duplicate Category">
                <i data-lucide="copy" class="w-3.5 h-3.5"></i>
              </button>
            </div>
            
            <div class="flex items-center space-x-1">
              <button class="px-2.5 py-1 rounded-lg text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 btn-edit-cat flex items-center gap-1 font-medium text-[11px]" data-id="${c.id}">
                <i data-lucide="edit-3" class="w-3 h-3"></i>
                <span>Edit</span>
              </button>
              <button class="p-1.5 rounded-lg text-gray-400 hover:text-rose-400 hover:bg-gray-800/80 btn-del-cat" data-id="${c.id}" title="Delete Category">
                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
              </button>
            </div>
          </div>
        </div>
      `;
    }).join("");

    if (window.lucide) lucide.createIcons();
    attachCategoryCardListeners();
  }

  function attachCategoryCardListeners() {
    // Edit Category
    document.querySelectorAll(".btn-edit-cat").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        const found = state.categories.find(c => c.id === id);
        if (found) openCategoryModal(found);
      });
    });

    // Duplicate Category
    document.querySelectorAll(".btn-dup-cat").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-id");
        showToast("Duplicating category...", "info");
        try {
          const res = await fetch(`/api/categories/${id}/duplicate`, { method: "POST" });
          if (res.ok) {
            showToast("Category duplicated successfully!", "success");
            fetchCategories();
          } else {
            const err = await res.json();
            showToast("Duplicate error: " + err.detail, "danger");
          }
        } catch (e) {
          showToast("Network error: " + e.message, "danger");
        }
      });
    });

    // Set Default Category
    document.querySelectorAll(".btn-set-default").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-id");
        try {
          const res = await fetch(`/api/categories/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_default: true })
          });
          if (res.ok) {
            showToast("Default category updated!", "success");
            fetchCategories();
          }
        } catch (e) {
          showToast("Update error: " + e.message, "danger");
        }
      });
    });

    // Delete Category
    document.querySelectorAll(".btn-del-cat").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        const found = state.categories.find(c => c.id === id);
        if (found) openDeleteModal(found);
      });
    });
  }

  // ----------------------------------------------------
  // CATEGORY CREATE / EDIT MODAL & LIVE PREVIEW
  // ----------------------------------------------------
  const catModal = document.getElementById("category-modal");
  const btnCloseCatModal = document.getElementById("btn-close-cat-modal");
  const btnCancelCatModal = document.getElementById("btn-cancel-cat-modal");
  const btnSaveCat = document.getElementById("btn-save-cat");
  const btnCreateCategory = document.getElementById("btn-create-category");

  if (btnCreateCategory) {
    btnCreateCategory.addEventListener("click", () => openCategoryModal(null));
  }
  if (btnCloseCatModal) btnCloseCatModal.addEventListener("click", () => catModal.classList.add("hidden"));
  if (btnCancelCatModal) btnCancelCatModal.addEventListener("click", () => catModal.classList.add("hidden"));

  function openCategoryModal(cat = null) {
    const isEdit = !!cat;
    document.getElementById("category-modal-title").textContent = isEdit ? `Edit Category: ${cat.name}` : "Create Video Category";
    document.getElementById("form-cat-id").value = isEdit ? cat.id : "";
    document.getElementById("form-cat-name").value = isEdit ? cat.name : "";
    document.getElementById("form-cat-desc").value = isEdit ? (cat.description || "") : "";
    document.getElementById("form-cat-icon").value = isEdit ? (cat.icon || "🎯") : "🎯";
    document.getElementById("form-cat-color").value = isEdit ? (cat.accent_color || "#00E5FF") : "#00E5FF";
    document.getElementById("form-cat-color-hex").value = isEdit ? (cat.accent_color || "#00E5FF") : "#00E5FF";
    document.getElementById("form-cat-theme-label").value = isEdit ? (cat.theme_label || "") : "";
    document.getElementById("form-cat-style").value = isEdit ? (cat.visual_style || "Cinematic Drone") : "Cinematic Drone";
    document.getElementById("form-cat-lang").value = isEdit ? (cat.default_language || "hindi") : "hindi";
    document.getElementById("form-cat-duration").value = isEdit ? (cat.default_duration || 52) : 52;
    document.getElementById("form-cat-pos-y").value = isEdit ? (cat.caption_position_y || 76) : 76;
    document.getElementById("form-caption-pos-val").textContent = `${isEdit ? (cat.caption_position_y || 76) : 76}%`;
    document.getElementById("form-cat-prompt").value = isEdit ? (cat.custom_prompt_instructions || "") : "";
    document.getElementById("form-cat-default").checked = isEdit ? !!cat.is_default : false;
    document.getElementById("form-cat-enabled").checked = isEdit ? !!cat.is_enabled : true;

    updateThemeLivePreview();
    catModal.classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
  }

  // Live Preview Update Logic
  function updateThemeLivePreview() {
    const icon = document.getElementById("form-cat-icon")?.value || "🎯";
    const name = document.getElementById("form-cat-name")?.value || "Category Name";
    const color = document.getElementById("form-cat-color")?.value || "#00E5FF";
    const lang = document.getElementById("form-cat-lang")?.value || "hindi";
    const style = document.getElementById("form-cat-style")?.value || "Cinematic Drone";
    const posY = document.getElementById("form-cat-pos-y")?.value || 76;

    // Calculate readable text color
    const hex = color.lstrip ? color.lstrip("#") : color.replace("#", "");
    let textColor = "#000000";
    if (hex.length === 6) {
      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);
      const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
      textColor = lum > 0.55 ? "#000000" : "#FFFFFF";
    }

    // Modal Badge Icon
    const modalIconBadge = document.getElementById("modal-icon-badge");
    if (modalIconBadge) modalIconBadge.textContent = icon;

    // Form Pill
    const formPill = document.getElementById("form-color-preview-pill");
    if (formPill) {
      formPill.style.backgroundColor = color;
      formPill.style.color = textColor;
      formPill.textContent = color.toUpperCase();
    }

    // Live 9:16 Mockup elements
    const prevIcon = document.getElementById("preview-cat-icon");
    if (prevIcon) prevIcon.textContent = icon;

    const prevName = document.getElementById("preview-cat-name");
    if (prevName) prevName.textContent = name;

    const prevPill = document.getElementById("preview-cat-pill");
    if (prevPill) {
      prevPill.style.backgroundColor = color;
      prevPill.style.color = textColor;
    }

    const prevSubPill = document.getElementById("preview-subtitle-pill");
    if (prevSubPill) {
      prevSubPill.style.backgroundColor = color;
      prevSubPill.style.color = textColor;
      prevSubPill.textContent = lang === "hinglish" 
        ? "Kya aap jaante hain ye mystery sach hai?!" 
        : (lang === "english" ? "Did you know this mysterious fact?!" : "क्या आप जानते हैं ये रहस्य सच है?!");
    }

    const prevStyle = document.getElementById("preview-sample-style");
    if (prevStyle) prevStyle.textContent = `Visual: ${style}`;

    const prevLangBadge = document.getElementById("preview-lang-badge");
    if (prevLangBadge) {
      if (lang === "hinglish") {
        prevLangBadge.textContent = "ROMAN HINGLISH";
        prevLangBadge.className = "px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cyan-500/20 text-cyan-300";
      } else if (lang === "english") {
        prevLangBadge.textContent = "ENGLISH";
        prevLangBadge.className = "px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/20 text-amber-300";
      } else {
        prevLangBadge.textContent = "HINDI DEVANAGARI";
        prevLangBadge.className = "px-2 py-0.5 rounded-full text-[10px] font-semibold bg-violet-500/20 text-violet-300";
      }
    }

    const prevSampleTitle = document.getElementById("preview-sample-title");
    if (prevSampleTitle) {
      prevSampleTitle.textContent = lang === "hinglish"
        ? "Dosto, kya aap jaante hain ki universe ka sabse bada secret kya hai?"
        : (lang === "english" ? "What is the most terrifying secret in the universe?" : "क्या आप जानते हैं कि ब्रह्मांड का सबसे बड़ा रहस्य क्या है?");
    }
  }

  // Attach live preview event listeners
  ["form-cat-name", "form-cat-icon", "form-cat-style", "form-cat-lang"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("input", updateThemeLivePreview);
  });

  const catColorInput = document.getElementById("form-cat-color");
  const catColorHex = document.getElementById("form-cat-color-hex");
  if (catColorInput && catColorHex) {
    catColorInput.addEventListener("input", (e) => {
      catColorHex.value = e.target.value.toUpperCase();
      updateThemeLivePreview();
    });
    catColorHex.addEventListener("input", (e) => {
      if (/^#[0-9A-Fa-f]{6}$/.test(e.target.value)) {
        catColorInput.value = e.target.value;
        updateThemeLivePreview();
      }
    });
  }

  // Quick Preset Swatches
  document.querySelectorAll("#color-preset-swatches button").forEach(swatch => {
    swatch.addEventListener("click", () => {
      const col = swatch.getAttribute("data-color");
      const label = swatch.getAttribute("data-label");
      if (catColorInput) catColorInput.value = col;
      if (catColorHex) catColorHex.value = col.toUpperCase();
      const themeLabelInput = document.getElementById("form-cat-theme-label");
      if (themeLabelInput && !themeLabelInput.value) themeLabelInput.value = label;
      updateThemeLivePreview();
    });
  });

  // Slider Position
  const posSlider = document.getElementById("form-cat-pos-y");
  if (posSlider) {
    posSlider.addEventListener("input", (e) => {
      document.getElementById("form-caption-pos-val").textContent = `${e.target.value}%`;
      updateThemeLivePreview();
    });
  }

  // Save Category Button
  if (btnSaveCat) {
    btnSaveCat.addEventListener("click", async () => {
      const catId = document.getElementById("form-cat-id").value;
      const name = document.getElementById("form-cat-name").value.trim();
      const accentColor = document.getElementById("form-cat-color").value;

      if (!name) {
        showToast("Category name is required.", "warning");
        return;
      }

      const payload = {
        name: name,
        description: document.getElementById("form-cat-desc").value.trim(),
        accent_color: accentColor,
        icon: document.getElementById("form-cat-icon").value.trim() || "🎯",
        theme_label: document.getElementById("form-cat-theme-label").value.trim() || name,
        visual_style: document.getElementById("form-cat-style").value,
        default_language: document.getElementById("form-cat-lang").value,
        default_duration: parseInt(document.getElementById("form-cat-duration").value, 10) || 52,
        caption_position_y: parseFloat(document.getElementById("form-cat-pos-y").value) || 76.0,
        custom_prompt_instructions: document.getElementById("form-cat-prompt").value.trim(),
        is_default: document.getElementById("form-cat-default").checked,
        is_enabled: document.getElementById("form-cat-enabled").checked
      };

      try {
        let res;
        if (catId) {
          res = await fetch(`/api/categories/${catId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
        } else {
          res = await fetch("/api/categories", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
        }

        if (res.ok) {
          showToast(`Category '${name}' saved successfully!`, "success");
          catModal.classList.add("hidden");
          fetchCategories();
        } else {
          const err = await res.json();
          showToast(err.detail || "Save failed.", "danger");
        }
      } catch (e) {
        showToast("Network error: " + e.message, "danger");
      }
    });
  }

  // ----------------------------------------------------
  // DELETE CATEGORY SAFETY MODAL
  // ----------------------------------------------------
  const delModal = document.getElementById("category-delete-modal");
  const btnCancelDel = document.getElementById("btn-cancel-delete-modal");
  const btnConfirmDel = document.getElementById("btn-confirm-delete-cat");

  if (btnCancelDel) btnCancelDel.addEventListener("click", () => delModal.classList.add("hidden"));

  function openDeleteModal(cat) {
    state.categoryToDelete = cat;
    document.getElementById("delete-cat-message").textContent = `Are you sure you want to delete category '${cat.name}'? All existing video drafts will be safely reassigned or preserved so nothing is broken.`;
    delModal.classList.remove("hidden");
  }

  if (btnConfirmDel) {
    btnConfirmDel.addEventListener("click", async () => {
      if (!state.categoryToDelete) return;
      const catId = state.categoryToDelete.id;
      const reassignId = document.getElementById("delete-reassign-select")?.value;
      const archiveOnly = document.getElementById("delete-archive-only")?.checked;

      try {
        const res = await fetch(`/api/categories/${catId}`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            reassign_to_id: reassignId || null,
            archive_only: archiveOnly
          })
        });

        if (res.ok) {
          showToast(`Category removed safely!`, "success");
          delModal.classList.add("hidden");
          fetchCategories();
        } else {
          const err = await res.json();
          showToast(err.detail || "Delete failed", "danger");
        }
      } catch (e) {
        showToast("Network error: " + e.message, "danger");
      }
    });
  }

  // Search & Filter Listeners for Categories View
  const searchInput = document.getElementById("categories-search");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      state.activeCategorySearch = e.target.value.trim();
      renderCategoriesGrid();
    });
  }

  const catFilterContainer = document.getElementById("cat-filter-container");
  if (catFilterContainer) {
    catFilterContainer.addEventListener("click", (e) => {
      const btn = e.target.closest(".cat-filter-btn");
      if (!btn) return;
      catFilterContainer.querySelectorAll(".cat-filter-btn").forEach(b => {
        b.classList.remove("cat-filter-active", "active", "border-violet-500/40", "bg-violet-500/10", "text-white");
        b.classList.add("border-gray-800", "bg-gray-900", "text-gray-400");
      });
      btn.classList.add("cat-filter-active", "border-violet-500/40", "bg-violet-500/10", "text-white");
      btn.classList.remove("border-gray-800", "bg-gray-900", "text-gray-400");

      state.activeCategoryFilter = btn.getAttribute("data-lang") || "all";
      renderCategoriesGrid();
    });
  }

  // Export & Import Handlers
  const btnExport = document.getElementById("btn-export-categories");
  if (btnExport) {
    btnExport.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/categories/data/export");
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `cosmos_categories_export_${new Date().toISOString().slice(0,10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
        showToast("Exported categories successfully!", "success");
      } catch (e) {
        showToast("Export failed: " + e.message, "danger");
      }
    });
  }

  const btnImportTrigger = document.getElementById("btn-import-categories-trigger");
  const fileInput = document.getElementById("import-categories-file");
  if (btnImportTrigger && fileInput) {
    btnImportTrigger.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = async (ev) => {
        try {
          const payload = JSON.parse(ev.target.result);
          const res = await fetch("/api/categories/data/import", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          const result = await res.json();
          showToast(`Imported ${result.imported_categories} categories!`, "success");
          fetchCategories();
        } catch (err) {
          showToast("Invalid JSON file: " + err.message, "danger");
        }
      };
      reader.readAsText(file);
    });
  }

  // ----------------------------------------------------
  // VIDEO PIPELINE & PLAYER
  // ----------------------------------------------------
  async function fetchJobs() {
    try {
      const res = await fetch("/api/video/jobs?limit=10");
      const data = await res.json();
      state.jobs = data.jobs || [];
      renderJobsList(state.jobs);

      // If a completed job exists, load the latest one into preview
      const completed = state.jobs.find(j => j.status === "completed" && j.video_path);
      if (completed) {
        loadVideoPreview(completed);
      }
    } catch (e) {
      console.warn("Jobs fetch error:", e);
    }
  }

  function renderJobsList(jobs) {
    const container = document.getElementById("video-jobs-list");
    if (!container) return;

    if (!jobs || jobs.length === 0) {
      container.innerHTML = `<p class="text-xs text-gray-500">No render jobs yet.</p>`;
      return;
    }

    container.innerHTML = jobs.map(j => {
      const isDone = j.status === "completed";
      const isInterrupted = j.status === "interrupted";
      const isFailed = j.status === "failed";
      const statusColor = isDone 
        ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20" 
        : (isInterrupted 
          ? "text-amber-400 bg-amber-500/10 border border-amber-500/20" 
          : (isFailed 
            ? "text-rose-400 bg-rose-500/10 border border-rose-500/20" 
            : "text-violet-400 bg-violet-500/10 border border-violet-500/20"));

      return `
        <div class="p-3 rounded-xl bg-gray-900 border border-gray-800 hover:border-violet-500/50 hover:bg-gray-850 transition flex items-center justify-between cursor-pointer job-item group shadow-sm" data-id="${j.job_id}" title="Click to inspect 7-step pipeline lifecycle, retry, or preview">
          <div class="space-y-0.5 max-w-[70%]">
            <div class="flex items-center space-x-2">
              <i data-lucide="play-circle" class="w-3.5 h-3.5 text-violet-400 group-hover:scale-110 transition"></i>
              <p class="font-bold text-xs text-white truncate">${j.job_id}</p>
            </div>
            <p class="text-[11px] text-gray-400 truncate">${j.current_step || j.status}</p>
          </div>
          <div class="flex items-center space-x-2">
            <span class="text-[10px] font-mono font-bold text-gray-400">${j.progress_pct || 0}%</span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${statusColor}">${j.status.toUpperCase()}</span>
            <span class="text-[10px] text-violet-400 opacity-0 group-hover:opacity-100 transition hidden sm:inline">Inspect →</span>
          </div>
        </div>
      `;
    }).join("");

    if (window.lucide) lucide.createIcons();

    // Attach click listeners to every job item: ALWAYS open Job Lifecycle & Inspector Modal
    document.querySelectorAll(".job-item").forEach(item => {
      item.addEventListener("click", () => {
        const jId = item.getAttribute("data-id");
        const found = state.jobs.find(x => x.job_id === jId);
        if (found) {
          if (found.video_path) {
            loadVideoPreview(found);
          }
          openJobModal(found);
        }
      });
    });
  }

  function loadVideoPreview(job) {
    const player = document.getElementById("studio-video-player");
    const source = document.getElementById("video-source");
    const emptyState = document.getElementById("video-empty-state");
    const titleEl = document.getElementById("preview-video-title");
    const thumbImg = document.getElementById("preview-thumbnail-img");

    state.currentVideoPath = job.video_path;
    state.currentThumbnailPath = job.thumbnail_path;
    state.currentTitle = job.job_id;

    if (source && player) {
      source.src = `/api/video/stream/${job.job_id}`;
      player.load();
      if (emptyState) emptyState.classList.add("hidden");
    }

    if (titleEl) titleEl.textContent = job.job_id;
    if (thumbImg && job.thumbnail_path) {
      thumbImg.src = `/api/video/thumbnail/${job.job_id}`;
    }
  }

  function startJobPolling(jobId, title) {
    const card = document.getElementById("video-progress-card");
    const titleEl = document.getElementById("job-active-title");
    const stepEl = document.getElementById("job-active-step");
    const pctEl = document.getElementById("job-active-pct");
    const fillEl = document.getElementById("job-progress-fill");

    if (card) card.classList.remove("hidden");
    if (titleEl) titleEl.textContent = title || "Creating Video...";

    if (state.pollInterval) clearInterval(state.pollInterval);

    state.pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/video/status/${jobId}`);
        const job = await res.json();

        if (stepEl) stepEl.textContent = job.current_step || "Processing...";
        if (pctEl) pctEl.textContent = `${job.progress_pct}%`;
        if (fillEl) fillEl.style.width = `${job.progress_pct}%`;

        // Keep modal live if inspecting this job
        if (state.selectedJob && state.selectedJob.job_id === jobId) {
          updateJobModalUI(job);
        }
        fetchActivePipeline();

        if (job.status === "completed") {
          clearInterval(state.pollInterval);
          showToast("Video rendered and synced successfully!", "success");
          fetchJobs();
          if (state.selectedJob && state.selectedJob.job_id === jobId) {
            updateJobModalUI(job);
          }
          setTimeout(() => {
            if (card) card.classList.add("hidden");
          }, 3000);
        } else if (job.status === "failed") {
          clearInterval(state.pollInterval);
          showToast("Video generation failed: " + job.error_message, "danger");
          fetchJobs();
          if (state.selectedJob && state.selectedJob.job_id === jobId) {
            updateJobModalUI(job);
          }
        }
      } catch (e) {
        console.warn("Polling error:", e);
      }
    }, 2000);
  }

  // ----------------------------------------------------
  // JOB LIFECYCLE & PIPELINE TRACKER
  // ----------------------------------------------------
  const jobModal = document.getElementById("job-detail-modal");
  const btnCloseJobModal = document.getElementById("btn-close-job-modal");
  const btnRetryJob = document.getElementById("btn-retry-job");
  const btnDeleteJob = document.getElementById("btn-delete-job");
  const btnJobLoadPreview = document.getElementById("btn-job-load-preview");
  const btnJobSchedule = document.getElementById("btn-job-schedule");
  const headerTrackerBtn = document.getElementById("header-pipeline-tracker");

  function initPipelineTracker() {
    if (headerTrackerBtn) {
      headerTrackerBtn.addEventListener("click", () => {
        if (state.activePipelineJob) {
          openJobModal(state.activePipelineJob);
        } else if (state.jobs && state.jobs.length > 0) {
          openJobModal(state.jobs[0]);
        } else {
          showToast("No render jobs yet. Click 'New Short' to create one!", "info");
        }
      });
    }

    if (btnCloseJobModal) {
      btnCloseJobModal.addEventListener("click", closeJobModal);
    }

    if (jobModal) {
      jobModal.addEventListener("click", (e) => {
        if (e.target === jobModal) closeJobModal();
      });
    }

    if (btnRetryJob) {
      btnRetryJob.addEventListener("click", async () => {
        if (!state.selectedJob) return;
        const jobId = state.selectedJob.job_id;
        try {
          btnRetryJob.disabled = true;
          btnRetryJob.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Starting...</span>`;
          if (window.lucide) lucide.createIcons();
          
          const res = await fetch(`/api/video/retry/${jobId}`, { method: "POST" });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || "Retry failed");
          
          showToast(`Restarted render for ${jobId}`, "success");
          state.selectedJob.status = "processing";
          state.selectedJob.progress_pct = 10;
          state.selectedJob.current_step = "Retrying render pipeline...";
          updateJobModalUI(state.selectedJob);
          
          startJobPolling(jobId, state.selectedJob.topic || "COSMOS Short");
          fetchJobs();
          fetchActivePipeline();
        } catch (err) {
          showToast("Retry failed: " + err.message, "danger");
        } finally {
          btnRetryJob.disabled = false;
          btnRetryJob.innerHTML = `<i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i><span>Retry Render Now</span>`;
          if (window.lucide) lucide.createIcons();
        }
      });
    }

    if (btnDeleteJob) {
      btnDeleteJob.addEventListener("click", async () => {
        if (!state.selectedJob) return;
        const jobId = state.selectedJob.job_id;
        if (!confirm(`Dismiss and remove record for ${jobId}?`)) return;
        try {
          const res = await fetch(`/api/video/job/${jobId}`, { method: "DELETE" });
          if (!res.ok) throw new Error("Delete failed");
          showToast(`Job ${jobId} removed`, "info");
          closeJobModal();
          fetchJobs();
          fetchActivePipeline();
        } catch (err) {
          showToast("Failed to remove job: " + err.message, "danger");
        }
      });
    }

    if (btnJobLoadPreview) {
      btnJobLoadPreview.addEventListener("click", () => {
        if (!state.selectedJob) return;
        closeJobModal();
        switchView("video");
        loadVideoPreview(state.selectedJob);
      });
    }

    if (btnJobSchedule) {
      btnJobSchedule.addEventListener("click", () => {
        if (!state.selectedJob) return;
        const targetJob = state.selectedJob;
        closeJobModal();
        loadVideoPreview(targetJob);
        switchView("schedule");
        const openSchedBtn = document.getElementById("btn-open-schedule-modal");
        if (openSchedBtn) openSchedBtn.click();
      });
    }

    // Header poll
    fetchActivePipeline();
    setInterval(fetchActivePipeline, 3500);
  }

  function openJobModal(job) {
    if (!jobModal || !job) return;
    state.selectedJob = job;
    updateJobModalUI(job);
    jobModal.classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
  }

  function closeJobModal() {
    if (!jobModal) return;
    jobModal.classList.add("hidden");
    const modalVideo = document.getElementById("job-modal-video-player");
    if (modalVideo) {
      modalVideo.pause();
      modalVideo.src = "";
    }
  }

  function updateJobModalUI(job) {
    if (!job) return;
    state.selectedJob = job;

    const idEl = document.getElementById("job-modal-id");
    const titleEl = document.getElementById("job-modal-title");
    const badgeEl = document.getElementById("job-modal-status-badge");
    const stepTextEl = document.getElementById("job-modal-step-text");
    const pctTextEl = document.getElementById("job-modal-pct-text");
    const progressBar = document.getElementById("job-modal-progress-bar");
    const errorBox = document.getElementById("job-modal-error-box");
    const errorTitle = document.getElementById("job-modal-error-title");
    const errorDesc = document.getElementById("job-modal-error-desc");
    const videoBox = document.getElementById("job-modal-video-box");
    const videoPlayer = document.getElementById("job-modal-video-player");
    const retryBtn = document.getElementById("btn-retry-job");
    const previewBtn = document.getElementById("btn-job-load-preview");
    const schedBtn = document.getElementById("btn-job-schedule");

    if (idEl) idEl.textContent = job.job_id || "cosmos_job";
    if (titleEl) titleEl.textContent = job.topic || job.title || "COSMOS Short Pipeline";

    const pct = Number(job.progress_pct || 0);
    if (pctTextEl) pctTextEl.textContent = `${pct}%`;
    if (progressBar) progressBar.style.width = `${pct}%`;
    if (stepTextEl) stepTextEl.textContent = job.current_step || job.status || "Ready";

    const status = (job.status || "ready").toLowerCase();
    if (badgeEl) {
      if (status === "completed") {
        badgeEl.textContent = "COMPLETED";
        badgeEl.className = "px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
      } else if (status === "processing" || status === "queued") {
        badgeEl.textContent = "PROCESSING";
        badgeEl.className = "px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-violet-500/10 text-violet-400 border border-violet-500/30 animate-pulse";
      } else if (status === "interrupted") {
        badgeEl.textContent = "INTERRUPTED (SAFE RESUME)";
        badgeEl.className = "px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-amber-500/10 text-amber-300 border border-amber-500/30";
      } else {
        badgeEl.textContent = "FAILED";
        badgeEl.className = "px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-rose-500/10 text-rose-400 border border-rose-500/30";
      }
    }

    const stages = [
      { id: 1, minPct: 10, name: "Prompt & Concept" },
      { id: 2, minPct: 25, name: "Hindi Script & Segmentation" },
      { id: 3, minPct: 40, name: "EdgeTTS Voiceover" },
      { id: 4, minPct: 60, name: "HD Visual Media" },
      { id: 5, minPct: 75, name: "Dynamic Subtitles" },
      { id: 6, minPct: 90, name: "FFmpeg 1080x1920 MP4" },
      { id: 7, minPct: 100, name: "Viral Thumbnail & Schedule" }
    ];

    stages.forEach((st) => {
      const stepRow = document.getElementById(`pipe-step-${st.id}`);
      const stepNum = document.getElementById(`pipe-step-${st.id}-num`);
      const stepStatus = document.getElementById(`pipe-step-${st.id}-status`);
      if (!stepRow || !stepStatus) return;

      if (status === "completed" || pct >= st.minPct) {
        stepStatus.textContent = "✓ Completed";
        stepStatus.className = "text-[10px] px-2 py-0.5 rounded font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
        if (stepNum) stepNum.className = "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-emerald-500/20 text-emerald-400 font-mono";
      } else if (status === "processing") {
        const prevMin = st.id === 1 ? 0 : stages[st.id - 2].minPct;
        if (pct >= prevMin && pct < st.minPct) {
          stepStatus.textContent = "⚡ In Progress";
          stepStatus.className = "text-[10px] px-2 py-0.5 rounded font-medium bg-violet-500/20 text-violet-300 border border-violet-500/40 animate-pulse";
          if (stepNum) stepNum.className = "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-violet-500 text-white font-mono animate-pulse";
        } else {
          stepStatus.textContent = "Pending";
          stepStatus.className = "text-[10px] px-2 py-0.5 rounded font-medium bg-gray-800 text-gray-500";
          if (stepNum) stepNum.className = "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-gray-800 text-gray-500 font-mono";
        }
      } else if (status === "interrupted" || status === "failed") {
        const prevMin = st.id === 1 ? 0 : stages[st.id - 2].minPct;
        if (pct >= prevMin && pct < st.minPct) {
          stepStatus.textContent = status === "interrupted" ? "⚠️ Interrupted" : "✕ Failed";
          stepStatus.className = "text-[10px] px-2 py-0.5 rounded font-medium bg-amber-500/20 text-amber-300 border border-amber-500/40";
          if (stepNum) stepNum.className = "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-amber-500/20 text-amber-300 font-mono";
        } else {
          stepStatus.textContent = "Pending";
          stepStatus.className = "text-[10px] px-2 py-0.5 rounded font-medium bg-gray-800 text-gray-500";
          if (stepNum) stepNum.className = "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-gray-800 text-gray-500 font-mono";
        }
      } else {
        stepStatus.textContent = "Pending";
        stepStatus.className = "text-[10px] px-2 py-0.5 rounded font-medium bg-gray-800 text-gray-500";
        if (stepNum) stepNum.className = "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-gray-800 text-gray-500 font-mono";
      }
    });

    if (errorBox) {
      if (status === "interrupted") {
        errorBox.classList.remove("hidden");
        if (errorTitle) errorTitle.textContent = "Pipeline Paused (Server Restart / Interrupted)";
        if (errorDesc) errorDesc.textContent = "This render was halted before finishing when the background process stopped. All parameters and script texts are saved in SQLite. Click 'Retry Render Now' below to finish rendering with 1-click.";
      } else if (status === "failed") {
        errorBox.classList.remove("hidden");
        if (errorTitle) errorTitle.textContent = "Pipeline Error Detected";
        if (errorDesc) errorDesc.textContent = job.error_message || "An error occurred during video rendering. Click 'Retry Render Now' to re-attempt.";
      } else {
        errorBox.classList.add("hidden");
      }
    }

    if (retryBtn) {
      if (status === "interrupted" || status === "failed") {
        retryBtn.classList.remove("hidden");
      } else {
        retryBtn.classList.add("hidden");
      }
    }

    if (job.video_path) {
      if (videoBox) videoBox.classList.remove("hidden");
      if (videoPlayer) {
        videoPlayer.src = `/api/video/stream/${job.job_id}`;
      }
      if (previewBtn) previewBtn.classList.remove("hidden");
      if (schedBtn) schedBtn.classList.remove("hidden");
    } else {
      if (videoBox) videoBox.classList.add("hidden");
      if (previewBtn) previewBtn.classList.add("hidden");
      if (schedBtn) schedBtn.classList.add("hidden");
    }
  }

  async function fetchActivePipeline() {
    try {
      const res = await fetch("/api/video/active");
      if (!res.ok) return;
      const data = await res.json();
      state.activePipelineJob = data.active_job || data.latest_completed || (state.jobs && state.jobs[0]);

      const pulseEl = document.getElementById("pipeline-status-pulse");
      const pingEl = document.getElementById("pipeline-status-ping");
      const labelEl = document.getElementById("pipeline-status-label");
      const pctEl = document.getElementById("pipeline-status-pct");

      if (data.active_job) {
        const j = data.active_job;
        if (pulseEl) pulseEl.className = "w-2.5 h-2.5 rounded-full bg-violet-400 inline-block";
        if (pingEl) pingEl.className = "absolute w-2.5 h-2.5 rounded-full bg-violet-400 animate-ping opacity-75";
        if (labelEl) {
          const step = j.current_step || "Rendering Short...";
          labelEl.textContent = step.length > 25 ? step.substring(0, 23) + "..." : step;
        }
        if (pctEl) {
          pctEl.textContent = `${j.progress_pct || 0}%`;
          pctEl.className = "text-[10px] px-1.5 py-0.5 rounded font-mono font-bold bg-violet-950 text-violet-300 border border-violet-700/50";
        }

        if (state.selectedJob && state.selectedJob.job_id === j.job_id && jobModal && !jobModal.classList.contains("hidden")) {
          updateJobModalUI(j);
        }
      } else {
        const hasInterrupted = state.jobs && state.jobs.some(x => x.status === "interrupted");
        if (hasInterrupted) {
          if (pulseEl) pulseEl.className = "w-2.5 h-2.5 rounded-full bg-amber-400 inline-block";
          if (pingEl) pingEl.className = "hidden absolute w-2.5 h-2.5 rounded-full";
          if (labelEl) labelEl.textContent = "Render Interrupted";
          if (pctEl) {
            pctEl.textContent = "Retry";
            pctEl.className = "text-[10px] px-1.5 py-0.5 rounded font-mono font-bold bg-amber-950 text-amber-300 border border-amber-700/50";
          }
        } else {
          if (pulseEl) pulseEl.className = "w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block";
          if (pingEl) pingEl.className = "hidden absolute w-2.5 h-2.5 rounded-full";
          if (labelEl) labelEl.textContent = "Pipeline Ready";
          if (pctEl) {
            pctEl.textContent = "Ready";
            pctEl.className = "text-[10px] px-1.5 py-0.5 rounded font-mono font-bold bg-gray-800 text-gray-300 border border-gray-700";
          }
        }
      }
    } catch (e) {
      console.warn("Active pipeline fetch error:", e);
    }
  }

  // ----------------------------------------------------
  // CALENDAR & SAFE PUBLISHING
  // ----------------------------------------------------
  async function fetchCalendarEvents() {
    try {
      const res = await fetch("/api/calendar/events");
      const data = await res.json();
      renderCalendarEvents(data.events || []);
    } catch (e) {
      console.warn("Calendar load error:", e);
    }
  }

  function renderCalendarEvents(events) {
    const container = document.getElementById("calendar-timeline-container");
    if (!container) return;

    if (!events || events.length === 0) {
      container.innerHTML = `
        <div class="p-6 text-center text-gray-500 text-xs">
          <i data-lucide="calendar" class="w-8 h-8 mx-auto mb-2 text-gray-600"></i>
          <p>No upcoming scheduled videos. Plan a release using the button above.</p>
        </div>
      `;
      if (window.lucide) lucide.createIcons();
      return;
    }

    container.innerHTML = events.map(ev => `
      <div class="p-4 rounded-xl bg-gray-900 border border-gray-800 flex items-center justify-between">
        <div class="space-y-1">
          <p class="font-bold text-sm text-white">${ev.title}</p>
          <p class="text-xs text-gray-400">Scheduled: ${ev.scheduled_for} | Privacy: <strong class="text-violet-400 uppercase">${ev.privacy_status}</strong></p>
        </div>
        <span class="px-2.5 py-1 rounded-full text-xs font-semibold ${ev.upload_status === 'uploaded' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}">
          ${ev.upload_status.toUpperCase()}
        </span>
      </div>
    `).join("");
    if (window.lucide) lucide.createIcons();
  }

  // Quick Private Upload Button
  const btnQuickUploadPrivate = document.getElementById("btn-quick-upload-private");
  if (btnQuickUploadPrivate) {
    btnQuickUploadPrivate.addEventListener("click", async () => {
      if (!state.currentVideoPath) {
        showToast("No generated video selected to upload.", "warning");
        return;
      }

      showToast("Starting private test upload to COSMOS VIRAL...", "info");
      try {
        const res = await fetch("/api/calendar/upload", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            video_path: state.currentVideoPath,
            thumbnail_path: state.currentThumbnailPath,
            title: state.currentTitle || "COSMOS Short",
            privacy_status: "private"
          })
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Upload failed");
        }

        const data = await res.json();
        showToast(`Uploaded successfully as PRIVATE! ID: ${data.video_id}`, "success");
      } catch (e) {
        showToast("Upload error: " + e.message, "danger");
      }
    });
  }

  // ----------------------------------------------------
  // MONETIZATION & OPTIMAL TIMES
  // ----------------------------------------------------
  async function fetchMonetization() {
    try {
      const res = await fetch("/api/analytics/monetization");
      const data = await res.json();

      const shorts = data.shorts_views || {};
      const subs = data.subscribers || {};

      const shortsViewsEl = document.getElementById("ypp-shorts-views");
      if (shortsViewsEl) shortsViewsEl.textContent = (shorts.current || 0).toLocaleString();
      const shortsPctEl = document.getElementById("ypp-shorts-pct");
      if (shortsPctEl) shortsPctEl.textContent = `${shorts.progress_pct || 0}% Reached`;
      const shortsRemEl = document.getElementById("ypp-shorts-remain");
      if (shortsRemEl) shortsRemEl.textContent = `${(shorts.remaining || 0).toLocaleString()} views needed`;
      const shortsBarEl = document.getElementById("ypp-shorts-bar");
      if (shortsBarEl) shortsBarEl.style.width = `${Math.max(0.5, shorts.progress_pct || 0)}%`;

      const subsCountEl = document.getElementById("ypp-subs-count");
      if (subsCountEl) subsCountEl.textContent = (subs.current || 0).toLocaleString();
      const subsPctEl = document.getElementById("ypp-subs-pct");
      if (subsPctEl) subsPctEl.textContent = `${subs.progress_pct || 0}% Reached`;
      const subsRemEl = document.getElementById("ypp-subs-remain");
      if (subsRemEl) subsRemEl.textContent = `${subs.remaining || 0} subscribers needed`;
      const subsBarEl = document.getElementById("ypp-subs-bar");
      if (subsBarEl) subsBarEl.style.width = `${Math.max(1, subs.progress_pct || 0)}%`;
    } catch (e) {
      console.warn("Monetization load error:", e);
    }
  }

  async function fetchBestPostingTimes() {
    const dom = document.getElementById("chart-posting-heatmap");
    if (!dom || !window.echarts) return;

    try {
      const res = await fetch("/api/analytics/best_time");
      const data = await res.json();

      if (window.chartPostingHeatmap) window.chartPostingHeatmap.dispose();
      window.chartPostingHeatmap = echarts.init(dom);

      const isDark = state.theme === "dark";
      const textColor = isDark ? "#9CA3AF" : "#4B5563";

      const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`);
      const days = data.days || ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

      const option = {
        backgroundColor: "transparent",
        tooltip: {
          position: "top",
          formatter: (params) => `Hour: ${hours[params.value[0]]}<br/>Engagement: ${params.value[2]}%`
        },
        grid: { height: "70%", top: "10%", left: "8%", right: "4%" },
        xAxis: {
          type: "category",
          data: hours,
          splitArea: { show: true },
          axisLabel: { color: textColor, fontSize: 10 }
        },
        yAxis: {
          type: "category",
          data: days,
          splitArea: { show: true },
          axisLabel: { color: textColor, fontSize: 11 }
        },
        visualMap: {
          min: 0,
          max: 100,
          calculable: true,
          orient: "horizontal",
          left: "center",
          bottom: "0%",
          inRange: {
            color: isDark 
              ? ["#111827", "#1E1B4B", "#6D28D9", "#8B5CF6", "#06B6D4"]
              : ["#F3F4F6", "#DDD6FE", "#A78BFA", "#7C3AED", "#0891B2"]
          },
          textStyle: { color: textColor, fontSize: 10 }
        },
        series: [
          {
            name: "Engagement Score",
            type: "heatmap",
            data: data.heatmap || [],
            label: { show: false },
            emphasis: {
              itemStyle: { shadowBlur: 10, shadowColor: "rgba(0, 0, 0, 0.5)" }
            }
          }
        ]
      };
      window.chartPostingHeatmap.setOption(option);
    } catch (e) {
      console.warn("Posting heatmap error:", e);
    }
  }

  // ----------------------------------------------------
  // EVENT LISTENERS & MODALS
  // ----------------------------------------------------
    // ----------------------------------------------------
  // MANUAL SCRIPT WRITING & VIDEO EDITING STYLE CONTROLLER
  // ----------------------------------------------------
  function setupManualScriptController() {
    const scriptInput = document.getElementById("studio-script-input");
    const titleInput = document.getElementById("studio-title-input");
    const styleInput = document.getElementById("studio-editing-style-prompt");
    const btnClearManual = document.getElementById("btn-clear-manual-script");

    // Clear to Write Manually Button
    if (btnClearManual) {
      btnClearManual.addEventListener("click", () => {
        if (scriptInput) scriptInput.value = "";
        if (titleInput) titleInput.value = "";
        if (styleInput) styleInput.value = "";
        
        const badge = document.getElementById("studio-duration-badge");
        if (badge) badge.textContent = "0 words (~0s)";

        const langIndicator = document.getElementById("script-lang-indicator");
        if (langIndicator) langIndicator.textContent = "✍️ Clean Slate (Write Your Manual Script)";

        const keywordsContainer = document.getElementById("studio-keywords-container");
        if (keywordsContainer) {
          keywordsContainer.innerHTML = `<span class="text-xs text-gray-500 italic">Sequential stock keywords will be generated from your script & editing style...</span>`;
        }

        // Clear active pill highlight
        document.querySelectorAll(".btn-topic-pill").forEach(p => p.classList.remove("topic-pill-active"));
        showToast("Editor cleared! Type your custom script & editing style prompt.", "info");
        if (scriptInput) scriptInput.focus();
      });
    }

    // Real-time typing listener: detects words, duration, and language
    if (scriptInput) {
      scriptInput.addEventListener("input", () => {
        updateScriptWordCountAndLanguage(scriptInput.value);
      });
    }

    // Style preset pills
    document.querySelectorAll(".btn-style-preset").forEach(btn => {
      btn.addEventListener("click", () => {
        const style = btn.getAttribute("data-style");
        if (styleInput && style) {
          styleInput.value = style;
          showToast("Applied editing style preset!", "info");
        }
      });
    });
  }

  function updateScriptWordCountAndLanguage(text) {
    const clean = (text || "").trim();
    const words = clean ? clean.split(/\s+/).filter(Boolean).length : 0;
    const durationSec = Math.max(0, Math.round(words / 2.5));
    const badge = document.getElementById("studio-duration-badge");
    if (badge) badge.textContent = `${words} words (~${durationSec}s)`;

    const langIndicator = document.getElementById("script-lang-indicator");
    const langSelect = document.getElementById("studio-script-lang");
    const voiceSelect = document.getElementById("studio-script-voice");

    if (words > 0) {
      const hasDevanagari = /[\u0900-\u097F]/.test(clean);
      if (hasDevanagari) {
        if (langIndicator) langIndicator.textContent = "🇮🇳 Hindi Script Detected (Madhur / Swara Voice)";
        if (langSelect && langSelect.value === "auto" && voiceSelect && voiceSelect.value === "auto") {
          voiceSelect.value = "hi-IN-MadhurNeural-Male";
        }
      } else {
        if (langIndicator) langIndicator.textContent = "🌐 English / Roman Script Detected (Christopher / Jenny Voice)";
        if (langSelect && langSelect.value === "auto" && voiceSelect && voiceSelect.value === "auto") {
          voiceSelect.value = "en-US-ChristopherNeural-Male";
        }
      }
    } else {
      if (langIndicator) langIndicator.textContent = "✍️ Manual Input Ready";
    }
  }

function setupEventListeners() {
    const syncBtn = document.getElementById("btn-sync-yt");
    if (syncBtn) {
      syncBtn.addEventListener("click", async () => {
        const icon = document.getElementById("sync-icon");
        if (icon) icon.classList.add("animate-spin");
        showToast("Syncing channel stats from YouTube API...", "info");

        try {
          const res = await fetch("/api/youtube/sync", { method: "POST" });
          const data = await res.json();
          if (res.ok) {
            showToast(data.message, "success");
            fetchYouTubeData();
            fetchMonetization();
          } else {
            showToast("Sync failed: " + data.detail, "danger");
          }
        } catch (e) {
          showToast("Sync error: " + e.message, "danger");
        } finally {
          if (icon) icon.classList.remove("animate-spin");
        }
      });
    }

    // Schedule Modal Handlers
    const openSchedBtn = document.getElementById("btn-open-schedule-modal");
    const btnQuickSched = document.getElementById("btn-quick-schedule");
    const schedModal = document.getElementById("schedule-modal");
    const closeSchedBtn = document.getElementById("btn-close-schedule-modal");
    const cancelSchedBtn = document.getElementById("btn-cancel-schedule-modal");
    const confirmSchedBtn = document.getElementById("btn-confirm-schedule");
    const btnApplyBestTime = document.getElementById("btn-apply-best-time");

    async function openScheduleModal() {
      if (!schedModal) return;

      // Ensure video path is populated
      if (!state.currentVideoPath && state.jobs && state.jobs.length > 0) {
        const completed = state.jobs.find(j => j.status === "completed" && j.video_path);
        if (completed) {
          loadVideoPreview(completed);
        }
      }

      if (!state.currentVideoPath) {
        showToast("Please generate or select a completed video first to schedule.", "warning");
        return;
      }

      const modalTitleEl = document.getElementById("schedule-modal-video-title");
      if (modalTitleEl) modalTitleEl.textContent = state.currentTitle || "COSMOS Short";

      // Fetch upcoming optimal peak release window (18:30 IST)
      try {
        const res = await fetch("/api/calendar/best_time_slot");
        const data = await res.json();
        
        const dtInput = document.getElementById("schedule-datetime");
        if (dtInput && data.target_local_iso) {
          dtInput.value = data.target_local_iso;
        }

        const bestTimeText = document.getElementById("modal-best-time-text");
        if (bestTimeText && data.label) {
          bestTimeText.textContent = data.label;
        }

        const applyLabel = document.getElementById("btn-apply-best-time-label");
        if (applyLabel && data.label) {
          applyLabel.textContent = `⚡ Set to Next Peak Window (${data.label})`;
        }
      } catch (e) {
        console.warn("Could not fetch optimal time:", e);
      }

      schedModal.classList.remove("hidden");
      if (window.lucide) lucide.createIcons();
    }

    if (btnQuickSched) {
      btnQuickSched.addEventListener("click", () => openScheduleModal());
    }
    if (openSchedBtn) {
      openSchedBtn.addEventListener("click", () => openScheduleModal());
    }
    if (closeSchedBtn && schedModal) {
      closeSchedBtn.addEventListener("click", () => schedModal.classList.add("hidden"));
    }
    if (cancelSchedBtn && schedModal) {
      cancelSchedBtn.addEventListener("click", () => schedModal.classList.add("hidden"));
    }

    // Apply Best Time button click
    if (btnApplyBestTime) {
      btnApplyBestTime.addEventListener("click", async () => {
        try {
          const res = await fetch("/api/calendar/best_time_slot");
          const data = await res.json();
          const dtInput = document.getElementById("schedule-datetime");
          if (dtInput && data.target_local_iso) {
            dtInput.value = data.target_local_iso;
            showToast(`Optimal release window set to ${data.label}!`, "success");
          }
        } catch (e) {
          showToast("Error calculating optimal slot: " + e.message, "danger");
        }
      });
    }

    // Confirm Schedule Button Click
    if (confirmSchedBtn) {
      confirmSchedBtn.addEventListener("click", async () => {
        const dt = document.getElementById("schedule-datetime")?.value;
        if (!dt) {
          showToast("Please choose or confirm a release date and time.", "warning");
          return;
        }

        if (!state.currentVideoPath) {
          showToast("No video file selected for scheduling.", "warning");
          return;
        }

        const schedMode = document.querySelector('input[name="sched_mode"]:checked')?.value || "youtube";
        const labelEl = document.getElementById("btn-confirm-schedule-label");

        if (schedMode === "youtube") {
          // Upload directly to YouTube with Scheduled RFC3339 publishAt
          if (labelEl) labelEl.textContent = "Uploading & Scheduling to YouTube...";
          confirmSchedBtn.disabled = true;
          showToast("Uploading video and setting YouTube schedule...", "info");

          try {
            // Convert local datetime to UTC RFC3339
            const localDate = new Date(dt);
            const utcRfc3339 = localDate.toISOString();

            const res = await fetch("/api/calendar/upload", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                video_path: state.currentVideoPath,
                thumbnail_path: state.currentThumbnailPath,
                title: state.currentTitle || "COSMOS Short",
                privacy_status: "private",
                publish_at: utcRfc3339
              })
            });

            if (!res.ok) {
              const err = await res.json();
              throw new Error(err.detail || "Upload scheduling failed.");
            }

            const result = await res.json();
            showToast(`Video successfully scheduled on YouTube for ${dt}!`, "success");
            schedModal.classList.add("hidden");
            fetchCalendarEvents();
          } catch (e) {
            showToast("Scheduling upload failed: " + e.message, "danger");
          } finally {
            if (labelEl) labelEl.textContent = "Confirm & Schedule Video";
            confirmSchedBtn.disabled = false;
          }
        } else {
          // Save in COSMOS Local Content Calendar
          try {
            await fetch("/api/calendar/schedule", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                video_path: state.currentVideoPath,
                title: state.currentTitle || "COSMOS Short",
                scheduled_for: dt,
                privacy_status: "private"
              })
            });
            showToast("Video scheduled in COSMOS Calendar!", "success");
            schedModal.classList.add("hidden");
            fetchCalendarEvents();
          } catch (e) {
            showToast("Schedule failed: " + e.message, "danger");
          }
        }
      });
    }
  }

  // ----------------------------------------------------
  // ALGORITHM & GROWTH DOCTOR CONTROLLER
  // ----------------------------------------------------
  async function fetchGrowthDiagnostics() {
    try {
      const res = await fetch("/api/growth/diagnostics");
      if (!res.ok) return;
      const data = await res.json();

      const stuckCountEl = document.getElementById("growth-stuck-count");
      const stuckPctEl = document.getElementById("growth-stuck-pct");
      if (stuckCountEl) stuckCountEl.textContent = data.stuck_videos_count || 0;
      if (stuckPctEl) stuckPctEl.textContent = `${data.stuck_percentage || 0}% of uploads`;

      const container = document.getElementById("stuck-videos-container");
      if (!container) return;

      if (!data.zero_view_videos || data.zero_view_videos.length === 0) {
        container.innerHTML = `<div class="p-4 text-center text-emerald-400 text-xs">🎉 No zero-view videos detected! All uploads have broken through.</div>`;
        return;
      }

      container.innerHTML = data.zero_view_videos.map(v => {
        const title = v.title || "Untitled";
        const thumb = v.thumbnail_url || "/static/images/thumb_placeholder.png";
        const views = v.view_count || 0;
        return `
          <div class="p-2.5 rounded-xl bg-gray-900/80 border border-gray-800 flex items-center justify-between gap-3 hover:border-gray-700 transition">
            <div class="flex items-center space-x-2.5 min-w-0">
              <img src="${thumb}" alt="thumb" class="w-9 h-12 rounded object-cover bg-gray-950 border border-gray-800 flex-shrink-0">
              <div class="min-w-0">
                <p class="text-xs font-semibold text-white truncate max-w-[200px]" title="${title}">${title}</p>
                <div class="flex items-center space-x-2 text-[10px] text-gray-400 mt-0.5">
                  <span class="text-rose-400 font-bold">${views} Views</span>
                  <span>•</span>
                  <span class="text-amber-400">Swiped Early</span>
                </div>
              </div>
            </div>
            <button class="btn-revive-hook btn-secondary text-[11px] px-2.5 py-1.5 flex-shrink-0 text-amber-300 hover:text-white border-amber-500/30 hover:border-amber-500" data-title="${encodeURIComponent(title)}">
              ⚡ Revive Hook
            </button>
          </div>
        `;
      }).join("");

      // Bind Revive Hook buttons
      container.querySelectorAll(".btn-revive-hook").forEach(btn => {
        btn.addEventListener("click", () => {
          const title = decodeURIComponent(btn.getAttribute("data-title"));
          const hookInput = document.getElementById("hook-input-title");
          const igInput = document.getElementById("ig-input-title");
          if (hookInput) hookInput.value = title;
          if (igInput) igInput.value = title;
          generateHooks(title);
          showToast(`Analyzing hook for: "${title.slice(0, 25)}..."`, "info");
        });
      });

    } catch (e) {
      console.warn("Could not fetch growth diagnostics:", e);
    }
  }

  async function generateHooks(title) {
    if (!title) return;
    const btn = document.getElementById("btn-generate-hooks");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="animate-spin inline-block mr-1">⚡</span> Generating...`;
    }

    try {
      const res = await fetch("/api/growth/revive_hook", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, language: "hindi" })
      });
      const data = await res.json();

      const curiosityEl = document.getElementById("hook-curiosity-text");
      const shockEl = document.getElementById("hook-shock-text");
      const whatifEl = document.getElementById("hook-whatif-text");
      const titleEl = document.getElementById("hook-title-text");
      const tagsContainer = document.getElementById("hook-tags-container");

      if (curiosityEl) curiosityEl.textContent = data.curiosity_hook || "";
      if (shockEl) shockEl.textContent = data.shock_hook || "";
      if (whatifEl) whatifEl.textContent = data.what_if_hook || "";
      if (titleEl) titleEl.textContent = data.optimized_title || title;

      if (tagsContainer && data.tags) {
        tagsContainer.innerHTML = data.tags.map(t => `
          <span class="px-2 py-0.5 rounded-md bg-gray-900 border border-gray-800 text-[10px] text-cyan-300 font-mono">${t}</span>
        `).join("");
      }

      showToast("Generated 3 viral hooks with Qwen 7B!", "success");
    } catch (e) {
      showToast("Hook generation failed: " + e.message, "danger");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="zap" class="w-3.5 h-3.5"></i><span>Generate Hooks</span>`;
        if (window.lucide) lucide.createIcons();
      }
    }
  }

  async function generateInstagramBundle(title) {
    if (!title) return;
    const btn = document.getElementById("btn-generate-ig-bundle");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="animate-spin inline-block mr-1">🔄</span> Generating...`;
    }

    try {
      const res = await fetch("/api/growth/instagram_bundle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, category: "Space & Universe", language: "hindi" })
      });
      const data = await res.json();

      const capEl = document.getElementById("ig-caption-text");
      const tagsEl = document.getElementById("ig-tags-text");
      const audioEl = document.getElementById("ig-audio-style");
      const timeEl = document.getElementById("ig-best-time");

      if (capEl) capEl.value = `${data.caption}\n\n${data.cta}`;
      if (tagsEl) tagsEl.value = data.hashtags || "";
      if (audioEl) audioEl.textContent = data.audio_recommendation || "Cinematic Dark Synth";
      if (timeEl) timeEl.textContent = data.best_time_to_post || "18:30 IST";

      showToast("Instagram Reels bundle generated!", "success");
    } catch (e) {
      showToast("Instagram bundle generation failed: " + e.message, "danger");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="share-2" class="w-3.5 h-3.5"></i><span>Generate Instagram Bundle</span>`;
        if (window.lucide) lucide.createIcons();
      }
    }
  }

  async function fetchMilestoneRoadmap() {
    try {
      const res = await fetch("/api/growth/milestone_roadmap");
      if (!res.ok) return;
      const data = await res.json();

      const subsCard = document.getElementById("growth-roadmap-subs");
      const viewsCard = document.getElementById("growth-roadmap-views");
      if (subsCard) subsCard.textContent = data.current_subs || 49;
      if (viewsCard) viewsCard.textContent = `${(data.current_views || 0).toLocaleString()} / 10M Views`;

      const curSubsEl = document.getElementById("roadmap-current-subs");
      const subsBarEl = document.getElementById("roadmap-subs-bar");
      const subsNeededEl = document.getElementById("roadmap-subs-needed");

      if (curSubsEl) curSubsEl.textContent = data.current_subs || 49;
      if (subsBarEl) {
        const pct = Math.min(100, Math.max(1, ((data.current_subs || 49) / 1000) * 100));
        subsBarEl.style.width = `${pct}%`;
      }
      if (subsNeededEl) subsNeededEl.textContent = `${data.remaining_subs} to go (~${data.daily_subs_needed}/day in 90d)`;

      const curViewsEl = document.getElementById("roadmap-current-views");
      const viewsBarEl = document.getElementById("roadmap-views-bar");
      const viewsNeededEl = document.getElementById("roadmap-views-needed");

      if (curViewsEl) curViewsEl.textContent = (data.current_views || 0).toLocaleString();
      if (viewsBarEl) {
        const pct = Math.min(100, Math.max(0.1, ((data.current_views || 0) / 10000000) * 100));
        viewsBarEl.style.width = `${pct}%`;
      }
      if (viewsNeededEl) viewsNeededEl.textContent = `${(data.remaining_views || 0).toLocaleString()} to go (~${(data.daily_views_needed || 0).toLocaleString()}/day)`;

    } catch (e) {
      console.warn("Could not fetch roadmap:", e);
    }
  }

  function setupGrowthEventListeners() {
    const scanBtn = document.getElementById("btn-scan-growth");
    if (scanBtn) {
      scanBtn.addEventListener("click", () => {
        fetchGrowthDiagnostics();
        fetchMilestoneRoadmap();
        showToast("Algorithm scan completed!", "success");
      });
    }

    const genHooksBtn = document.getElementById("btn-generate-hooks");
    if (genHooksBtn) {
      genHooksBtn.addEventListener("click", () => {
        const title = document.getElementById("hook-input-title")?.value?.trim();
        if (!title) {
          showToast("Please enter a video topic or title.", "warning");
          return;
        }
        generateHooks(title);
      });
    }

    const genIgBtn = document.getElementById("btn-generate-ig-bundle");
    if (genIgBtn) {
      genIgBtn.addEventListener("click", () => {
        const title = document.getElementById("ig-input-title")?.value?.trim() || document.getElementById("hook-input-title")?.value?.trim();
        if (!title) {
          showToast("Please enter a video title for the Instagram package.", "warning");
          return;
        }
        generateInstagramBundle(title);
      });
    }

    // Hook copy buttons
    document.querySelectorAll(".btn-copy-hook").forEach(btn => {
      btn.addEventListener("click", () => {
        const targetId = btn.getAttribute("data-target");
        const el = document.getElementById(targetId);
        if (el) {
          navigator.clipboard.writeText(el.textContent.trim()).then(() => {
            showToast("Copied to clipboard!", "success");
          });
        }
      });
    });

    const copyIgCapBtn = document.getElementById("btn-copy-ig-caption");
    if (copyIgCapBtn) {
      copyIgCapBtn.addEventListener("click", () => {
        const el = document.getElementById("ig-caption-text");
        if (el) {
          navigator.clipboard.writeText(el.value).then(() => {
            showToast("Instagram caption copied!", "success");
          });
        }
      });
    }

    const copyIgTagsBtn = document.getElementById("btn-copy-ig-tags");
    if (copyIgTagsBtn) {
      copyIgTagsBtn.addEventListener("click", () => {
        const el = document.getElementById("ig-tags-text");
        if (el) {
          navigator.clipboard.writeText(el.value).then(() => {
            showToast("Instagram hashtags copied!", "success");
          });
        }
      });
    }
  }

  // ----------------------------------------------------
  // DYNAMIC TAB LOGO & INACTIVE TAB RE-ENGAGEMENT ANIMATION
  // ----------------------------------------------------
  function setupTabVisibilityAnimation() {
    const originalTitle = "COSMOS GROWTH OS — YouTube Command Center";
    const normalFavicon = "/static/images/favicon.svg";
    const alertFavicon = "/static/images/favicon-alert.svg";
    const faviconEl = document.getElementById("app-favicon");

    let normalFaviconUri = normalFavicon;
    let alertFaviconUri = alertFavicon;

    // Preload both SVG favicons as memory Data URIs once (ZERO network requests & ZERO glitch during tab switching)
    Promise.all([
      fetch(normalFavicon).then(r => r.text()).catch(() => null),
      fetch(alertFavicon).then(r => r.text()).catch(() => null)
    ]).then(([s1, s2]) => {
      if (s1) normalFaviconUri = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(s1);
      if (s2) alertFaviconUri = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(s2);
    });

    const repeatingAlerts = [
      "🪐 (1) Hey! Come back to COSMOS...",
      "⚡ Your YouTube Shorts need you!",
      "🚀 Reach 1,000 Subs & Monetize!"
    ];

    let tabAnimInterval = null;
    let titleIndex = 0;
    let isAlertIcon = false;
    let restoreTimeout = null;

    function startInactiveAnimation() {
      if (tabAnimInterval) clearInterval(tabAnimInterval);
      if (restoreTimeout) clearTimeout(restoreTimeout);

      titleIndex = 0;
      isAlertIcon = false;

      tabAnimInterval = setInterval(() => {
        // 1. Cycle repeating dynamic titles smoothly
        document.title = repeatingAlerts[titleIndex % repeatingAlerts.length];
        titleIndex++;

        // 2. Animate favicon directly from memory without network hits
        if (faviconEl) {
          isAlertIcon = !isAlertIcon;
          faviconEl.href = isAlertIcon ? alertFaviconUri : normalFaviconUri;
        }
      }, 1400);
    }

    function stopInactiveAnimation() {
      if (tabAnimInterval) {
        clearInterval(tabAnimInterval);
        tabAnimInterval = null;
      }

      // Restore normal favicon immediately from memory
      if (faviconEl) {
        faviconEl.href = normalFaviconUri;
      }

      // Friendly welcoming title, then back to original
      document.title = "✨ Welcome back, Creator!";
      restoreTimeout = setTimeout(() => {
        document.title = originalTitle;
      }, 1400);
    }

    // Handle Page Visibility API (Chrome/Edge/Firefox)
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        startInactiveAnimation();
      } else {
        stopInactiveAnimation();
      }
    });

    // Fallback for Window Blur / Focus
    window.addEventListener("blur", () => {
      if (document.hidden) {
        startInactiveAnimation();
      }
    });

    window.addEventListener("focus", () => {
      stopInactiveAnimation();
    });
  }

  // ----------------------------------------------------
  // INITIAL APP BOOTSTRAP (Runs after all handlers and variables are fully initialized)
  // ----------------------------------------------------
  fetchHealth();
  fetchYouTubeData();
  fetchCuratedTopics();
  fetchCategories();
  fetchPromptTemplates();
  fetchJobs();
  fetchMonetization();
  fetchBestPostingTimes();
  fetchCalendarEvents();
  fetchGrowthDiagnostics();
  fetchMilestoneRoadmap();
  initPipelineTracker();

  setupEventListeners();
  setupGrowthEventListeners();
  setupWinningTopicListeners();
  setupManualScriptController();
  setupTabVisibilityAnimation();

  // Toast Notification System
  function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    const bg = type === "success" ? "bg-emerald-600" : (type === "danger" ? "bg-rose-600" : (type === "warning" ? "bg-amber-600" : "bg-violet-600"));

    toast.className = `p-3 rounded-xl text-white text-xs font-semibold shadow-xl flex items-center space-x-2 transition transform translate-y-2 opacity-0 ${bg}`;
    toast.innerHTML = `
      <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.remove("translate-y-2", "opacity-0");
    }, 10);

    setTimeout(() => {
      toast.classList.add("opacity-0");
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
});
