const BASE_URL = "http://localhost:8000";

// 🧭 Глобальные переменные для графиков
let roiChart = null;
let cpaChart = null;
let ctrChart = null;

// 🎯 Выбранные кампании (множественный выбор через чекбоксы dropdown)
let selectedCampaigns = [];

// 🟢 Активная кампания (по умолчанию null = все свернуты)
let activeCampaignId = null;

// 🟢 Состояние локальных контролов графиков
const chartControlsState = {
  roi: { log: false, norm: false, dual: false },
  cpa: { log: false, norm: false, dual: false },
  ctr: { log: false, norm: false, dual: false }
};

// 📝 Логгер
function logEvent(message) {
  console.log(`[LOG] ${new Date().toISOString()} ${message}`);
}

// === Режимы раскрытия графиков (expanded / fullscreen) ===
function setupChartExpandModes() {
  const container = document.querySelector('.report-container');
  const chartsPanel = container?.querySelector('.charts-panel');
  const tablePanel = container?.querySelector('.table-panel');
  if (!container || !chartsPanel || !tablePanel) return;

  const cards = chartsPanel.querySelectorAll('.chart-card');
  cards.forEach((card) => {
    const expandBtn = card.querySelector('.chart-btn--expand');
    const fullscreenBtn = card.querySelector('.chart-btn--fullscreen');
    const collapseBtn = card.querySelector('.chart-btn--collapse');

    // === Промежуточный режим ===
    expandBtn?.addEventListener('click', () => {
      cards.forEach((c) => {
        if (c !== card) c.classList.add('hidden');
      });
      tablePanel.classList.add('hidden');
      container.classList.add('mode-expanded');
      card.classList.add('active');
      const canvas = card.querySelector('canvas');
      if (canvas && canvas._chart) canvas._chart.resize();
    });

    // === Полноэкранный режим ===
    fullscreenBtn?.addEventListener('click', () => {
      cards.forEach((c) => {
        if (c !== card) c.classList.add('hidden');
      });
      tablePanel.classList.add('hidden');
      card.classList.add('fullscreen');
      const canvas = card.querySelector('canvas');
      if (canvas && canvas._chart) canvas._chart.resize();
    });

    // === Возврат в обычный режим ===
    collapseBtn?.addEventListener('click', () => {
      container.classList.remove('mode-expanded');
      card.classList.remove('active', 'fullscreen');
      tablePanel.classList.remove('hidden');
      const list = Array.from(cards);
      list.forEach((c, i) => {
        if (c !== card) {
          c.classList.remove('hidden');
          c.style.transitionDelay = `${0.2 + i * 0.2}s`;
        }
      });
      setTimeout(() => {
        list.forEach((c) => (c.style.transitionDelay = ''));
      }, 1200);
    });
  });
}

// 🔧 Синхронизация "воздуха" под графиком и таблицей
function syncBottomGap(chart, tablePanelEl) {
  const gap = chart.height - chart.chartArea.bottom;
  const chartsPanelBorderY = 2;
  const effectiveGap = Math.max(0, gap + chartsPanelBorderY);
  tablePanelEl.style.setProperty('--bottom-gap', `${effectiveGap}px`);
}

// 📦 Метки метрик
function getLabel(metric) {
  switch (metric) {
    case "roi": return "ROI %";
    case "cpa": return "CPA";
    case "ctr": return "CTR %";
    default: return metric.toUpperCase();
  }
}

// 📊 Получение выбранной метрики из dropdown
function getSelectedMetric() {
  const btn = document.querySelector("#metric-dropdown .dropdown-btn");
  return btn?.dataset?.value || "roi";
}

// 📐 Подсчёт колонок таблицы
function getTableColumnCount() {
  const theadRow = document.querySelector("#roi-table thead tr");
  return theadRow?.children.length || 6;
}

