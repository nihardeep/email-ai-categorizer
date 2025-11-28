// Placeholder for InboxSDK
// Download the actual InboxSDK from https://www.inboxsdk.com/
// and replace this file with the downloaded inboxsdk.js

console.log('InboxSDK placeholder loaded - replace with actual SDK');

// This is a minimal stub to prevent errors
window.InboxSDK = {
  load: function(version, appId) {
    console.warn('Using InboxSDK stub - replace with actual SDK');
    return {
      Lists: {
        registerThreadRowViewHandler: function(callback) {
          console.log('ThreadRowViewHandler registered (stub)');
        },
        getThreadRowViews: function() {
          return [];
        }
      },
      Conversations: {
        registerMessageViewHandler: function(callback) {
          console.log('MessageViewHandler registered (stub)');
        }
      }
    };
  }
};
