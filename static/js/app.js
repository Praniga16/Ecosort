/**
 * EcoSort AI - Modern Web App Logic
 * Modular Vanilla JavaScript Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide Icons if available
  if (window.lucide) {
    lucide.createIcons();
  }

  // Setup Mobile Nav Toggle
  setupMobileNav();

  // Page-specific setup
  if (document.getElementById('dropzone')) {
    initScanner();
  }
  if (document.getElementById('historyTableBody')) {
    initHistoryPage();
  }
  if (document.getElementById('categoryChart')) {
    initAnalyticsPage();
  }
});

/* Global Toast Notification System */
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || 'ℹ'}</span>
    <span class="toast-message">${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/* Mobile Sidebar Toggle */
function setupMobileNav() {
  const toggleBtn = document.getElementById('mobileToggle');
  const sidebar = document.getElementById('sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('mobile-open');
    });
  }
}

/* Scanner Variables */
let selectedFile = null;
let cameraStream = null;

function initScanner() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const browseBtn = document.getElementById('browseBtn');
  const openCameraBtn = document.getElementById('openCameraBtn');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const removeBtn = document.getElementById('removeBtn');
  const captureBtn = document.getElementById('captureBtn');
  const closeCameraBtn = document.getElementById('closeCameraBtn');

  if (browseBtn && fileInput) {
    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelection(e.target.files[0]);
      }
    });
  }

  if (dropzone) {
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelection(e.dataTransfer.files[0]);
      }
    });
  }

  if (openCameraBtn) openCameraBtn.addEventListener('click', openCamera);
  if (closeCameraBtn) closeCameraBtn.addEventListener('click', closeCamera);
  if (captureBtn) captureBtn.addEventListener('click', capturePhoto);
  if (removeBtn) removeBtn.addEventListener('click', resetScan);
  if (analyzeBtn) analyzeBtn.addEventListener('click', analyzeImage);
}

function handleFileSelection(file) {
  const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
  const maxSize = 10 * 1024 * 1024; // 10MB

  if (!validTypes.includes(file.type)) {
    showToast('Please upload a valid JPG, PNG, or WEBP image.', 'error');
    return;
  }

  if (file.size > maxSize) {
    showToast('File size exceeds the 10 MB limit.', 'error');
    return;
  }

  selectedFile = file;
  previewImage(file);
}

function previewImage(file) {
  const dropzone = document.getElementById('dropzone');
  const previewContainer = document.getElementById('previewContainer');
  const previewImg = document.getElementById('previewImg');
  const fileNameDisplay = document.getElementById('fileNameDisplay');
  const fileSizeDisplay = document.getElementById('fileSizeDisplay');

  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';

    dropzone.style.display = 'none';
    previewContainer.classList.add('active');

    // Reset old results
    hideResult();
  };
  reader.readAsDataURL(file);
}

function resetScan() {
  selectedFile = null;
  const dropzone = document.getElementById('dropzone');
  const previewContainer = document.getElementById('previewContainer');
  const fileInput = document.getElementById('fileInput');

  if (fileInput) fileInput.value = '';
  if (dropzone) dropzone.style.display = 'flex';
  if (previewContainer) previewContainer.classList.remove('active');

  hideResult();
}

