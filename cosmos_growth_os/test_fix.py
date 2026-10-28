import subprocess
import os

test_js = """
const fs = require('fs');
let jsCode = fs.readFileSync('C:/Users/nikhil/Downloads/MoneyPrinterTurbo-Portable-Windows-1.3.9/cosmos_growth_os/frontend/js/app.js', 'utf8');

// Cut the initialization block from top
const initBlock = `  // Load Initial Data
  fetchHealth();
  fetchYouTubeData();
  fetchCuratedTopics();
  fetchCategories();
  fetchPromptTemplates();
  fetchJobs();
  fetchMonetization();
  fetchBestPostingTimes();
  fetchCalendarEvents();
  fetchGrowthDiagnostics();
  fetchMilestoneRoadmap();
  initPipelineTracker();

  // Setup Event Listeners
  setupEventListeners();
  setupGrowthEventListeners();
  setupWinningTopicListeners();
  setupManualScriptController();
  setupTabVisibilityAnimation();`;

jsCode = jsCode.replace(initBlock, '  // Initialization deferred to end of file');

// Paste it right before the closing of DOMContentLoaded
jsCode = jsCode.replace('  // Toast Notification System', `${initBlock}\\n\\n  // Toast Notification System`);

const listeners = [];
global.window = global;
global.setInterval = () => {};
global.setTimeout = () => {};
global.document = {
  addEventListener: (event, cb) => {
    if (event === 'DOMContentLoaded') {
      try {
        console.log('Starting DOMContentLoaded execution...');
        cb();
        console.log('DOMContentLoaded execution COMPLETED successfully with ZERO errors!');
      } catch (err) {
        console.error('Error during DOMContentLoaded:', err);
      }
    }
  },
  documentElement: { setAttribute: () => {} },
  getElementById: (id) => {
    return {
      id,
      addEventListener: (type, fn) => { listeners.push({ id, type }); },
      classList: { add: () => {}, remove: () => {}, toggle: () => {} },
      style: {},
      setAttribute: () => {},
      getAttribute: () => '',
      options: [{ getAttribute: () => '' }],
      selectedIndex: 0,
      value: ''
    };
  },
  querySelectorAll: (sel) => [
    {
      addEventListener: (type, fn) => { listeners.push({ sel, type }); },
      classList: { add: () => {}, remove: () => {} },
      getAttribute: () => ''
    }
  ]
};
global.localStorage = { getItem: () => null, setItem: () => {} };
global.fetch = (url) => {
  return Promise.resolve({ ok: true, json: () => Promise.resolve({
    subscribers: { current: 49, target: 1000, remaining: 951, progress_pct: 4.9 },
    shorts_views: { current: 11340, target: 10000000, remaining: 9988660, progress_pct: 0.11 }
  })});
};

eval(jsCode);
console.log('Total listeners registered:', listeners.length);
"""

with open('test_runner.js', 'w', encoding='utf-8') as f:
    f.write(test_js)

res = subprocess.run(['node', 'test_runner.js'], capture_output=True, text=True)
print('STDOUT:\n', res.stdout)
print('STDERR:\n', res.stderr)

if os.path.exists('test_runner.js'):
    os.remove('test_runner.js')
if os.path.exists('test_fix.py'):
    os.remove('test_fix.py')
