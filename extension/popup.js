// Email AI Categorizer Popup Script

document.addEventListener('DOMContentLoaded', function() {
  // Get DOM elements
  const enableBtn = document.getElementById('enableBtn');
  const disableBtn = document.getElementById('disableBtn');
  const settingsBtn = document.getElementById('settingsBtn');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const emailsProcessed = document.getElementById('emailsProcessed');
  const categoriesApplied = document.getElementById('categoriesApplied');

  // Initialize popup
  initializePopup();

  // Event listeners
  enableBtn.addEventListener('click', enableCategorization);
  disableBtn.addEventListener('click', disableCategorization);
  settingsBtn.addEventListener('click', openSettings);

  async function initializePopup() {
    try {
      // Get current status from storage
      const result = await chrome.storage.local.get(['enabled', 'stats']);
      const isEnabled = result.enabled !== false; // Default to true

      updateStatus(isEnabled);
      updateStats(result.stats || { processed: 0, categorized: 0 });

    } catch (error) {
      console.error('Error initializing popup:', error);
      updateStatus(false);
    }
  }

  function updateStatus(enabled) {
    if (enabled) {
      statusDot.className = 'status-dot status-active';
      statusText.textContent = 'Active';
      enableBtn.disabled = true;
      disableBtn.disabled = false;
    } else {
      statusDot.className = 'status-dot status-inactive';
      statusText.textContent = 'Inactive';
      enableBtn.disabled = false;
      disableBtn.disabled = true;
    }
  }

  function updateStats(stats) {
    emailsProcessed.textContent = stats.processed || 0;
    categoriesApplied.textContent = stats.categorized || 0;
  }

  async function enableCategorization() {
    try {
      await chrome.storage.local.set({ enabled: true });
      updateStatus(true);

      // Send message to content script
      const tabs = await chrome.tabs.query({ url: 'https://mail.google.com/*' });
      tabs.forEach(tab => {
        chrome.tabs.sendMessage(tab.id, { action: 'enableCategorization' });
      });

    } catch (error) {
      console.error('Error enabling categorization:', error);
    }
  }

  async function disableCategorization() {
    try {
      await chrome.storage.local.set({ enabled: false });
      updateStatus(false);

      // Send message to content script
      const tabs = await chrome.tabs.query({ url: 'https://mail.google.com/*' });
      tabs.forEach(tab => {
        chrome.tabs.sendMessage(tab.id, { action: 'disableCategorization' });
      });

    } catch (error) {
      console.error('Error disabling categorization:', error);
    }
  }

  function openSettings() {
    // Open settings page (to be implemented)
    console.log('Settings button clicked');
  }

  // Listen for updates from content script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'statsUpdate') {
      updateStats(message.stats);
    }
  });
});