async function analyzeImage() {
  if (!selectedFile) {
    showToast('Please select or capture an image first.', 'warning');
    return;
  }

  const scanningOverlay = document.getElementById('scanningOverlay');
  const analyzeBtn = document.getElementById('analyzeBtn');

  if (scanningOverlay) scanningOverlay.classList.add('active');
  if (analyzeBtn) analyzeBtn.disabled = true;

  const formData = new FormData();
  formData.append('image', selectedFile);

  try {
    const response = await fetch('/predict', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (scanningOverlay) scanningOverlay.classList.remove('active');
    if (analyzeBtn) analyzeBtn.disabled = false;

    if (!response.ok || !data.success) {
      if (data.model_loaded === false) {
        showToast(data.error || 'AI Model is not trained yet.', 'warning');
        showModelNotTrainedResult(data.error);
      } else {
        showToast(data.error || 'Unable to analyze image.', 'error');
      }
      return;
    }

    showToast('Classification complete!', 'success');
    showResult(data);
    updateStatistics();

  } catch (err) {
    if (scanningOverlay) scanningOverlay.classList.remove('active');
    if (analyzeBtn) analyzeBtn.disabled = false;
    showToast('Network or server error occurred.', 'error');
    console.error('Prediction Error:', err);
  }
}

function showResult(data) {
  const placeholder = document.getElementById('resultPlaceholder');
  const content = document.getElementById('resultContent');

  if (placeholder) placeholder.style.display = 'none';
  if (!content) return;

  // Set Emoji & Title
  document.getElementById('resEmoji').textContent = data.icon || '♻';
  document.getElementById('resName').textContent = data.name || data.class;

  const catTag = document.getElementById('resCategory');
  catTag.textContent = data.category || 'Unknown';
  catTag.className = `result-category-tag ${data.category === 'Recyclable' ? 'recyclable' : 'general-waste'}`;

  // Confidence
  document.getElementById('resConfidence').textContent = `${data.confidence.toFixed(1)}%`;

  // Confidence level alert banner
  const alertBox = document.getElementById('confidenceAlert');
  if (alertBox) {
    let alertClass = 'high';
    if (data.confidence < 60) alertClass = 'low';
    else if (data.confidence < 80) alertClass = 'moderate';

    alertBox.className = `confidence-alert ${alertClass}`;
    alertBox.innerHTML = `
      <span>● ${data.confidence_level}</span>
      ${data.confidence_tip ? `<span style="font-size:0.8rem; opacity:0.9;">(${data.confidence_tip})</span>` : ''}
    `;
  }

  // Recommended Action
  document.getElementById('resAdvice').textContent = data.advice;

  // Probabilities list
  const probList = document.getElementById('probabilitiesList');
  if (probList && data.scores) {
    probList.innerHTML = '';
    const sortedClasses = Object.keys(data.scores);

    sortedClasses.forEach((cls, idx) => {
      const pct = data.scores[cls];
      const isTop = idx === 0;

      const item = document.createElement('div');
      item.className = 'prob-item';
      item.innerHTML = `
        <div class="prob-meta">
          <span>${cls.charAt(0).toUpperCase() + cls.slice(1)}</span>
          <span>${pct.toFixed(1)}%</span>
        </div>
        <div class="prob-bar-bg">
          <div class="prob-bar-fill ${isTop ? 'top' : ''}" style="width: ${pct}%"></div>
        </div>
      `;
      probList.appendChild(item);
    });
  }

  content.classList.add('active');
}

function showModelNotTrainedResult(errorMsg) {
  const placeholder = document.getElementById('resultPlaceholder');
  const content = document.getElementById('resultContent');

  if (placeholder) placeholder.style.display = 'none';
  if (!content) return;

  content.innerHTML = `
    <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #F59E0B; padding: 24px; border-radius: 14px; text-align: center;">
      <div style="font-size: 2.5rem; margin-bottom: 12px;">⚠️</div>
      <h3 style="color: #F59E0B; font-size: 1.2rem; margin-bottom: 8px;">Model Not Trained Yet</h3>
      <p style="font-size: 0.9rem; color: #6B7D76; margin-bottom: 16px;">
        ${errorMsg || 'Please train the MobileNetV2 model using python train.py before making real waste predictions.'}
      </p>
      <code style="background: #041F17; color: #2DD496; padding: 6px 14px; border-radius: 6px; font-size: 0.85rem;">python train.py</code>
    </div>
  `;
  content.classList.add('active');
}

function hideResult() {
  const placeholder = document.getElementById('resultPlaceholder');
  const content = document.getElementById('resultContent');
  if (placeholder) placeholder.style.display = 'flex';
  if (content) content.classList.remove('active');
}

/* Webcam Camera Module */
async function openCamera() {
  const modal = document.getElementById('cameraModal');
  const video = document.getElementById('cameraVideo');

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showToast('Webcam access is not supported by your browser.', 'error');
    return;
  }

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' }
    });
    video.srcObject = cameraStream;
    modal.classList.add('active');
    showToast('Camera active. Position item inside frame.', 'info');
  } catch (err) {
    console.error('Camera Access Error:', err);
    if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
      showToast('Camera permission denied by user.', 'error');
    } else if (err.name === 'NotFoundError') {
      showToast('No camera device found on this system.', 'error');
    } else {
      showToast('Unable to open camera feed.', 'error');
    }
  }
}

