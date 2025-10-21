const BASE_URL = "http://localhost:8000"; // ← замени на продакшн-URL
const IS_DEV = !window.Telegram?.WebApp?.initData;
const initData = window.Telegram?.WebApp?.initData || "";

async function extractToken(initData) {
  if (IS_DEV) {
    console.warn("⚠️ DEV MODE: Using test token");
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."; // ← вставь свой токен
  }

  const res = await fetch(`${BASE_URL}/auth/telegram`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ init_data: initData })
  });
  const data = await res.json();
  return data.access_token;
}

async function fetchDailyROI(startDate, endDate, campaignId, costPerAction) {
  const token = await extractToken(initData);
  console.log("🔐 Полученный токен (ROI):", token); // ← временный лог

  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
    campaign_id: campaignId,
    cost_per_action: costPerAction
  });

  const res = await fetch(`${BASE_URL}/analytics/roi/daily?${params}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  const data = await res.json();
  renderTable(data);
  renderChart(data);
}

async function fetchRoiImage(startDate, endDate, campaignId, costPerAction) {
  const token = await extractToken(initData);
  console.log("🔐 Полученный токен (PNG):", token); // ← временный лог

  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
    campaign_id: campaignId,
    cost_per_action: costPerAction
  });

  const res = await fetch(`${BASE_URL}/analytics/roi/plot?${params}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  const blob = await res.blob();
  const imgUrl = URL.createObjectURL(blob);

  const imgElement = document.getElementById("roi-image");
  imgElement.src = imgUrl;

  const downloadBtn = document.getElementById("download-png");
  downloadBtn.onclick = () => {
    const a = document.createElement("a");
    a.href = imgUrl;
    a.download = "roi_graph.png";
    a.click();
  };
}

function renderTable(data) {
  const tbody = document.querySelector("#roi-table tbody");
  tbody.innerHTML = "";

  data.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.date}</td>
      <td>${row.actions}</td>
      <td>${row.reward}</td>
      <td>${row.roi_percent}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderChart(data) {
  const ctx = document.getElementById("roi-chart").getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: {
      labels: data.map(row => row.date),
      datasets: [{
        label: "ROI (%)",
        data: data.map(row => row.roi_percent),
        borderColor: "#4CAF50",
        backgroundColor: "rgba(76, 175, 80, 0.2)",
        fill: true
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

function applyFilters() {
  const startDate = document.getElementById("start-date").value;
  const endDate = document.getElementById("end-date").value;
  const campaignId = document.getElementById("campaign-id").value;
  const costPerAction = document.getElementById("cost-per-action").value;

  if (!startDate || !endDate || !campaignId || !costPerAction) {
    alert("Пожалуйста, заполните все поля фильтра.");
    return;
  }

  fetchDailyROI(startDate, endDate, campaignId, costPerAction);
  fetchRoiImage(startDate, endDate, campaignId, costPerAction);
}
