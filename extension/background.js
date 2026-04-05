// Service worker: open the side panel when the toolbar icon is clicked.
// This is the entire background logic — everything else happens in the panel.

chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((err) => console.error('Vibenote: failed to set panel behavior', err));