// === Применение фильтров (с опцией тихого режима) ===
function applyFilters({ silent = false } = {}) {
  logEvent("✅ Фильтры применены");

  const startDate = document.getElementById("start-date").value;
  const endDate = document.getElementById("end-date").value;
  const costPerAction = document.getElementById("cost-per-action").value;
  const campaignIds = selectedCampaigns.slice();
  const metricBtn = document.querySelector("#metric-dropdown .dropdown-btn");
  const metric = metricBtn?.dataset?.value || "roi";

  const required = [startDate, endDate, campaignIds.length, costPerAction];
  if (required.some(v => !v)) {
    if (!silent) {
      alert("⚠️ Заполните все поля перед отправкой.");
      ["start-date", "end-date", "cost-per-action"].forEach(id => {
        const el = document.getElementById(id);
        el.classList.toggle("error", !el.value);
      });
      const campaignBtn = document.querySelector("#campaign-dropdown .dropdown-btn");
      if (campaignBtn) campaignBtn.classList.toggle("error", campaignIds.length === 0);
    }
    return;
  }

  saveFilters();
  fetchDailyROI(startDate, endDate, campaignIds, costPerAction);
  logEvent("📤 Фильтры отправлены на сервер");
}

// === Запрос к API ===
async function fetchDailyROI(startDate, endDate, campaignIds, costPerAction) {
  const fetchOne = async (id) => {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      cost_per_action: costPerAction,
      campaign_id: id
    });
    const res = await fetch(`${BASE_URL}/analytics/roi/daily?${params}`);
    if (!res.ok) {
      logEvent(`❌ API вернул статус ${res.status} для кампании ${id}`);
      return [];
    }
    const json = await res.json();
    return Array.isArray(json) ? json.map(r => ({ ...r, campaign_id: r.campaign_id ?? String(id) })) : [];
  };

  const results = await Promise.all(campaignIds.map(fetchOne));
  const data = results.flat();

  if (!Array.isArray(data) || data.length === 0) {
    renderFallbackChart("roi-chart", "Нет данных для ROI");
    renderFallbackChart("cpa-chart", "Нет данных для CPA");
    renderFallbackChart("ctr-chart", "Нет данных для CTR");
    const tbody = document.querySelector("#roi-table tbody");
    const columnCount = getTableColumnCount();
    tbody.innerHTML = `<tr><td colspan="${columnCount}">⚠️ Нет данных по выбранным кампаниям</td></tr>`;
    document.getElementById("roi-summary").textContent = "⚠️ Нет данных для отчёта.";
    logEvent("📉 Нет данных — UI очищен");
    return;
  }

  logEvent(`📦 Получены данные (объединённо): ${JSON.stringify(data)}`);
  renderTable(data, parseFloat(costPerAction));
  renderAllCharts(data, parseFloat(costPerAction));
}

// === Фолбэк для графиков ===
function renderFallbackChart(canvasId, message) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");

  if (canvasId === "roi-chart" && roiChart) { roiChart.destroy(); roiChart = null; }
  if (canvasId === "cpa-chart" && cpaChart) { cpaChart.destroy(); cpaChart = null; }
  if (canvasId === "ctr-chart" && ctrChart) { ctrChart.destroy(); ctrChart = null; }

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = "16px sans-serif";
  ctx.fillStyle = "gray";
  ctx.textAlign = "center";
  ctx.fillText(message, canvas.width / 2, canvas.height / 2);

  logEvent(`📉 ${message}`);
}