function closeCamera() {
  const modal = document.getElementById('cameraModal');
  const video = document.getElementById('cameraVideo');

  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
    cameraStream = null;
  }
  if (video) video.srcObject = null;
  if (modal) modal.classList.remove('active');
}

function capturePhoto() {
  const video = document.getElementById('cameraVideo');
  if (!video || !cameraStream) return;

  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;

  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  canvas.toBlob((blob) => {
    if (!blob) {
      showToast('Failed to capture snapshot.', 'error');
      return;
    }

    const file = new File([blob], `camera_capture_${Date.now()}.jpg`, { type: 'image/jpeg' });
    closeCamera();
    handleFileSelection(file);
    showToast('Photo captured! Analyzing...', 'info');
    analyzeImage();
  }, 'image/jpeg', 0.92);
}

/* Real-Time Stats Refresher */
async function updateStatistics() {
  try {
    const response = await fetch('/api/stats');
    const data = await response.json();

    if (data.success && data.stats) {
      const stats = data.stats;
      const totalEl = document.getElementById('statTotalScans');
      const recEl = document.getElementById('statRecyclable');
      const genEl = document.getElementById('statGeneralWaste');
      const accEl = document.getElementById('statModelAccuracy');

      if (totalEl) totalEl.textContent = stats.total_scans;
      if (recEl) recEl.textContent = stats.recyclable_count;
      if (genEl) genEl.textContent = stats.general_waste_count;
      if (accEl) {
        if (data.meta && data.meta.val_accuracy) {
          accEl.textContent = `${data.meta.val_accuracy}%`;
        } else {
          accEl.textContent = `${stats.avg_confidence}%`;
        }
      }
    }
  } catch (err) {
    console.warn('Could not update live statistics:', err);
  }
}

/* History Page Handler */
function initHistoryPage() {
  const searchInput = document.getElementById('historySearch');
  const clearBtn = document.getElementById('clearHistoryBtn');

  if (searchInput) {
    searchInput.addEventListener('input', (e) => filterHistoryTable(e.target.value.toLowerCase()));
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
      if (confirm('Are you sure you want to clear all prediction history?')) {
        try {
          const res = await fetch('/api/history/clear', { method: 'POST' });
          const data = await res.json();
          if (data.success) {
            showToast('History cleared.', 'info');
            location.reload();
          }
        } catch (err) {
          showToast('Failed to clear history.', 'error');
        }
      }
    });
  }
}

function filterHistoryTable(query) {
  const rows = document.querySelectorAll('#historyTableBody tr');
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  });
}

/* Analytics Dashboard Handler */
async function initAnalyticsPage() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();

    if (!data.success || !data.stats) return;
    const stats = data.stats;

    // Render Category Distribution Doughnut Chart
    const ctxCat = document.getElementById('categoryChart').getContext('2d');
    new Chart(ctxCat, {
      type: 'doughnut',
      data: {
        labels: ['Cardboard', 'Glass', 'Metal', 'Paper', 'Plastic', 'Trash'],
        datasets: [{
          data: [
            stats.category_counts.cardboard,
            stats.category_counts.glass,
            stats.category_counts.metal,
            stats.category_counts.paper,
            stats.category_counts.plastic,
            stats.category_counts.trash
          ],
          backgroundColor: ['#D97706', '#2563EB', '#64748B', '#EAB308', '#16A36F', '#EF4444'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });

    // Render Recyclable vs General Bar Chart
    const ctxRec = document.getElementById('recyclableChart').getContext('2d');
    new Chart(ctxRec, {
      type: 'bar',
      data: {
        labels: ['Recyclable', 'General Waste'],
        datasets: [{
          label: 'Total Scanned Items',
          data: [stats.recyclable_count, stats.general_waste_count],
          backgroundColor: ['#16A36F', '#F59E0B'],
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    });

  } catch (err) {
    console.error('Failed to initialize analytics charts:', err);
  }
}
