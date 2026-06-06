const input = document.getElementById("imageInput");
const uploadBtn = document.getElementById("uploadBtn");
const canvas = document.getElementById("imageCanvas");
const ctx = canvas.getContext("2d");
const homeView = document.getElementById("homeView");
const recipeDetailView = document.getElementById("recipeDetailView");
const modal = document.getElementById("modal");
const modalBackdrop = document.getElementById("modalBackdrop");
const modalTitle = document.getElementById("modalTitle");
const modalContent = document.getElementById("modalContent");
const tipsBtn = document.getElementById("tipsBtn");
const recipeBtn = document.getElementById("recipeBtn");
const confirmRecipeBtn = document.getElementById("confirmRecipeBtn");
const recipeSection = document.getElementById("recipeSection");
const closeModal = document.getElementById("closeModal");
const statusPill = document.getElementById("statusPill");
const canvasHint = document.getElementById("canvasHint");
const authToggleBtn = document.getElementById("authToggleBtn");

const savedRecipeList = document.getElementById("savedRecipeList");
const savedRecipeCount = document.getElementById("savedRecipeCount");
const savedRecipeEmpty = document.getElementById("savedRecipeEmpty");

const backToHomeBtn = document.getElementById("backToHomeBtn");
const detailRecipeTitle = document.getElementById("detailRecipeTitle");
const detailRecipeMeta = document.getElementById("detailRecipeMeta");
const detailChecklist = document.getElementById("detailChecklist");
const detailSteps = document.getElementById("detailSteps");

const LEGACY_STORAGE_KEY = "fruitgrade.savedRecipes.v1";
const LOCAL_RECIPES_KEY = "fruitgrade.savedRecipes.local.v2";
const SESSION_TOKEN_KEY = "fruitgrade.sessionToken.v1";
const SESSION_USER_KEY = "fruitgrade.sessionUser.v1";

const authPanel = document.getElementById("authPanel");
const loginView = document.getElementById("loginView");
const signupView = document.getElementById("signupView");
const authStatus = document.getElementById("authStatus");
const authUserLabel = document.getElementById("authUserLabel");
const authMessage = document.getElementById("authMessage");
const openSignupBtn = document.getElementById("openSignupBtn");
const openLoginBtn = document.getElementById("openLoginBtn");
const signupForm = document.getElementById("signupForm");
const loginForm = document.getElementById("loginForm");
const cameraInput = document.getElementById("cameraInput");
const fabContainer = document.getElementById("fabContainer");
const fabMain = document.getElementById("fabMain");
const fabActions = document.getElementById("fabActions");
const fabCamera = document.getElementById("fabCamera");
const fabFolder = document.getElementById("fabFolder");
const signupUsername = document.getElementById("signupUsername");
const signupPassword = document.getElementById("signupPassword");
const loginUsername = document.getElementById("loginUsername");
const loginPassword = document.getElementById("loginPassword");

const API_KEY_STORAGE_KEY = "fruitgrade.apiKey";

let currentUser = null;
let sessionToken = localStorage.getItem(SESSION_TOKEN_KEY) || "";
let localRecipes = [];
let currentRecipeMode = "local";
let activeSavedRecipeId = null;
let authPanelOpen = false;
let authViewMode = "login";