// === Таблица ===
function renderTable(data, costPerAction) {
  const tbody = document.querySelector("#roi-table tbody");
  tbody.innerHTML = "";

  const grouped = {};
  data.forEach(row => {
    const key = row.campaign_id || "Без ID";
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(row);
  });

  Object.entries(grouped).forEach(([campaignId, rows], i) => {
    if (rows.length === 0) return;

    const columnCount = getTableColumnCount();
    const borderColor = `hsl(${i * 60}, 70%, 50%)`;
    const backgroundColor = `hsla(${i * 60}, 70%, 50%, 0.1)`;
    const borderWidth = 2;

    const header = document.createElement("tr");
    header.classList.add("campaign-header");
    header.dataset.campaignId = String(campaignId);
    header.innerHTML = `<td colspan="${columnCount}" style="text-align:center">
      <span class="legend-icon"
            style="border:${borderWidth}px solid ${borderColor};
                   background:${backgroundColor};"></span>
      Кампания ${campaignId} — ${getLabel(getSelectedMetric())}
    </td>`;
    tbody.appendChild(header);

    header.addEventListener("click", () => {
      const clickedId = header.dataset.campaignId;
      activeCampaignId = (activeCampaignId === clickedId) ? null : clickedId;

      tbody.querySelectorAll("tr.campaign-header").forEach(h => {
        const isActive = h.dataset.campaignId === activeCampaignId;
        h.classList.toggle("active", isActive);
      });

      tbody.querySelectorAll("tr:not(.campaign-header)").forEach(r => {
        const same = r.dataset.campaignId === activeCampaignId;
        r.style.display = activeCampaignId ? (same ? "" : "none") : "none";
      });

      logEvent(`📊 Кампания ${campaignId} ${activeCampaignId ? "раскрыта" : "свернута"}`);
    });

    rows.forEach(row => {
      const tr = document.createElement("tr");
      tr.dataset.campaignId = String(campaignId);

      const roi = parseFloat(row.roi_percent);
      const roiColor = roi >= 100 ? "#28a745" : "#dc3545";

      const cpa = row.actions > 0 ? row.reward / row.actions : 0;
      const cpr = row.reward > 0 ? row.actions / row.reward : 0;

      tr.innerHTML = `
        <td>${row.date}</td>
        <td>${row.actions}</td>
        <td>${row.reward.toFixed(2)}</td>
        <td style="color:${roiColor}">${roi.toFixed(1)}%</td>
        <td>${cpa.toFixed(2)}</td>   <!-- серый обычный текст -->
        <td>${cpr.toFixed(2)}</td>   <!-- серый обычный текст -->
      `;
      tbody.appendChild(tr);
    });
  });

  if (activeCampaignId) {
    const activeId = String(activeCampaignId);
    tbody.querySelectorAll("tr.campaign-header").forEach(h => {
      const isActive = h.dataset.campaignId === activeId;
      h.classList.toggle("active", isActive);
    });
    tbody.querySelectorAll("tr:not(.campaign-header)").forEach(r => {
      r.style.display = (r.dataset.campaignId === activeId) ? "" : "none";
    });
  } else {
    tbody.querySelectorAll("tr:not(.campaign-header)").forEach(r => {
      r.style.display = "none";
    });
  }

  const metric = getSelectedMetric();
  const summary = generateReport(data, costPerAction, metric);
  const roiText = document.getElementById("roi-text");
  roiText.value = summary;
  roiText.style.height = "auto";
  const scrollHeight = roiText.scrollHeight;
  roiText.style.height = scrollHeight > 0 ? scrollHeight + "px" : "6em";

  document.getElementById("metric-indicator").innerHTML =
    `<span class="icon metrics-icon"></span> Текущая метрика: ${getLabel(metric)}`;

  localStorage.setItem("roiReport", summary);
  logEvent("📋 Отчёт сгенерирован");
}

