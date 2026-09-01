/* ── State ─────────────────────────────────────── */
let currentMode = 't2i';
let modelsData = null;
let presetsData = null;

/* ── Init ───────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
    initBackground();
    initDragAndDrop();
    await Promise.all([fetchModels(), fetchPresets()]);
    updateCharCount('negPromptInput', 'negCount');
    updateUploadVisibility();
    pollStatus();
    setInterval(pollStatus, 3000);
});

/* ── Fetch Models from API ─────────────────────── */
async function fetchModels() {
    try {
        const res = await fetch('/api/models');
        modelsData = await res.json();
        populateModelDropdown();
    } catch (e) {
        console.error('Failed to fetch models:', e);
    }
}

function populateModelDropdown() {
    const select = document.getElementById('modelSelect');
    select.innerHTML = '';

    const models = currentMode === 't2i' ? modelsData.t2i : modelsData.i2i;
    const defaultId = currentMode === 't2i' ? modelsData.default_t2i : modelsData.default_i2i;

    models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = `${m.name} — ${m.desc}`;
        if (m.id === defaultId) opt.selected = true;
        select.appendChild(opt);
    });

    onModelChange();
}

/* ── Fetch Presets from API ──────────────────────── */
async function fetchPresets() {
    try {
        const res = await fetch('/api/presets');
        presetsData = await res.json();
        populatePresetDropdown();
    } catch (e) {
        console.error('Failed to fetch presets:', e);
    }
}

let presetsExpanded = false;

function populatePresetDropdown() {
    const grid = document.getElementById('presetGrid');
    grid.innerHTML = '';

    // Add a "None" preset
    const noneItem = document.createElement('div');
    noneItem.className = 'preset-item active';
    noneItem.textContent = 'None';
    noneItem.dataset.value = '';
    noneItem.onclick = () => selectPreset(noneItem);
    grid.appendChild(noneItem);

    if (!presetsData || !presetsData.all) return;

    const topPresetIds = ['anim_japan', 'photo_fisheye', 'art_oil'];
    let topPresets = presetsData.all.filter(p => topPresetIds.includes(p.id));

    topPresets.forEach((p) => {
        const item = document.createElement('div');
        item.className = 'preset-item';
        item.textContent = p.label;
        item.dataset.value = p.id;
        item.onclick = () => selectPreset(item);
        grid.appendChild(item);
    });

    // Populate Modal Grid
    const modalGrid = document.getElementById('modalPresetGrid');
    modalGrid.innerHTML = '';
    const cats = presetsData.categories;
    for (const [category, presets] of Object.entries(cats)) {
        const catLabel = document.createElement('div');
        catLabel.className = 'modal-category';
        catLabel.textContent = category;
        modalGrid.appendChild(catLabel);

        const catGrid = document.createElement('div');
        catGrid.className = 'preset-grid';
        catGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(110px, 1fr))';

        presets.forEach(p => {
            const item = document.createElement('div');
            item.className = 'preset-item';
            item.textContent = p.label;
            item.dataset.value = p.id;
            item.onclick = () => {
                selectPreset(item);
                closePresetModal();
            };
            catGrid.appendChild(item);
        });
        modalGrid.appendChild(catGrid);
    }
}

function selectPreset(itemOrValue) {
    let value = typeof itemOrValue === 'string' ? itemOrValue : itemOrValue.dataset.value;

    document.querySelectorAll('.preset-item').forEach(el => {
        if (el.dataset.value === value) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });

    const hiddenInput = document.getElementById('presetSelect');
    hiddenInput.value = value;
    onPresetChange();
}

function openPresetModal() {
    document.getElementById('presetModal').classList.add('active');
}

function closePresetModal() {
    document.getElementById('presetModal').classList.remove('active');
}