const tipsByCrop = {
  apple: "1. 표면의 색이 맑고 밝은 것<br>2. 꼭지가 마르지 않고 푸른색을 띠는 것",
  potato: "1. 표면에 흠집이 없고 매끄러우며 단단한 것<br>2. 껍질에 녹색 빛이 돌거나 싹이 난 건 피하기",
  cabbage: "1. 겉잎이 연한 녹색을 띠고 윤기가 난 것<br>2. 들었을 때 묵직하고 속이 꽉 찬 것<br>3. 밑동을 잘라낸 단면이 하얗고 마르지 않은 것",
  onion_white: "1. 껍질이 얇고 바스락거리는 것<br>2. 만졌을 때 단단하고 윗부분과 뿌리 부분이 단단하고 싹이 나지 않은 것",
  onion_red: "1. 껍질이 얇고 바스락거리는 것<br>2. 만졌을 때 단단하고 윗부분과 뿌리 부분이 단단하고 싹이 나지 않은 것",
  garlic: "1. 알이 굵고 끝이 뾰족하며, 만졌을 때 빈 곳 없이 단단하고 묵직한 것<br>2. 겉껍질이 얇게 잘 마르고 연한 붉은 빛을 띠는 것<br>3. 싹이 난 건 피하기",
  onjumilgam: "1. 껍질이 얇고 만졌을 때 단단하며 묵직한 것<br>2. 꼭지가 작고 연한 녹색을 띠는 것",
  hallabong: "1. 껍질이 얇고 크기에 비해 묵직한 것<br>2. 껍질이 주름진 건 피하고, 꼭지 부분이 싱싱한 것 택하기",
  persimmon: "1. 표면에 흠집이 없고 윤기가 난 것<br>2. 전체적으로 색이 고르게 짙은 주황색을 띠는 것<br>3. 꼭지가 과육에 딱 달라붙어 있는 것",
  pear: "1. 껍질이 팽팽하고 크기에 비해 묵직한 것<br>2. 표면이 맑은 황갈색인 것<br>3. 배꼽 부분이 넓고 깊게 쑥 들어간 것",
  chinese_cabbage: "1. 들었을 때 묵직하고 속이 꽉 찬 것<br>2. 겉잎은 짙은 녹색, 속잎은 뚜렷한 노란색인 것",
  radish: "1. 모양이 반듯하게 곧고 잔뿌리가 적은 것<br>2. 표면이 흠집 없이 매끄러운 것<br>3. 위와 아래의 경계가 뚜렷한 것",
};

const displayNameMap = {
  apple: "사과",
  potato: "감자",
  cabbage: "양배추",
  onion_white: "양파",
  onion_red: "적양파",
  garlic: "마늘",
  onjumilgam: "밀감",
  hallabong: "한라봉",
  persimmon: "감",
  pear: "배",
  chinese_cabbage: "배추",
  radish: "무",
};

const recommendedDailyMap = {
  apple: "1",
  potato: "1-2",
  cabbage: "0.25",
  onion_white: "0.5",
  onion_red: "0.5",
  garlic: "3",
  onjumilgam: "1~2",
  hallabong: "1",
  persimmon: "1",
  pear: "0.5",
  chinese_cabbage: "0.1",
  radish: "0.5",
};

function displayCropName(rawName) {
  if (!rawName) return rawName;
  const key = String(rawName)
    .toLowerCase()
    .replace(/-/g, "_")
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "");
  return displayNameMap[key] || rawName;
}

let analyzedItems = [];
let activeItem = null;
let activeRecipe = null;
let savedRecipes = [];
let canvasState = {
  scaleX: 1,
  scaleY: 1,
};

async function analyzeFile(file) {
  setStatus("Analyzing...");
  setCanvasHint("이미지 분석 중...");

  const form = new FormData();
  form.append("image", file);

  let res;
  try {
    res = await fetch("/api/analyze", { method: "POST", body: form });
  } catch (e) {
    setStatus("분석 실패");
    setCanvasHint("이미지 분석에 실패했습니다.");
    return;
  }

  if (!res.ok) {
    setStatus("분석 실패");
    setCanvasHint("이미지 분석에 실패했습니다.");
    return;
  }

  const data = await res.json();
  analyzedItems = data.items || [];

  const url = URL.createObjectURL(file);
  const img = new Image();
  img.onload = () => {
    canvas.width = img.width;
    canvas.height = img.height;

    const rect = canvas.getBoundingClientRect();
    const displayWidth = rect.width || img.width;
    const displayHeight = rect.height || img.height;

    canvasState.scaleX = img.width / displayWidth;
    canvasState.scaleY = img.height / displayHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);
    ctx.font = "16px Arial";

    analyzedItems.forEach((item) => {
      const b = item.bbox;
      ctx.strokeStyle = "lime";
      ctx.lineWidth = 3;
      ctx.strokeRect(b.x, b.y, b.w, b.h);

      const rawName = item.crop_name || item.detector_class_name;
      const displayName = displayCropName(rawName);
      const label = item.grade ? `${displayName} / ${item.grade || "?"}` : displayName;
      const labelWidth = ctx.measureText(label).width + 10;
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(b.x, Math.max(0, b.y - 20), labelWidth, 20);
      ctx.fillStyle = "white";
      ctx.fillText(label, b.x + 5, Math.max(15, b.y - 5));
    });

    setStatus(`${analyzedItems.length} items`);
    setCanvasHint("박스를 클릭하세요.");
  };
  img.src = url;
}

