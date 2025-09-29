import { FieldCanvas } from './components/FieldCanvas';
import { ControlPanel } from './components/ControlPanel';
import './index.css';

function App() {
  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 text-white overflow-hidden">
      {/* Control Panel - Fixed width sidebar */}
      <div className="w-80 bg-gradient-to-b from-gray-800 to-gray-900 border-r border-gray-600 flex-shrink-0 shadow-2xl overflow-hidden">
        <ControlPanel />
      </div>
      
      {/* Main Canvas Area - Takes remaining space */}
      <div className="flex-1 flex flex-col">
        {/* Header Bar */}
        <div className="bg-gradient-to-r from-gray-800 to-gray-700 px-6 py-3 border-b border-gray-600 shadow-lg flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              <h2 className="text-lg font-semibold text-gray-200">Field Visualization</h2>
            </div>
            <div className="flex items-center space-x-4 text-sm text-gray-400">
              <span className="hidden sm:inline">🎯 Interactive Planner</span>
            </div>
          </div>
        </div>

        {/* Canvas Container */}
        <div className="flex-1 p-6 bg-gradient-to-br from-gray-850 to-gray-900 overflow-hidden">
          <div className="w-full h-full flex items-center justify-center relative">
            <FieldCanvas width={800} height={600} />
            {/* Improved Controls Instructions */}
            <div className="absolute top-6 right-6 bg-gray-800/90 backdrop-blur-md border border-gray-600/50 rounded-xl p-4 text-sm text-gray-200 shadow-xl max-w-xs">
              <div className="flex items-center space-x-2 mb-3">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <span className="font-semibold text-blue-300">Controls</span>
              </div>
              <div className="space-y-2 text-xs text-gray-300">
                <div className="flex items-center space-x-2">
                  <span className="text-blue-400">🖱️</span>
                  <span>Drag to pan field</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-400">🔍</span>
                  <span>Scroll to zoom</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-purple-400">👆</span>
                  <span>Click to select items</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-orange-400">⇧</span>
                  <span>Shift = disable snap</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Status bar */}
        <div className="bg-gradient-to-r from-gray-800 to-gray-700 px-6 py-2 border-t border-gray-600 text-sm flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-gray-300 font-medium">FTC Field Viewer</span>
              <span className="text-gray-500 hidden sm:inline">•</span>
              <span className="text-blue-400 hidden sm:inline">Web v1.0</span>
            </div>
            <div className="text-gray-400 text-xs hidden md:block">
              Ready for field planning 🚀
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;