// === Управление раскрытием кампаний ===
function toggleCampaignRows(campaignId) {
  const tbody = document.querySelector("#roi-table tbody");
  if (!tbody) return;

  // Найдём заголовок и посчитаем, видны ли сейчас строки кампании
  let show = false;
  let header = null;
  let visibleCount = 0;

  tbody.querySelectorAll("tr").forEach(tr => {
    const text = tr.textContent || "";
    const isHeader = tr.classList.contains("campaign-header");

    if (isHeader && text.includes(`Кампания ${campaignId}`)) {
      show = true;
      header = tr;
      return;
    }
    if (show && !isHeader) {
      if (tr.style.display !== "none") visibleCount++;
    }
    if (isHeader && !text.includes(`Кампания ${campaignId}`)) {
      show = false;
    }
  });

  // Если эта кампания активна И её строки уже видимы → это пользовательский клик на свернуть
  if (activeCampaignId === campaignId && visibleCount > 0) {
    activeCampaignId = null;

    tbody.querySelectorAll("tr").forEach(tr => {
      if (!tr.classList.contains("campaign-header")) tr.style.display = "none";
      if (tr.classList.contains("campaign-header")) {
        tr.classList.remove("active");
        tr.querySelectorAll("td").forEach(td => td.removeAttribute("style"));
      }
    });
    return;
  }

  // Иначе (строки ещё скрыты или активна другая кампания) → раскрываем кампанию
  activeCampaignId = campaignId;

  // Сброс: скрыть строки и снять подсветку у всех заголовков
  tbody.querySelectorAll("tr").forEach(tr => {
    if (!tr.classList.contains("campaign-header")) tr.style.display = "none";
    if (tr.classList.contains("campaign-header")) {
      tr.classList.remove("active");
      tr.querySelectorAll("td").forEach(td => td.removeAttribute("style"));
    }
  });

  // Раскрыть только выбранную кампанию
  let open = false;
  header = null;
  tbody.querySelectorAll("tr").forEach(tr => {
    const text = tr.textContent || "";
    const isHeader = tr.classList.contains("campaign-header");

    if (isHeader && text.includes(`Кампания ${campaignId}`)) {
      open = true;
      header = tr;
      return;
    }
    if (open && !isHeader) tr.style.display = "";
    if (isHeader && !text.includes(`Кампания ${campaignId}`)) open = false;
  });

  // Подсветка заголовка выбранной кампании
  if (header) {
    header.classList.add("active");
    const tds = header.querySelectorAll("td");
    const table = document.querySelector("#roi-table");
    const styles = table ? getComputedStyle(table) : getComputedStyle(document.documentElement);
    const activeColor = styles.getPropertyValue("--active-color").trim() || "#d9d9d9";

    tds.forEach(td => {
      td.style.color = "#fff";
      td.style.backgroundColor = activeColor;
      td.style.borderRadius = "6px";
    });
  }
}

// === Генерация текстового отчёта ===
function generateReport(data, costPerAction, metric = "roi") {
  if (!Array.isArray(data) || data.length === 0 || costPerAction <= 0) {
    return "❌ Нет данных для отчёта.";
  }

  const grouped = {};
  data.forEach(row => {
    const key = row.campaign_id || "Без ID";
    if (!grouped[key]) {
      grouped[key] = { totalActions: 0, totalReward: 0, days: 0 };
    }
    grouped[key].totalActions += row.actions;
    grouped[key].totalReward += row.reward;
    grouped[key].days += 1;
  });

  let report = ``;
  Object.entries(grouped).forEach(([id, stats]) => {
    switch (metric) {
      case "cpa": {
        const cpa = stats.totalActions > 0 ? stats.totalReward / stats.totalActions : 0;
        report += `• Кампания ${id}: CPA = ${cpa.toFixed(2)} (${stats.totalActions} действий)\n`;
        break;
      }
      case "ctr": {
        const ctr = stats.days > 0 ? (stats.totalActions / stats.days) * 100 : 0;
        report += `• Кампания ${id}: CTR ≈ ${ctr.toFixed(1)}% (${stats.days} дней)\n`;
        break;
      }
      default: {
        const roi = stats.totalActions > 0 ? ((stats.totalReward / stats.totalActions) / costPerAction) * 100 : 0;
        report += `• Кампания ${id}: ${stats.totalActions} действий, Вознаграждение ${stats.totalReward.toFixed(2)}, Агрегированный ROI ≈ ${roi.toFixed(1)}%\n`;
      }
    }
  });

  return report;
}

