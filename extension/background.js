// Email AI Categorizer Background Script
// Handles background tasks and extension lifecycle

console.log('Email AI Categorizer: Background script loaded');

// Extension installation
chrome.runtime.onInstalled.addListener((details) => {
  console.log('Email AI Categorizer: Extension installed/updated');

  if (details.reason === 'install') {
    // First time installation
    initializeExtension();
  } else if (details.reason === 'update') {
    // Extension update
    handleUpdate();
  }
});

// Initialize extension settings
function initializeExtension() {
  console.log('Email AI Categorizer: Initializing extension');

  // Set default settings
  const defaultSettings = {
    enabled: true,
    stats: {
      processed: 0,
      categorized: 0,
      lastReset: Date.now()
    },
    categories: [
      'Work',
      'Personal',
      'Important',
      'Spam',
      'Newsletters',
      'Social',
      'Finance',
      'Shopping'
    ]
  };

  chrome.storage.local.set(defaultSettings, () => {
    console.log('Email AI Categorizer: Default settings initialized');
  });
}

// Handle extension updates
function handleUpdate() {
  console.log('Email AI Categorizer: Handling update');

  // Check for breaking changes and migrate settings if needed
  chrome.storage.local.get(null, (result) => {
    // Migrate old settings to new format if necessary
    // Add migration logic here as the extension evolves
  });
}

// Handle tab updates (when user navigates to Gmail)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes('mail.google.com')) {
    console.log('Email AI Categorizer: Gmail tab loaded');

    // Inject content script if not already injected
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content.js']
    }).catch((error) => {
      console.error('Error injecting content script:', error);
    });
  }
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Email AI Categorizer: Received message:', message);

  if (message.action === 'categorizeEmail') {
    handleCategorizationRequest(message.data, sendResponse);
    return true; // Keep message channel open for async response
  }

  if (message.action === 'getSettings') {
    chrome.storage.local.get(null, (result) => {
      sendResponse(result);
    });
    return true;
  }

  if (message.action === 'updateStats') {
    updateStats(message.stats, sendResponse);
    return true;
  }
});

// Handle categorization requests from content script
async function handleCategorizationRequest(emailData, sendResponse) {
  try {
    // Get backend URL from settings
    const result = await chrome.storage.local.get(['backendUrl']);
    const backendUrl = result.backendUrl || 'https://email-ai-categorizer.vercel.app';

    // Send request to backend
    const response = await fetch(`${backendUrl}/categorize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(emailData)
    });

    if (response.ok) {
      const result = await response.json();
      sendResponse({ success: true, category: result.category });
    } else {
      console.error('Backend categorization failed:', response.status);
      sendResponse({ success: false, error: 'Backend request failed' });
    }
  } catch (error) {
    console.error('Error in categorization request:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// Update statistics
function updateStats(newStats, sendResponse) {
  chrome.storage.local.get(['stats'], (result) => {
    const currentStats = result.stats || { processed: 0, categorized: 0 };
    const updatedStats = {
      processed: currentStats.processed + (newStats.processed || 0),
      categorized: currentStats.categorized + (newStats.categorized || 0),
      lastUpdated: Date.now()
    };

    chrome.storage.local.set({ stats: updatedStats }, () => {
      sendResponse({ success: true, stats: updatedStats });
    });
  });
}

// Handle extension icon click (if no popup is set)
chrome.action.onClicked.addListener((tab) => {
  // This will only be called if no popup is defined
  console.log('Extension icon clicked');
});

// Periodic cleanup (reset stats monthly)
function scheduleCleanup() {
  setInterval(() => {
    chrome.storage.local.get(['stats'], (result) => {
      const stats = result.stats;
      if (stats && stats.lastReset) {
        const daysSinceReset = (Date.now() - stats.lastReset) / (1000 * 60 * 60 * 24);
        if (daysSinceReset > 30) { // Reset monthly
          chrome.storage.local.set({
            stats: {
              processed: 0,
              categorized: 0,
              lastReset: Date.now()
            }
          });
          console.log('Email AI Categorizer: Monthly stats reset');
        }
      }
    });
  }, 24 * 60 * 60 * 1000); // Check daily
}

// Start cleanup scheduler
scheduleCleanup();

// Handle extension suspension
chrome.runtime.onSuspend.addListener(() => {
  console.log('Email AI Categorizer: Extension suspending');
});
