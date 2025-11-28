// Email AI Categorizer Content Script
// This script runs on Gmail pages and handles email processing

let isEnabled = false;
let inboxSDK = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeExtension);

async function initializeExtension() {
  console.log('Email AI Categorizer: Initializing...');

  try {
    // Load InboxSDK
    if (typeof InboxSDK !== 'undefined') {
      inboxSDK = InboxSDK.load(2, 'sdk_email-ai-categorizer_123456789');
      console.log('Email AI Categorizer: InboxSDK loaded');

      // Set up email listeners
      setupEmailListeners();

      // Check if extension is enabled
      const result = await chrome.storage.local.get(['enabled']);
      isEnabled = result.enabled !== false; // Default to true

      if (isEnabled) {
        startCategorization();
      }
    } else {
      console.error('Email AI Categorizer: InboxSDK not loaded');
    }
  } catch (error) {
    console.error('Email AI Categorizer: Initialization error:', error);
  }
}

// Set up listeners for new emails
function setupEmailListeners() {
  if (!inboxSDK) return;

  // Listen for new emails in inbox
  inboxSDK.Lists.registerThreadRowViewHandler((threadRowView) => {
    if (isEnabled) {
      processThreadRow(threadRowView);
    }
  });

  // Listen for opened email threads
  inboxSDK.Conversations.registerMessageViewHandler((messageView) => {
    if (isEnabled) {
      processMessageView(messageView);
    }
  });
}

// Start automatic categorization
function startCategorization() {
  console.log('Email AI Categorizer: Starting categorization');

  // Process existing threads
  setTimeout(() => {
    processExistingThreads();
  }, 2000); // Wait for Gmail to fully load
}

// Stop categorization
function stopCategorization() {
  console.log('Email AI Categorizer: Stopping categorization');
  isEnabled = false;
}

// Process a thread row (list view)
async function processThreadRow(threadRowView) {
  try {
    const threadData = await extractThreadData(threadRowView);

    if (threadData && !isAlreadyCategorized(threadData)) {
      const category = await getCategoryFromAI(threadData);

      if (category) {
        applyCategory(threadRowView, category);
        updateStats();
      }
    }
  } catch (error) {
    console.error('Error processing thread row:', error);
  }
}

// Process a message view (opened email)
async function processMessageView(messageView) {
  try {
    const messageData = await extractMessageData(messageView);

    if (messageData && !isAlreadyCategorized(messageData)) {
      const category = await getCategoryFromAI(messageData);

      if (category) {
        applyCategoryToMessage(messageView, category);
        updateStats();
      }
    }
  } catch (error) {
    console.error('Error processing message view:', error);
  }
}

// Extract data from thread row
async function extractThreadData(threadRowView) {
  try {
    const subject = threadRowView.getSubject();
    const sender = threadRowView.getContacts()[0]?.emailAddress || '';
    const snippet = threadRowView.getSnippet();

    return {
      subject,
      sender,
      snippet,
      type: 'thread'
    };
  } catch (error) {
    console.error('Error extracting thread data:', error);
    return null;
  }
}

// Extract data from message view
async function extractMessageData(messageView) {
  try {
    const subject = messageView.getSubject();
    const sender = messageView.getSender().emailAddress;
    const body = await messageView.getBodyElement();

    return {
      subject,
      sender,
      body: body ? body.textContent : '',
      type: 'message'
    };
  } catch (error) {
    console.error('Error extracting message data:', error);
    return null;
  }
}

// Check if email is already categorized
function isAlreadyCategorized(data) {
  // Check for existing labels/categories
  // This is a simplified check - you might want to implement more sophisticated logic
  return false;
}

// Get category from AI backend
async function getCategoryFromAI(data) {
  try {
    const response = await fetch('http://localhost:5000/categorize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });

    if (response.ok) {
      const result = await response.json();
      return result.category;
    } else {
      console.error('AI categorization failed:', response.status);
      return null;
    }
  } catch (error) {
    console.error('Error calling AI service:', error);
    return null;
  }
}

// Apply category to thread
function applyCategory(threadRowView, category) {
  try {
    // Add label to thread
    threadRowView.addLabel(category);
    console.log(`Applied category "${category}" to thread: ${threadRowView.getSubject()}`);
  } catch (error) {
    console.error('Error applying category to thread:', error);
  }
}

// Apply category to message
function applyCategoryToMessage(messageView, category) {
  try {
    // Add label to message
    messageView.addLabel(category);
    console.log(`Applied category "${category}" to message: ${messageView.getSubject()}`);
  } catch (error) {
    console.error('Error applying category to message:', error);
  }
}

// Process existing threads on page load
async function processExistingThreads() {
  if (!inboxSDK) return;

  try {
    const threadRowViews = inboxSDK.Lists.getThreadRowViews();
    console.log(`Processing ${threadRowViews.length} existing threads`);

    for (const threadRowView of threadRowViews.slice(0, 10)) { // Limit to first 10 for testing
      if (isEnabled) {
        await processThreadRow(threadRowView);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Rate limiting
      }
    }
  } catch (error) {
    console.error('Error processing existing threads:', error);
  }
}

// Update statistics
async function updateStats() {
  try {
    const result = await chrome.storage.local.get(['stats']);
    const stats = result.stats || { processed: 0, categorized: 0 };

    stats.processed += 1;
    stats.categorized += 1;

    await chrome.storage.local.set({ stats });

    // Notify popup of stats update
    chrome.runtime.sendMessage({ action: 'statsUpdate', stats });
  } catch (error) {
    console.error('Error updating stats:', error);
  }
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'enableCategorization') {
    isEnabled = true;
    startCategorization();
    sendResponse({ success: true });
  } else if (message.action === 'disableCategorization') {
    stopCategorization();
    sendResponse({ success: true });
  }
});