// === Локальные контролы графика (логарифм, нормализация, dual axis) ===
function attachLocalChartControls(chartInstance, metricKey, cardEl) {
  const originalDatasets = chartInstance._originalDatasets; // всегда берём чистые данные

  const setLogScale = (enabled) => {
    chartInstance.options.scales.y = {
      type: enabled ? "logarithmic" : "linear",
      position: "left",
      beginAtZero: true
    };
  };

  const setNormalization = (enabled) => {
    chartInstance.data.datasets.forEach((ds, i) => {
      if (!enabled) {
        ds.data = originalDatasets[i].slice();
        return;
      }
      const base = originalDatasets[i];
      const max = Math.max(...base.filter(n => n != null));
      ds.data = base.map(v => (v == null ? null : (max > 0 ? v / max : 0)));
    });
  };

  const setDualAxis = (enabled) => {
    if (enabled) {
      chartInstance.options.scales.y = { type: "linear", position: "left", beginAtZero: true };
      chartInstance.options.scales.y2 = { type: "linear", position: "right", beginAtZero: true, grid: { drawOnChartArea: false } };
      chartInstance.data.datasets.forEach((ds, i) => {
        ds.yAxisID = (i % 2 === 0) ? "y" : "y2";
      });
    } else {
      chartInstance.options.scales.y = { type: "linear", position: "left", beginAtZero: true };
      delete chartInstance.options.scales.y2;
      chartInstance.data.datasets.forEach(ds => { ds.yAxisID = "y"; });
    }
  };

  // делегирование кликов
  cardEl.removeEventListener("click", cardEl._chartToggleHandler || (() => {}));
  cardEl._chartToggleHandler = (e) => {
    const btn = e.target.closest(".chart-toggle");
    if (!btn) return;
    const option = btn.dataset.option;
    const isActive = btn.classList.toggle("active");

    chartControlsState[metricKey][option] = isActive;

    if (option === "log") setLogScale(isActive);
    if (option === "norm") setNormalization(isActive);
    if (option === "dual") setDualAxis(isActive);

    chartInstance.update();
  };
  cardEl.addEventListener("click", cardEl._chartToggleHandler);

  // синхронизация кнопок при рендере
  const toggles = cardEl.querySelectorAll(".chart-toggle");
  toggles.forEach(toggle => {
    const option = toggle.dataset.option;
    toggle.classList.toggle("active", !!chartControlsState[metricKey][option]);
  });
}

// === Графики ===
function renderAllCharts(data, costPerAction) {
  renderMetricChart(data, "roi", "roi-chart", costPerAction);
  renderMetricChart(data, "cpa", "cpa-chart", costPerAction);
  renderMetricChart(data, "ctr", "ctr-chart", costPerAction);
}

function renderMetricChart(data, metric, canvasId, costPerAction) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");

  if (canvasId === "roi-chart" && roiChart) { roiChart.destroy(); roiChart = null; }
  if (canvasId === "cpa-chart" && cpaChart) { cpaChart.destroy(); cpaChart = null; }
  if (canvasId === "ctr-chart" && ctrChart) { ctrChart.destroy(); ctrChart = null; }

  const chartLabel = getLabel(metric);
  const allDates = [...new Set(data.map(r => r.date))].sort();

  const grouped = {};
  data.forEach(row => {
    const key = row.campaign_id || "Без ID";
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(row);
  });

  const datasets = Object.keys(grouped).map((id, i) => {
    const values = allDates.map(date => {
      const row = grouped[id].find(r => r.date === date);
      if (!row) return null;
      switch (metric) {
        case "cpa": return row.actions > 0 ? row.reward / row.actions : 0;
        case "ctr": return row.actions;
        default: return row.roi_percent;
      }
    });
    return {
      label: `Кампания ${id} — ${chartLabel}`,
      data: values,
      borderColor: `hsl(${i * 60}, 70%, 50%)`,
      backgroundColor: `hsla(${i * 60}, 70%, 50%, 0.1)`,
      borderWidth: 1,
      fill: true,
      tension: 0.3,
      spanGaps: true,
      yAxisID: "y"
    };
  });

  const chartInstance = new Chart(ctx, {
    type: "line",
    data: { labels: allDates, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { padding: 0 } },
        y: { beginAtZero: true, type: "linear", position: "left" }
      },
      animation: false
    }
  });

  canvas._chart = chartInstance;
  chartInstance._originalDatasets = chartInstance.data.datasets.map(ds => ds.data.slice()); // сохраняем оригинал

  // применяем сохранённые настройки
  const state = chartControlsState[metric];
  if (state.log) chartInstance.options.scales.y.type = "logarithmic";
  if (state.norm) {
    chartInstance.data.datasets.forEach((ds, i) => {
      const base = chartInstance._originalDatasets[i];
      const max = Math.max(...base.filter(n => n != null));
      ds.data = base.map(v => (v == null ? null : (max > 0 ? v / max : 0)));
    });
  }
  if (state.dual) {
    chartInstance.options.scales.y2 = { type: "linear", position: "right", beginAtZero: true, grid: { drawOnChartArea: false } };
    chartInstance.data.datasets.forEach((ds, i) => {
      ds.yAxisID = (i % 2 === 0) ? "y" : "y2";
    });
  }
  chartInstance.update();

  const cardEl = canvas.closest(".chart-card");
  const metricKey = cardEl?.dataset?.chart;
  if (cardEl && metricKey) {
    attachLocalChartControls(chartInstance, metricKey, cardEl);
  }

  if (canvasId === "ctr-chart") {
    const tablePanelEl = document.querySelector(".table-panel");
    if (tablePanelEl) {
      syncBottomGap(chartInstance, tablePanelEl);
      chartInstance.options.onResize = () => syncBottomGap(chartInstance, tablePanelEl);
    }
  }

  if (canvasId === "roi-chart") roiChart = chartInstance;
  if (canvasId === "cpa-chart") cpaChart = chartInstance;
  if (canvasId === "ctr-chart") ctrChart = chartInstance;

  logEvent(`📈 График ${metric.toUpperCase()} построен`);
}