/* ── Mode Switching ────────────────────────────── */
function switchMode(mode) {
    currentMode = mode;

    // Toggle buttons
    document.querySelectorAll('#modeToggle button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    // Re-populate models for this mode
    if (modelsData) populateModelDropdown();

    // Show/hide upload and strength
    updateUploadVisibility();
}

function updateUploadVisibility() {
    const uploadSection = document.getElementById('uploadSection');
    const strengthRow = document.getElementById('strengthRow');

    if (currentMode === 'i2i') {
        uploadSection.classList.remove('hidden');
        strengthRow.style.display = 'flex';
    } else {
        uploadSection.classList.add('hidden');
        strengthRow.style.display = 'none';
    }
}

/* ── Model Change Handler ─────────────────────── */
function onModelChange() {
    if (!modelsData) return;

    const select = document.getElementById('modelSelect');
    const modelId = select.value;
    const models = currentMode === 't2i' ? modelsData.t2i : modelsData.i2i;
    const model = models.find(m => m.id === modelId);

    if (model) {
        // Auto-fill default slider values
        document.getElementById('guidanceSlider').value = model.default_guidance;
        document.getElementById('guidanceVal').textContent = parseFloat(model.default_guidance).toFixed(1);
        document.getElementById('stepsSlider').value = model.default_steps;
        document.getElementById('stepsVal').textContent = model.default_steps;

        if (model.default_strength !== undefined) {
            document.getElementById('strengthSlider').value = model.default_strength;
            document.getElementById('strengthVal').textContent = model.default_strength;
        }
    }
}

/* ── Preset Change Handler ───────────────────────── */
function onPresetChange() {
    const select = document.getElementById('presetSelect');
    const presetId = select.value;

    if (presetId && presetsData) {
        const preset = presetsData.all.find(p => p.id === presetId);
        if (preset) {
            const promptInput = document.getElementById('promptInput');
            if (!promptInput.value.trim()) {
                promptInput.placeholder = `Style: ${preset.label} — add custom details or leave empty`;
            }
        }
    } else {
        const promptInput = document.getElementById('promptInput');
        if (!promptInput.value.trim()) {
            promptInput.placeholder = "Describe your image... A cyberpunk cityscape at sunset, neon reflections on wet streets";
        }
    }
}

/* ── Collapsible Sections ──────────────────────── */
function toggleCollapsible(triggerId, contentId) {
    const trigger = document.getElementById(triggerId);
    const content = document.getElementById(contentId);
    trigger.classList.toggle('open');
    content.classList.toggle('open');
}

/* ── Character Count ───────────────────────────── */
function updateCharCount(inputId, countId) {
    const el = document.getElementById(inputId);
    const count = document.getElementById(countId);
    count.textContent = `${el.value.length} chars`;
}

/* ── Seed Randomizer ───────────────────────────── */
function randomizeSeed() {
    const seed = Math.floor(Math.random() * 4294967295);
    document.getElementById('seedInput').value = seed;
}

/* ── File Upload ─────────────────────────────────── */
function onFileSelected(input) {
    const zone = document.getElementById('uploadZone');
    const text = document.getElementById('uploadText');
    const filename = document.getElementById('uploadFilename');
    const thumb = document.getElementById('uploadThumb');

    if (input.files && input.files.length > 0) {
        const file = input.files[0];
        zone.classList.add('has-file');
        text.textContent = 'Image loaded';
        filename.textContent = file.name;

        // Show thumbnail preview
        const reader = new FileReader();
        reader.onload = e => {
            thumb.src = e.target.result;
            thumb.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        zone.classList.remove('has-file');
        text.textContent = 'Drop image or click to browse';
        filename.textContent = '';
        thumb.style.display = 'none';
    }
}

function initDragAndDrop() {
    const zone = document.getElementById('uploadZone');
    const input = document.getElementById('fileInput');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(name => {
        zone.addEventListener(name, e => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(name => {
        zone.addEventListener(name, () => zone.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(name => {
        zone.addEventListener(name, () => zone.classList.remove('drag-over'), false);
    });

    zone.addEventListener('drop', e => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            input.files = files;
            onFileSelected(input);
        }
    }, false);
}

/* ── Status Polling ────────────────────────────── */
async function pollStatus() {
    const el = document.getElementById('statusText');
    const dot = document.querySelector('.status-dot');
    try {
        const res = await fetch('/api/status');
        if (!res.ok) throw new Error('Not ok');
        const data = await res.json();

        dot.style.background = 'var(--success)';
        dot.style.boxShadow = '0 0 6px var(--success)';

        if (data.model) {
            el.textContent = `Online · ${data.model} loaded · ${data.vram_mb} MB VRAM`;
        } else {
            el.textContent = `Online · Ready`;
        }
    } catch (e) {
        dot.style.background = 'var(--danger)';
        dot.style.boxShadow = '0 0 6px var(--danger)';
        el.textContent = 'Offline — Server not running';
    }
}

/* ── CLI State Management ─────────────────────────── */
let progressInterval = null;
let currentProgress = 0;
let progressWs = null;

function showCliIdle() {
    const container = document.getElementById('cli-container');
    const idle = document.getElementById('cli-idle-state');
    const loading = document.getElementById('cli-loading-state');
    const resultImg = document.getElementById('resultImg');

    container.classList.remove('hidden');
    idle.style.display = 'flex';
    loading.classList.remove('active');
    resultImg.classList.remove('visible');
}

function showCliLoading() {
    const container = document.getElementById('cli-container');
    const idle = document.getElementById('cli-idle-state');
    const loading = document.getElementById('cli-loading-state');

    container.classList.remove('hidden');
    idle.style.display = 'none';
    loading.classList.add('active');
    currentProgress = 0;
    updateProgressBar(0);
    updateStatusLine('initializing pipeline');
}

function showCliResult() {
    const container = document.getElementById('cli-container');
    container.classList.add('hidden');
}

function updateProgressBar(percent) {
    const barEl = document.getElementById('cliProgressBar');
    const totalBlocks = 20;
    const filled = Math.round((percent / 100) * totalBlocks);
    const empty = totalBlocks - filled;
    const bar = '\u2588'.repeat(filled) + '\u2591'.repeat(empty);
    barEl.textContent = `[${bar}] ${Math.round(percent)}%`;
}

function updateStatusLine(msg, isError, isSuccess) {
    const el = document.getElementById('cliStatusLine');
    el.className = 'cli-status-line';
    if (isError) {
        el.innerHTML = `<span class="cli-error">[ERR] ${msg}</span>`;
    } else if (isSuccess) {
        el.innerHTML = `<span class="cli-success">[OK] ${msg}</span>`;
    } else {
        el.innerHTML = `${msg}<span class="blink-cursor">_</span>`;
    }
}

function startWebSocketProgress() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    progressWs = new WebSocket(`${protocol}//${window.location.host}/api/ws/progress`);

    progressWs.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            const { step, total, status } = data;

            if (status === 'idle') return;

            if (total > 0 && step > 0) {
                currentProgress = Math.round((step / total) * 100);
            }
            updateProgressBar(Math.min(currentProgress, 99));
            updateStatusLine(`${status} (${step}/${total})`);
        } catch (e) {
            // ignore parse errors
        }
    };

    progressWs.onerror = () => {
        // silently ignore — the HTTP request will still complete
    };
}

function stopProgress() {
    if (progressWs) {
        try { progressWs.close(); } catch(e) {}
        progressWs = null;
    }
}

/* ── Generation ──────────────────────────────────── */
async function generate() {
    const btn = document.getElementById('generateBtn');
    const resultImg = document.getElementById('resultImg');
    const metaBar = document.getElementById('metaBar');
    const actionBtns = document.getElementById('actionBtns');
    const storyPanel = document.getElementById('storyPanel');

    // Validation for I2I mode
    if (currentMode === 'i2i') {
        const fileInput = document.getElementById('fileInput');
        if (fileInput.files.length === 0) {
            alert('Please upload a source image for Image-to-Image mode.');
            return;
        }
    }

    // Gather params
    const modelId = document.getElementById('modelSelect').value;
    const prompt = document.getElementById('promptInput').value;
    const negPrompt = document.getElementById('negPromptInput').value;
    const strength = parseFloat(document.getElementById('strengthSlider').value);
    const guidance = parseFloat(document.getElementById('guidanceSlider').value);
    const steps = parseInt(document.getElementById('stepsSlider').value);
    const seed = parseInt(document.getElementById('seedInput').value) || -1;
    const preset = document.getElementById('presetSelect').value || '';

    // UI -> CLI Loading state
    btn.disabled = true;
    btn.innerHTML = '<span style="animation: pulse-text 2s ease-in-out infinite;">GENERATING...</span>';
    resultImg.classList.remove('visible');
    metaBar.classList.remove('visible');
    actionBtns.classList.remove('visible');
    storyPanel.classList.remove('visible');

    showCliLoading();
    startWebSocketProgress();

    // Build FormData
    const formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('negative_prompt', negPrompt);
    formData.append('model_id', modelId);
    formData.append('strength', strength);
    formData.append('guidance_scale', guidance);
    formData.append('num_inference_steps', steps);
    formData.append('seed', seed);
    if (preset) formData.append('preset', preset);

    // Attach file for I2I
    if (currentMode === 'i2i') {
        const fileInput = document.getElementById('fileInput');
        if (fileInput.files.length > 0) {
            formData.append('file', fileInput.files[0]);
        }
    }

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (data.status === 'success') {
            stopProgress();
            currentProgress = 100;
            updateProgressBar(100);
            updateStatusLine('generation complete', false, true);

            await new Promise(r => setTimeout(r, 300));

            resultImg.src = data.image_url + '?t=' + Date.now();
            resultImg.onload = () => {
                showCliResult();
                resultImg.classList.add('visible');

                document.getElementById('metaModel').textContent = data.model_id || '--';
                document.getElementById('metaSeed').textContent = data.seed || '--';
                document.getElementById('metaTime').textContent = data.time_seconds ? `${data.time_seconds}s` : '--';
                metaBar.classList.add('visible');

                const dlLink = document.getElementById('downloadLink');
                dlLink.href = data.image_url;
                let safePrompt = prompt.trim().substring(0, 50).replace(/[^a-zA-Z0-9_\- ]/g, '_');
                if (!safePrompt) safePrompt = 'image';
                dlLink.download = `${safePrompt} - generated by dreamU.png`;
                actionBtns.classList.add('visible');

                if (data.title) {
                    document.getElementById('storyTitle').textContent = data.title;
                    document.getElementById('storyText').textContent = data.story || '';
                    storyPanel.classList.add('visible');
                }

                if (data.seed) {
                    document.getElementById('seedInput').value = data.seed;
                }
            };

            setTimeout(async () => {
                await pollStatus();
                try {
                    const statusRes = await fetch('/api/status');
                    const statusData = await statusRes.json();
                    document.getElementById('metaVram').textContent = `${statusData.vram_mb} MB`;
                } catch (e) { }
            }, 500);

        } else {
            stopProgress();
            updateStatusLine('GENERATION FAILED: ' + (data.error || 'Unknown error'), true);
            updateProgressBar(currentProgress);
            setTimeout(() => showCliIdle(), 3000);
        }
    } catch (err) {
        console.error('Generation error:', err);
        stopProgress();
        updateStatusLine('CONNECTION FAILED - Is the server running?', true);
        updateProgressBar(currentProgress);
        setTimeout(() => showCliIdle(), 3000);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Generate</span><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>';
    }
}

function resetUI() {
    stopProgress();
    showCliIdle();
}

function initBackground() {
    const canvas = document.getElementById('automaton-bg');
    const ctx = canvas.getContext('2d');
    let width, height, cols, rows;
    const CELL_SIZE = 15;
    let grid = [];

    function resize() {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
        cols = Math.ceil(width / CELL_SIZE);
        rows = Math.ceil(height / CELL_SIZE);
        initGrid();
    }

    function initGrid() {
        grid = new Array(cols).fill(null).map(() =>
            new Array(rows).fill(null).map(() => Math.random() > 0.85 ? 1 : 0)
        );
    }

    function getExclusionBounds() {
        const logo = document.getElementById('mainLogo');
        const cli = document.getElementById('cli-container');
        const bounds = [];

        if (logo) {
            const r = logo.getBoundingClientRect();
            bounds.push({ x1: r.left - 1, y1: r.top - 5, x2: r.right + 1, y2: r.bottom + 5 });
        }
        if (cli && cli.offsetParent !== null) {
            const r = cli.getBoundingClientRect();
            bounds.push({ x1: r.left - 3, y1: r.top - 15, x2: r.right + 3, y2: r.bottom + 15 });
        }
        return bounds;
    }

    function reseed() {
        for (let i = 0; i < 5; i++) {
            const cx = Math.floor(Math.random() * cols);
            const cy = Math.floor(Math.random() * rows);
            for (let x = -2; x <= 2; x++) {
                for (let y = -2; y <= 2; y++) {
                    const nx = (cx + x + cols) % cols;
                    const ny = (cy + y + rows) % rows;
                    if (Math.random() > 0.5) grid[nx][ny] = 1;
                }
            }
        }
    }

    function countNeighbors(x, y) {
        let sum = 0;
        for (let i = -1; i <= 1; i++) {
            for (let j = -1; j <= 1; j++) {
                if (i === 0 && j === 0) continue;
                const nx = (x + i + cols) % cols;
                const ny = (y + j + rows) % rows;
                sum += grid[nx][ny];
            }
        }
        return sum;
    }

    function update() {
        let nextGrid = new Array(cols).fill(null).map(() => new Array(rows).fill(0));
        let changed = false;
        let aliveCount = 0;

        for (let x = 0; x < cols; x++) {
            for (let y = 0; y < rows; y++) {
                const state = grid[x][y];
                const neighbors = countNeighbors(x, y);

                if (state === 1 && (neighbors < 2 || neighbors > 3)) {
                    nextGrid[x][y] = 0;
                    changed = true;
                } else if (state === 0 && neighbors === 3) {
                    nextGrid[x][y] = 1;
                    changed = true;
                } else {
                    nextGrid[x][y] = state;
                }

                if (nextGrid[x][y]) aliveCount++;
            }
        }
        grid = nextGrid;

        return { changed, aliveCount };
    }

    let lastTime = 0;
    const THROTTLE_MS = 80;
    let staticFrames = 0;

    function loop(timestamp) {
        requestAnimationFrame(loop);

        if (timestamp - lastTime < THROTTLE_MS) return;
        lastTime = timestamp;

        const { changed, aliveCount } = update();

        if (!changed || aliveCount < 10) {
            staticFrames++;
            if (staticFrames > 50) {
                reseed();
                staticFrames = 0;
            }
        } else {
            staticFrames = 0;
        }

        ctx.fillStyle = 'rgba(5, 2, 8, 0.3)';
        ctx.fillRect(0, 0, width, height);

        const allBounds = getExclusionBounds();
        ctx.beginPath();
        ctx.fillStyle = '#b068f0';
        ctx.shadowBlur = 8;
        ctx.shadowColor = '#b068f0';

        for (let x = 0; x < cols; x++) {
            for (let y = 0; y < rows; y++) {
                if (grid[x][y] === 1) {
                    const rx = x * CELL_SIZE;
                    const ry = y * CELL_SIZE;

                    let inside = false;
                    for (const b of allBounds) {
                        if (rx >= b.x1 && rx <= b.x2 && ry >= b.y1 && ry <= b.y2) {
                            inside = true;
                            break;
                        }
                    }

                    if (!inside) {
                        ctx.rect(rx + 1, ry + 1, CELL_SIZE - 2, CELL_SIZE - 2);
                    }
                }
            }
        }
        ctx.fill();
    }

    window.addEventListener('resize', resize);
    resize();
    requestAnimationFrame(loop);
}

/* ── History Drawer Logic ────────────────────────── */
function openHistoryDrawer() {
    document.getElementById('historyOverlay').classList.add('active');
    document.getElementById('historyDrawer').classList.add('active');
    loadHistory();
}

function closeHistoryDrawer() {
    document.getElementById('historyOverlay').classList.remove('active');
    document.getElementById('historyDrawer').classList.remove('active');
}

async function loadHistory() {
    const grid = document.getElementById('historyGrid');
    grid.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem;">Loading...</div>';

    try {
        const res = await fetch('/api/history');
        const data = await res.json();

        if (!data.history || data.history.length === 0) {
            grid.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem;">No history found.</div>';
            return;
        }

        grid.innerHTML = '';
        data.history.forEach(item => {
            const el = document.createElement('div');
            el.className = 'history-item';

            const img = document.createElement('img');
            img.src = item.url;
            img.loading = 'lazy';

            const timeLabel = document.createElement('div');
            timeLabel.className = 'time-label';
            const date = new Date(item.time * 1000);
            timeLabel.textContent = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

            let promptOverlay = null;
            if (item.prompt) {
                promptOverlay = document.createElement('div');
                promptOverlay.className = 'prompt-overlay';

                const p = document.createElement('p');
                p.textContent = item.prompt;
                promptOverlay.appendChild(p);
            }

            el.onclick = () => {
                const resultImg = document.getElementById('resultImg');
                resultImg.src = item.url;
                resultImg.classList.add('visible');
                showCliResult();

                document.getElementById('downloadLink').href = item.url;
                document.getElementById('downloadLink').download = item.name;
                document.getElementById('actionBtns').classList.add('visible');

                if (window.innerWidth <= 1024) {
                    closeHistoryDrawer();
                }
            };

            el.appendChild(img);
            if (promptOverlay) {
                el.appendChild(promptOverlay);
            }
            el.appendChild(timeLabel);
            grid.appendChild(el);
        });
    } catch (err) {
        console.error(err);
        grid.innerHTML = '<div style="color: var(--danger); font-size: 0.8rem;">Failed to load history.</div>';
    }
}

async function fetchSystemStats() {
    try {
        const res = await fetch('/api/system_stats');
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById('systemStats').style.display = 'flex';

        document.getElementById('sysCpuFreq').textContent = data.cpu.freq_mhz;
        document.getElementById('sysCpuBar').style.width = data.cpu.usage_percent + '%';
        document.getElementById('sysCpuVal').textContent = Math.round(data.cpu.usage_percent) + '%';

        document.getElementById('sysMemUsed').textContent = data.memory.used_gb;
        document.getElementById('sysMemTotal').textContent = data.memory.total_gb;
        document.getElementById('sysMemBar').style.width = data.memory.usage_percent + '%';
        document.getElementById('sysMemVal').textContent = Math.round(data.memory.usage_percent) + '%';

        if (data.gpu.name !== 'N/A') {
            document.getElementById('sysGpuName').textContent = data.gpu.name;
            document.getElementById('sysGpuFreq').textContent = data.gpu.freq_mhz;
            document.getElementById('sysGpuTemp').textContent = data.gpu.temp_c;
            document.getElementById('sysGpuBar').style.width = data.gpu.usage_percent + '%';
            document.getElementById('sysGpuVal').textContent = Math.round(data.gpu.usage_percent) + '%';

            document.getElementById('sysVramUsed').textContent = data.gpu.mem_used_mb;
            document.getElementById('sysVramTotal').textContent = data.gpu.mem_total_mb;
            const vramPercent = data.gpu.mem_total_mb > 0 ? (data.gpu.mem_used_mb / data.gpu.mem_total_mb) * 100 : 0;
            document.getElementById('sysVramBar').style.width = vramPercent + '%';
            document.getElementById('sysVramVal').textContent = Math.round(vramPercent) + '%';
        } else {
            document.getElementById('gpuStatRow').style.display = 'none';
            document.getElementById('gpuMemRow').style.display = 'none';
        }
    } catch (err) {
        console.error('Failed to fetch system stats:', err);
    }
}

setInterval(fetchSystemStats, 1500);
setTimeout(fetchSystemStats, 500);