function normalizeRecipeRecord(recipe) {
  const ingredients = Array.isArray(recipe.ingredients) ? recipe.ingredients : [];
  const steps = Array.isArray(recipe.steps) ? recipe.steps : [];
  const checklistSource = Array.isArray(recipe.checklist_checked) ? recipe.checklist_checked : [];
  const checklistChecked = checklistSource.slice(0, ingredients.length);

  while (checklistChecked.length < ingredients.length) {
    checklistChecked.push(false);
  }

  return {
    id: recipe.id || `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    ingredient: recipe.ingredient || recipe.detector_class_name || "",
    title: recipe.title || "레시피",
    ingredients,
    steps,
    createdAt: recipe.createdAt || recipe.created_at || new Date().toISOString(),
    checklist_checked: checklistChecked,
  };
}

function formatSavedRecipeTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value || "");
  }

  const pad2 = (num) => String(num).padStart(2, "0");
  const year = String(date.getFullYear());
  const month = pad2(date.getMonth() + 1);
  const day = pad2(date.getDate());
  const hours = pad2(date.getHours());
  const minutes = pad2(date.getMinutes());
  const seconds = pad2(date.getSeconds());

  return `${year}.${month}.${day}_${hours}:${minutes}:${seconds}`;
}

function loadLocalRecipes() {
  try {
    const raw = localStorage.getItem(LOCAL_RECIPES_KEY) || localStorage.getItem(LEGACY_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((recipe) => normalizeRecipeRecord(recipe));
  } catch {
    return [];
  }
}

function saveLocalRecipes() {
  localStorage.setItem(LOCAL_RECIPES_KEY, JSON.stringify(localRecipes));
  localStorage.removeItem(LEGACY_STORAGE_KEY);
}

function setCanvasHint(message) {
  if (canvasHint) {
    canvasHint.textContent = message;
  }
}

function setAuthMessage(message, tone = "info") {
  authMessage.textContent = message;
  authMessage.dataset.tone = tone;
}

function updateAuthToggleLabel() {
  if (!authToggleBtn) return;
  authToggleBtn.textContent = currentUser ? "로그아웃" : "로그인";
}

function showAuthView(mode) {
  authViewMode = mode;
  loginView.classList.toggle("hidden", mode !== "login");
  signupView.classList.toggle("hidden", mode !== "signup");
  showAuthPanel();
}

function showAuthPanel() {
  authPanel.classList.remove("hidden");
  authPanelOpen = true;
}

function hideAuthPanel() {
  authPanel.classList.add("hidden");
  authPanelOpen = false;
}

function toggleAuthPanel() {
  if (authPanelOpen) {
    hideAuthPanel();
  } else {
    showAuthPanel();
  }
}

function setSession(token, user) {
  sessionToken = token;
  currentUser = user;
  localStorage.setItem(SESSION_TOKEN_KEY, token);
  localStorage.setItem(SESSION_USER_KEY, JSON.stringify(user));
  currentRecipeMode = "server";
  updateAuthToggleLabel();
}

function clearSession() {
  sessionToken = "";
  currentUser = null;
  currentRecipeMode = "local";
  localStorage.removeItem(SESSION_TOKEN_KEY);
  localStorage.removeItem(SESSION_USER_KEY);
  updateAuthToggleLabel();
}

function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (sessionToken) {
    headers.set("X-Session-Token", sessionToken);
  }
  return fetch(url, { ...options, headers });
}

function toServerRecipePayload(recipe) {
  return {
    ingredient: recipe.ingredient,
    title: recipe.title,
    ingredients: recipe.ingredients,
    steps: recipe.steps,
    created_at: recipe.createdAt,
    checklist_checked: recipe.checklist_checked,
  };
}

function replaceSavedRecipe(updatedRecipe) {
  const normalized = normalizeRecipeRecord(updatedRecipe);
  savedRecipes = savedRecipes.map((recipe) => (recipe.id === normalized.id ? normalized : recipe));
  if (currentRecipeMode === "local") {
    localRecipes = savedRecipes.slice();
    saveLocalRecipes();
  }
  return normalized;
}

function applyRecipeList(recipes, mode) {
  currentRecipeMode = mode;
  savedRecipes = recipes.map((recipe) => normalizeRecipeRecord(recipe));
  if (mode === "local") {
    localRecipes = savedRecipes.slice();
    saveLocalRecipes();
  }
  renderSavedRecipes();
}

async function fetchServerRecipes() {
  const response = await apiFetch("/api/me/recipes");
  if (!response.ok) {
    return [];
  }
  const recipes = await response.json();
  return recipes.map((recipe) => normalizeRecipeRecord(recipe));
}

async function syncLocalRecipesToServer() {
  if (!currentUser || !localRecipes.length) {
    return;
  }

  for (const recipe of localRecipes) {
    const response = await apiFetch("/api/me/recipes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(toServerRecipePayload(recipe)),
    });

    if (!response.ok) {
      throw new Error("Failed to sync saved recipes");
    }
  }

  localRecipes = [];
  saveLocalRecipes();
}

async function updateChecklistState(recipeId, checklistChecked) {
  if (currentRecipeMode === "server") {
    const response = await apiFetch(`/api/me/recipes/${recipeId}/checklist`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ checklist_checked: checklistChecked }),
    });

    if (!response.ok) {
      throw new Error("Failed to save checklist state");
    }

    const updatedRecipe = await response.json();
    replaceSavedRecipe(updatedRecipe);
    renderSavedRecipes();
    return;
  }

  const index = localRecipes.findIndex((recipe) => recipe.id === recipeId);
  if (index >= 0) {
    localRecipes[index].checklist_checked = checklistChecked.slice();
    saveLocalRecipes();
  }
}

async function restoreSession() {
  if (!sessionToken) {
    applyRecipeList(localRecipes, "local");
    renderAuthState();
    return;
  }

  const response = await apiFetch("/api/auth/me");
  if (!response.ok) {
    clearSession();
    applyRecipeList(localRecipes, "local");
    renderAuthState();
    return;
  }

  currentUser = await response.json();
  localStorage.setItem(SESSION_USER_KEY, JSON.stringify(currentUser));
  authUserLabel.textContent = `${currentUser.username}님으로 로그인됨`;

  try {
    await syncLocalRecipesToServer();
  } catch {
    setAuthMessage("기존 저장 항목 동기화에 실패했습니다. 새 레시피부터 서버에 저장됩니다.", "warning");
  }

  const recipes = await fetchServerRecipes();
  applyRecipeList(recipes, "server");
  renderAuthState();
}

function renderAuthState() {
  const signedIn = Boolean(currentUser);
  authStatus.classList.toggle("hidden", !signedIn);
  if (signedIn) {
    authUserLabel.textContent = `${currentUser.username}님으로 로그인됨`;
    setAuthMessage("로그인 상태입니다. 레시피와 체크리스트가 서버에 저장됩니다.");
  } else {
    authUserLabel.textContent = "";
    setAuthMessage("로그인하면 저장된 레시피와 체크리스트가 계정에 보관됩니다.");
  }
  updateAuthToggleLabel();
}

function setStatus(text) {
  if (statusPill) {
    statusPill.textContent = text;
  }
}

function loadSavedRecipes() {
  return loadLocalRecipes();
}

function saveSavedRecipes() {
  saveLocalRecipes();
}

function renderSavedRecipes() {
  if (savedRecipeCount) {
    savedRecipeCount.textContent = String(savedRecipes.length);
  }

  if (!savedRecipes.length) {
    savedRecipeEmpty.classList.remove("hidden");
    savedRecipeList.innerHTML = "";
    return;
  }

  savedRecipeEmpty.classList.add("hidden");
  savedRecipeList.innerHTML = "";

  const fragment = document.createDocumentFragment();
  savedRecipes.forEach((recipe) => {
    const item = document.createElement("div");
    item.className = "saved-recipe-item";
    item.dataset.recipeId = recipe.id;

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "saved-recipe-delete";
    deleteButton.dataset.deleteRecipeId = recipe.id;
    deleteButton.setAttribute("aria-label", `${recipe.title} 삭제`);
    deleteButton.textContent = "삭제";

    const bodyButton = document.createElement("button");
    bodyButton.type = "button";
    bodyButton.className = "saved-recipe-body";
    bodyButton.dataset.openRecipeId = recipe.id;

    const title = document.createElement("div");
    title.className = "saved-recipe-title";
    title.textContent = recipe.title;

    const sub = document.createElement("div");
    sub.className = "saved-recipe-sub";
    sub.textContent = `${displayCropName(recipe.ingredient)} · ${formatSavedRecipeTimestamp(recipe.createdAt)}`;

    bodyButton.append(title, sub);
    item.append(deleteButton, bodyButton);
    fragment.appendChild(item);
  });

  savedRecipeList.appendChild(fragment);
}

async function deleteSavedRecipe(recipeId) {
  const target = savedRecipes.find((item) => item.id === recipeId);
  if (!target) return;

  const confirmed = window.confirm(`"${target.title}" 레시피를 삭제할까요?`);
  if (!confirmed) return;

  if (currentRecipeMode === "server") {
    const response = await apiFetch(`/api/me/recipes/${recipeId}`, {
      method: "DELETE",
    });

    if (!response.ok && response.status !== 204) {
      throw new Error("Failed to delete saved recipe");
    }
  } else {
    localRecipes = localRecipes.filter((recipe) => recipe.id !== recipeId);
    saveLocalRecipes();
  }

  savedRecipes = savedRecipes.filter((recipe) => recipe.id !== recipeId);
  if (activeSavedRecipeId === recipeId) {
    activeSavedRecipeId = null;
    showHomeView();
  }
  renderSavedRecipes();
  setStatus("레시피가 삭제되었습니다");
}

function showHomeView() {
  homeView.classList.remove("hidden");
  recipeDetailView.classList.add("hidden");
}

function showRecipeDetail(recipe) {
  activeSavedRecipeId = recipe.id;
  detailRecipeTitle.textContent = recipe.title;
  detailRecipeMeta.textContent = `${displayCropName(recipe.ingredient)}로 만든 레시피입니다.`;

  const checklistState = Array.isArray(recipe.checklist_checked) ? recipe.checklist_checked : [];

  detailChecklist.innerHTML = (recipe.ingredients || [])
    .map((ingredient, index) => {
      const checked = checklistState[index] ? "checked" : "";
      return `
        <label class="checklist-item">
          <input type="checkbox" data-index="${index}" ${checked} />
          <span class="${checked}">${ingredient}</span>
        </label>
      `;
    })
    .join("");

  detailChecklist.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
    checkbox.addEventListener("change", async (event) => {
      const label = event.target.closest("label");
      const text = label.querySelector("span");
      text.classList.toggle("checked", event.target.checked);

      const targetRecipe = savedRecipes.find((item) => item.id === activeSavedRecipeId);
      if (!targetRecipe) return;

      const checklistChecked = Array.from(detailChecklist.querySelectorAll("input[type='checkbox']")).map(
        (element) => element.checked,
      );
      targetRecipe.checklist_checked = checklistChecked;

      if (currentRecipeMode === "local") {
        localRecipes = savedRecipes.slice();
        saveLocalRecipes();
        return;
      }

      try {
        await updateChecklistState(targetRecipe.id, checklistChecked);
      } catch {
        setStatus("체크리스트 저장에 실패했습니다");
      }
    });
  });

  detailSteps.innerHTML = (recipe.steps || [])
    .map((step) => `<li>${step}</li>`)
    .join("");

  homeView.classList.add("hidden");
  recipeDetailView.classList.remove("hidden");
}

function openSavedRecipe(recipeId) {
  const target = savedRecipes.find((item) => item.id === recipeId);
  if (!target) return;
  showRecipeDetail(target);
}

function openModal(item) {
  activeItem = item;
  activeRecipe = null;
  hideAuthPanel();
  confirmRecipeBtn.classList.add("hidden");
  modal.classList.remove("hidden");
  recipeSection.classList.add("hidden");

  const rawTitle = item.crop_name || item.detector_class_name || "알 수 없는 작물";
  modalTitle.textContent = displayCropName(rawTitle);
  const confidence = Number(item.grade_confidence || 0);
  const keyForRec = String(item.crop_name || item.detector_class_name || "")
    .toLowerCase()
    .replace(/-/g, "_")
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "");
  const rec = recommendedDailyMap[keyForRec] || "-";
  const recLabel = rec === "-" ? "-" : `${rec}개`;

  modalContent.innerHTML = `
    <div class="modal-meta">
      <span class="meta-chip">하루 권장 섭취량: ${recLabel}</span>
      <span class="meta-chip">등급: ${item.grade || "?"} (${item.grade_label_kr || "-"})</span>
      <span class="meta-chip">신뢰도: ${(confidence * 100).toFixed(1)}%</span>
    </div>
  `;
}

function closeModalView() {
  modal.classList.add("hidden");
  activeItem = null;
  activeRecipe = null;
  activeSavedRecipeId = null;
}

function renderTips(item) {
  const rawKey = (item.crop_name || item.detector_class_name || "") + "";
  const cropKey = rawKey
    .toLowerCase()
    .replace(/-/g, "_")
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "");
  const tip = tipsByCrop[cropKey] || tipsByCrop[rawKey.toLowerCase()] || "겉모양보다 무게감과 표면 상태를 함께 확인하세요.";

  confirmRecipeBtn.classList.add("hidden");
  recipeSection.innerHTML = `
    <h3>팁</h3>
    <p>${tip}</p>
  `;
  recipeSection.classList.remove("hidden");
}

async function loadRecipe(item) {
  if (!item) return;

  confirmRecipeBtn.classList.add("hidden");
  recipeSection.classList.remove("hidden");
  recipeSection.innerHTML = "<h3>추천 레시피</h3><p>레시피를 불러오는 중...</p>";

  const ingredient = item.crop_name || item.detector_class_name;
  let apiKey = localStorage.getItem(API_KEY_STORAGE_KEY) || "";

  async function requestRecipe(key) {
    const headers = { "Content-Type": "application/json" };
    if (key) {
      headers["X-API-KEY"] = key;
    }
    return fetch("/api/recipe", {
      method: "POST",
      headers,
      body: JSON.stringify({ ingredient }),
    });
  }

  let response;
  try {
    response = await requestRecipe(apiKey);
  } catch {
    recipeSection.innerHTML = "<h3>추천 레시피</h3><p>서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.</p>";
    setStatus("레시피 요청 실패");
    return;
  }

  if (response.status === 401 && !apiKey) {
    const enteredKey = window.prompt("API 키를 입력해주세요.");
    if (enteredKey && enteredKey.trim()) {
      apiKey = enteredKey.trim();
      localStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
      response = await requestRecipe(apiKey);
    }
  }

  if (!response.ok) {
    let reason = "알 수 없는 오류";
    try {
      const errorPayload = await response.json();
      reason = errorPayload.reason || errorPayload.detail || reason;
    } catch {
      reason = `HTTP ${response.status}`;
    }
    recipeSection.innerHTML = `<h3>추천 레시피</h3><p>레시피를 불러오지 못했습니다. (${reason})</p>`;
    setStatus("레시피 불러오기 실패");
    return;
  }

  const recipe = await response.json();
  activeRecipe = normalizeRecipeRecord({
    ingredient,
    title: recipe.title || `${ingredient} 레시피`,
    ingredients: recipe.ingredients || [],
    steps: recipe.steps || [],
    createdAt: new Date().toISOString(),
    checklist_checked: new Array((recipe.ingredients || []).length).fill(false),
  });

  recipeSection.innerHTML = `
    <h3>${activeRecipe.title}</h3>
    <strong>재료</strong>
    <ul>
      ${activeRecipe.ingredients.map((entry) => `<li>${entry}</li>`).join("")}
    </ul>
    <strong>조리 순서</strong>
    <ol>
      ${activeRecipe.steps.map((step) => `<li>${step}</li>`).join("")}
    </ol>
  `;

  confirmRecipeBtn.classList.remove("hidden");
  setStatus("레시피를 불러왔습니다");
}

async function confirmRecipe() {
  if (!activeRecipe) return;

  if (!currentUser) {
    const localRecipe = normalizeRecipeRecord({
      ...activeRecipe,
      checklist_checked: activeRecipe.checklist_checked || new Array(activeRecipe.ingredients.length).fill(false),
    });
    localRecipes.unshift(localRecipe);
    saveLocalRecipes();
    applyRecipeList(localRecipes, "local");
    setStatus("레시피가 저장되었습니다");
    closeModalView();
    return;
  }

  const response = await apiFetch("/api/me/recipes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(toServerRecipePayload(activeRecipe)),
  });

  if (!response.ok) {
    setStatus("레시피 저장에 실패했습니다");
    return;
  }

  const savedRecipe = normalizeRecipeRecord(await response.json());
  savedRecipes.unshift(savedRecipe);
  renderSavedRecipes();
  setStatus("레시피가 서버에 저장되었습니다");
  closeModalView();
}

function canvasPointToImage(pointX, pointY) {
  const rect = canvas.getBoundingClientRect();
  const x = (pointX - rect.left) * canvasState.scaleX;
  const y = (pointY - rect.top) * canvasState.scaleY;
  return { x, y };
}

function hitTestBox(point) {
  return analyzedItems.find((item) => {
    const b = item.bbox;
    return point.x >= b.x && point.x <= b.x + b.w && point.y >= b.y && point.y <= b.y + b.h;
  });
}

canvas.addEventListener("click", (event) => {
  if (!analyzedItems.length) return;
  const point = canvasPointToImage(event.clientX, event.clientY);
  const hit = hitTestBox(point);
  if (hit) {
    openModal(hit);
  }
});

savedRecipeList.addEventListener("click", (event) => {
  const deleteTarget = event.target.closest("[data-delete-recipe-id]");
  if (deleteTarget) {
    const recipeId = deleteTarget.dataset.deleteRecipeId;
    deleteSavedRecipe(recipeId).catch(() => {
      setStatus("레시피 삭제에 실패했습니다");
    });
    return;
  }

  const openTarget = event.target.closest("[data-open-recipe-id]");
  if (!openTarget) return;
  openSavedRecipe(openTarget.dataset.openRecipeId);
});

uploadBtn.onclick = async () => {
  if (!input.files.length) {
    alert("Select an image");
    return;
  }

  setStatus("Analyzing...");
  setCanvasHint("이미지 분석 중...");

  const file = input.files[0];
  const form = new FormData();
  form.append("image", file);

  const res = await fetch("/api/analyze", { method: "POST", body: form });
  if (!res.ok) {
    setStatus("분석 실패");
    setCanvasHint("이미지 분석에 실패했습니다.");
    return;
  }

  const data = await res.json();
  analyzedItems = data.items || [];

  const url = URL.createObjectURL(file);
  const img = new Image();
  img.onload = () => {
    canvas.width = img.width;
    canvas.height = img.height;

    const rect = canvas.getBoundingClientRect();
    const displayWidth = rect.width || img.width;
    const displayHeight = rect.height || img.height;

    canvasState.scaleX = img.width / displayWidth;
    canvasState.scaleY = img.height / displayHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);
    ctx.font = "16px Arial";

    analyzedItems.forEach((item) => {
      const b = item.bbox;
      ctx.strokeStyle = "lime";
      ctx.lineWidth = 3;
      ctx.strokeRect(b.x, b.y, b.w, b.h);
      const rawName = item.crop_name || item.detector_class_name;
      const displayName = displayCropName(rawName);
      const label = item.grade ? `${displayName} / ${item.grade || "?"}` : displayName;
      const labelWidth = ctx.measureText(label).width + 10;
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(b.x, Math.max(0, b.y - 20), labelWidth, 20);
      ctx.fillStyle = "white";
      ctx.fillText(label, b.x + 5, Math.max(15, b.y - 5));
    });

    setStatus(`${analyzedItems.length} items`);
    setCanvasHint("박스를 클릭하세요.");
  };
  img.src = url;
};

tipsBtn.addEventListener("click", () => {
  if (activeItem) renderTips(activeItem);
});

recipeBtn.addEventListener("click", async () => {
  if (activeItem) await loadRecipe(activeItem);
});

confirmRecipeBtn.addEventListener("click", () => {
  confirmRecipe().catch(() => setStatus("레시피 저장에 실패했습니다"));
});

signupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = signupUsername.value.trim();
  const password = signupPassword.value;
  if (!username || !password) {
    setAuthMessage("회원가입 정보를 입력해주세요.", "warning");
    return;
  }

  const response = await fetch("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    setAuthMessage(payload.reason || payload.detail || "회원가입에 실패했습니다.", "error");
    return;
  }

  const payload = await response.json();
  setSession(payload.token, payload.user);
  signupForm.reset();
  await restoreSession();
  hideAuthPanel();
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = loginUsername.value.trim();
  const password = loginPassword.value;
  if (!username || !password) {
    setAuthMessage("로그인 정보를 입력해주세요.", "warning");
    return;
  }

  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    setAuthMessage(payload.reason || payload.detail || "로그인에 실패했습니다.", "error");
    return;
  }

  const payload = await response.json();
  setSession(payload.token, payload.user);
  loginForm.reset();
  await restoreSession();
  hideAuthPanel();
});

logoutBtn.addEventListener("click", () => {
  clearSession();
  localRecipes = loadLocalRecipes();
  applyRecipeList(localRecipes, "local");
  renderAuthState();
  showAuthView("login");
});

authToggleBtn.addEventListener("click", () => {
  if (currentUser) {
    clearSession();
    localRecipes = loadLocalRecipes();
    applyRecipeList(localRecipes, "local");
    renderAuthState();
    showAuthView("login");
    hideAuthPanel();
    return;
  }

  toggleAuthPanel();
});

openSignupBtn.addEventListener("click", () => showAuthView("signup"));
openLoginBtn.addEventListener("click", () => showAuthView("login"));

backToHomeBtn.addEventListener("click", showHomeView);
closeModal.addEventListener("click", closeModalView);
modalBackdrop.addEventListener("click", closeModalView);

// Floating action button behavior (mobile)
if (fabMain) {
  fabMain.addEventListener("click", () => {
    if (!fabContainer || !fabActions) return;
    const isOpen = fabContainer.classList.toggle("fab-open");
    fabActions.setAttribute("aria-hidden", String(!isOpen));
  });
}

if (fabCamera) {
  fabCamera.addEventListener("click", () => {
    if (!cameraInput) return;
    cameraInput.value = null;
    cameraInput.click();
  });
}

if (cameraInput) {
  cameraInput.addEventListener("change", async (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    // close FAB actions after action
    if (fabContainer) fabContainer.classList.remove("fab-open");
    await analyzeFile(file);
  });
}

if (fabFolder) {
  fabFolder.addEventListener("click", () => {
    // trigger existing file input (folder picker)
    if (!input) return;
    input.click();
    if (fabContainer) fabContainer.classList.remove("fab-open");
  });
}

savedRecipes = loadSavedRecipes();
localRecipes = savedRecipes.slice();
applyRecipeList(localRecipes, "local");
renderAuthState();
showHomeView();
loginView.classList.remove("hidden");
signupView.classList.add("hidden");
hideAuthPanel();
restoreSession().catch(() => {
  clearSession();
  localRecipes = loadLocalRecipes();
  applyRecipeList(localRecipes, "local");
  renderAuthState();
});