// === Сохранение фильтров ===
function saveFilters() {
  const start = document.getElementById('start-date').value;
  const end = document.getElementById('end-date').value;
  const cpa = document.getElementById('cost-per-action').value;
  const campaigns = selectedCampaigns.slice();
  const metricBtn = document.querySelector("#metric-dropdown .dropdown-btn");
  const metric = metricBtn?.dataset?.value || "roi";

  const filters = { start, end, campaigns, cpa, metric };
  localStorage.setItem('filters', JSON.stringify(filters));
}

// === Восстановление фильтров ===
function restoreFilters() {
  const saved = localStorage.getItem('filters');
  if (!saved) return;

  const filters = JSON.parse(saved);
  document.getElementById('start-date').value = filters.start || "";
  document.getElementById('end-date').value = filters.end || "";
  document.getElementById('cost-per-action').value = filters.cpa || "";

  selectedCampaigns = [];
  document.querySelectorAll("#campaign-dropdown .campaign-toggle").forEach(btn => {
    btn.classList.remove("active");
  });

  if (Array.isArray(filters.campaigns)) {
    selectedCampaigns = filters.campaigns.slice();
    document.querySelectorAll("#campaign-dropdown .campaign-toggle").forEach(btn => {
      if (selectedCampaigns.includes(btn.dataset.value)) {
        btn.classList.add("active");
      }
    });
  }

  const campBtn = document.querySelector("#campaign-dropdown .dropdown-btn");
  if (campBtn) {
    campBtn.textContent = selectedCampaigns.length > 0
      ? `Выбрано: ${selectedCampaigns.length} ▾`
      : "Выбрать кампании ▾";
  }

  const metricBtn = document.querySelector("#metric-dropdown .dropdown-btn");
  const metricItem = document.querySelector(
    `#metric-dropdown .dropdown-menu li[data-value='${filters.metric || "roi"}']`
  );
  if (metricBtn && metricItem) {
    metricBtn.textContent = metricItem.textContent + " ▾";
    metricBtn.dataset.value = filters.metric || "roi";
  }
}

// === Очистка фильтров ===
function clearFilters() {
  ["start-date", "end-date", "cost-per-action"].forEach(id => {
    document.getElementById(id).value = "";
  });

  selectedCampaigns = [];
  document.querySelectorAll("#campaign-dropdown .campaign-toggle").forEach(btn => {
    btn.classList.remove("active");
  });
  const campBtn = document.querySelector("#campaign-dropdown .dropdown-btn");
  if (campBtn) campBtn.textContent = "Выбрать кампании ▾";

  const metricBtn = document.querySelector("#metric-dropdown .dropdown-btn");
  const defaultMetricItem = document.querySelector("#metric-dropdown .dropdown-menu li[data-value='roi']");
  if (metricBtn && defaultMetricItem) {
    metricBtn.textContent = defaultMetricItem.textContent + " ▾";
    metricBtn.dataset.value = "roi";
  }

  localStorage.removeItem("filters");
  localStorage.removeItem("roiReport");

  document.getElementById("roi-table").querySelector("tbody").innerHTML = "";
  document.getElementById("roi-summary").textContent = "";
  document.getElementById("metric-indicator").textContent = "📊 Текущая метрика: —";

  ["roi-chart", "cpa-chart", "ctr-chart"].forEach(id => {
    const canvas = document.getElementById(id);
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  });

  showToast("🧹 Фильтры и отчёт очищены");
  logEvent("🧹 Пользователь очистил фильтры");
}

