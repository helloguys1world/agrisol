// Shared UI Helpers & Notification System

function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const bgColor = type === 'success' ? 'bg-[#2D5A27] text-white' : (type === 'error' ? 'bg-red-700 text-white' : 'bg-[#8FBC8F] text-[#1C2819]');
  const icon = type === 'success' ? 'fa-check-circle' : (type === 'error' ? 'fa-exclamation-triangle' : 'fa-info-circle');

  toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg transform transition-all duration-300 translate-y-2 opacity-0 ${bgColor} text-sm font-medium z-50`;
  toast.innerHTML = `
    <i class="fas ${icon}"></i>
    <span class="flex-1">${message}</span>
    <button onclick="this.parentElement.remove()" class="text-white/80 hover:text-white ml-2">
      <i class="fas fa-times"></i>
    </button>
  `;

  container.appendChild(toast);

  // Animate in
  setTimeout(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  }, 10);

  // Auto remove after 4.5 seconds
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// Global Pump Controller function
async function updatePlotPump(plotId, status) {
  try {
    const response = await fetch(`/api/plots/${plotId}/pump`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pump_status: status })
    });
    const result = await response.json();
    if (result.success) {
      showToast(result.message, 'success');
      // Update UI button highlights if on dashboard
      const btnGroup = document.getElementById(`pump-btns-${plotId}`);
      if (btnGroup) {
        btnGroup.querySelectorAll('button').forEach(btn => {
          btn.classList.remove('bg-[#2D5A27]', 'text-white', 'shadow-sm');
          btn.classList.add('bg-white', 'text-[#4B5548]');
        });
        const activeBtn = document.getElementById(`pump-${plotId}-${status}`);
        if (activeBtn) {
          activeBtn.classList.add('bg-[#2D5A27]', 'text-white', 'shadow-sm');
          activeBtn.classList.remove('bg-white', 'text-[#4B5548]');
        }
      }
    } else {
      showToast(result.error || 'Failed to update pump status', 'error');
    }
  } catch (err) {
    showToast('Network error while communicating with pump controller', 'error');
  }
}