// === Вспомогательные утилиты ===
function showToast(message = "✅ PNG сохранён") {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2000);
}

function applyTheme(isDark) {
  document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
  localStorage.setItem("theme", isDark ? "dark" : "light");
}

// === Dropdown-компоненты ===
document.addEventListener("click", (e) => {
  document.querySelectorAll(".dropdown.open").forEach(dd => {
    if (!dd.contains(e.target)) dd.classList.remove("open");
  });

  if (e.target.classList.contains("dropdown-btn")) {
    const dropdown = e.target.closest(".dropdown");
    dropdown.classList.toggle("open");
  }

  if (e.target.closest("#campaign-dropdown .campaign-toggle")) {
    const btnEl = e.target.closest(".campaign-toggle");
    const value = btnEl.dataset.value;
    const isActive = btnEl.classList.toggle("active");

    if (isActive) {
      selectedCampaigns.push(value);
    } else {
      selectedCampaigns = selectedCampaigns.filter(id => id !== value);
    }

    const campBtn = document.querySelector("#campaign-dropdown .dropdown-btn");
    campBtn.textContent = selectedCampaigns.length > 0
      ? `Выбрано: ${selectedCampaigns.length} ▾`
      : "Выбрать кампании ▾";

    logEvent(`🎯 Выбраны кампании: ${selectedCampaigns.join(", ")}`);
  }

  if (e.target.closest("#metric-dropdown .dropdown-menu li")) {
    const li = e.target.closest("li");
    const btn = document.querySelector("#metric-dropdown .dropdown-btn");
    btn.textContent = li.textContent + " ▾";
    btn.dataset.value = li.dataset.value;
    li.closest(".dropdown").classList.remove("open");
    logEvent(`📊 Выбрана метрика: ${li.dataset.value}`);
  }
});

// === Автообновление фильтров ===
function startAutoRefresh(intervalMs = 30000) {
  setInterval(() => {
    logEvent("🔄 Автообновление фильтров");
    applyFilters({ silent: true });
  }, intervalMs);
}

// === Инициализация ===
window.addEventListener('DOMContentLoaded', () => {
  restoreFilters();

  const savedTheme = localStorage.getItem("theme");
  const isDark = savedTheme === "dark";

  const themeSwitch = document.getElementById("theme-switch");
  if (themeSwitch) {
    themeSwitch.addEventListener("click", () => {
      const root = document.documentElement;
      const currentTheme = root.getAttribute("data-theme");
      const newTheme = currentTheme === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", newTheme);
      localStorage.setItem("theme", newTheme);
    });
  }

  applyTheme(isDark);

  const fpStart = flatpickr("#start-date", { dateFormat: "Y-m-d", allowInput: false, locale: "ru" });
  const fpEnd = flatpickr("#end-date", { dateFormat: "Y-m-d", allowInput: false, locale: "ru" });

  document.querySelectorAll(".input-with-icon").forEach(group => {
    const input = group.querySelector("input");
    const iconBtn = group.querySelector(".calendar-wrapper");
    if (input && iconBtn) {
      iconBtn.addEventListener("click", () => {
        if (input._flatpickr) input._flatpickr.open();
      });
    }
  });

  applyFilters();
  startAutoRefresh(30000);

  const showBtn = document.getElementById('show-btn');
  const clearBtn = document.getElementById('clear-btn');
  const downloadChartPngBtn = document.getElementById("download-chart-png");
  const downloadMarkdownBtn = document.getElementById("download-markdown");

  document.querySelector(".spinner-icons .up").addEventListener("click", () => {
    const input = document.getElementById("cost-per-action");
    input.stepUp();
  });

  document.querySelector(".spinner-icons .down").addEventListener("click", () => {
    const input = document.getElementById("cost-per-action");
    input.stepDown();
  });

  if (showBtn) {
    showBtn.addEventListener('click', () => {
      saveFilters();
      applyFilters();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      localStorage.removeItem('filters');
      document.getElementById('filter-form').reset();
      clearFilters();
    });
  }

  if (downloadChartPngBtn) {
    downloadChartPngBtn.addEventListener("click", () => {
      const canvas = document.getElementById("roi-chart");
      const link = document.createElement("a");
      link.href = canvas.toDataURL("image/png");
      link.download = "roi-chart.png";
      link.click();
      showToast("✅ PNG сохранён");
      logEvent("📥 PNG скачан пользователем");
    });
  }

  if (downloadMarkdownBtn) {
    downloadMarkdownBtn.addEventListener("click", () => {
      const content = document.getElementById("roi-summary").textContent;
      const blob = new Blob([content], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "roi-report.md";
      link.click();
      logEvent("📄 Markdown-отчёт скачан");
    });
  }

  const exportDropdown = document.querySelector(".export-dropdown");
  const exportBtn = exportDropdown?.querySelector(".export-btn");

  if (exportDropdown && exportBtn) {
    exportBtn.addEventListener("click", () => {
      exportDropdown.classList.toggle("open");
    });

    document.addEventListener("click", (e) => {
      if (!exportDropdown.contains(e.target)) {
        exportDropdown.classList.remove("open");
      }
    });

    document.getElementById("export-excel").addEventListener("click", () => {
      const table = document.getElementById("roi-table");
      if (!table) {
        showToast("⚠️ Нет данных для экспорта");
        return;
      }
      const wb = XLSX.utils.table_to_book(table, { sheet: "ROI Report" });
      XLSX.writeFile(wb, "roi-report.xlsx");
      showToast("📊 Excel сохранён");
      logEvent("📊 Пользователь выгрузил Excel");
      exportDropdown.classList.remove("open");
    });

    /// 📄 Экспорт PDF (синхронизирован с Excel и Markdown, без кракозябр)
const API_BASE_URL = "http://127.0.0.1:8000"; // dev
// const API_BASE_URL = window.location.origin; // prod

document.getElementById("export-pdf").addEventListener("click", async () => {
  const summary = document.getElementById("roi-summary").textContent;

  const table = document.getElementById("roi-table");
  const rows = Array.from(table.querySelectorAll("tr")).map(tr =>
    Array.from(tr.querySelectorAll("td, th")).map(td => td.textContent)
  );

  const payload = encodeURIComponent(JSON.stringify(rows));
  const summaryEncoded = encodeURIComponent(summary);

  const response = await fetch(`${API_BASE_URL}/export/pdf`, {
  method: "POST",
  headers: { "Content-Type": "application/json; charset=utf-8" },
  body: JSON.stringify({
    summary,
    rows: rows.map(r => ({ name: r[0], roi: r[1] }))
  })
});

if (!response.ok) {
  showToast("⚠️ Ошибка при формировании PDF");
  return;
}

const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const link = document.createElement("a");
link.href = url;
link.download = "roi-report.pdf";
link.click();
window.URL.revokeObjectURL(url);

  showToast("📄 PDF сформирован из актуальных данных");
  logEvent("📄 Пользователь выгрузил PDF отчёт");
  exportDropdown.classList.remove("open");
});

    document.getElementById("export-md").addEventListener("click", () => {
      const content = document.getElementById("roi-summary").textContent;
      if (!content) {
        showToast("⚠️ Отчёт пуст — примените фильтры");
        return;
      }
      const blob = new Blob([content], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "roi-report.md";
      link.click();
      showToast("📝 Markdown сохранён");
      logEvent("📝 Пользователь выгрузил Markdown‑отчёт");
      exportDropdown.classList.remove("open");
    });
  }

  // 🌀 Анимация появления графиков
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) entry.target.classList.add("visible");
    });
  }, { threshold: 0.1 });

  ["roi-chart", "cpa-chart", "ctr-chart"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.add("fade-in");
      observer.observe(el);
    }
  });

  // 🔹 Вызов новой функции для управления режимами графиков
  setupChartExpandModes();

  logEvent("📦 Инициализация завершена: фильтры/тема/обработчики установлены");
});










