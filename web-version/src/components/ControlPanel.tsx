import React, { useState } from 'react';
import { useFieldStore } from '../store/fieldStore';
import { generateId } from '../types/field';

export const ControlPanel: React.FC = () => {
  const {
    points,
    vectors,
    gridOpacity,
    showLabels,
    zoom,
    fieldSizeInches,
    selectedPointId,
    selectedVectorId,
    addPoint,
    addVector,
    removePoint,
    removeVector,
    setGridOpacity,
    setShowLabels,
    clearAll,
    exportData,
    importData
  } = useFieldStore();

  const [showPointDialog, setShowPointDialog] = useState(false);
  const [showVectorDialog, setShowVectorDialog] = useState(false);
  const [newPoint, setNewPoint] = useState({ name: '', x: 0, y: 0, color: '#ff4d4d' });
  const [newVector, setNewVector] = useState({ name: '', x: 0, y: 0, magnitude: 0, direction: 0, color: '#00ff00' });

  const handleAddPoint = () => {
    if (newPoint.name.trim()) {
      addPoint({
        id: generateId(),
        name: newPoint.name.trim(),
        x: newPoint.x,
        y: newPoint.y,
        color: newPoint.color
      });
      setNewPoint({ name: '', x: 0, y: 0, color: '#ff4d4d' });
      setShowPointDialog(false);
    }
  };

  const handleAddVector = () => {
    if (newVector.name.trim()) {
      addVector({
        id: generateId(),
        name: newVector.name.trim(),
        x: newVector.x,
        y: newVector.y,
        magnitude: newVector.magnitude,
        direction: newVector.direction,
        color: newVector.color
      });
      setNewVector({ name: '', x: 0, y: 0, magnitude: 0, direction: 0, color: '#00ff00' });
      setShowVectorDialog(false);
    }
  };

  const handleExport = () => {
    const data = exportData();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'field_data.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = e.target?.result as string;
          importData(data);
        } catch (error) {
          alert('Error importing file: Invalid format');
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-600 p-4">
        <div className="flex items-center space-x-2 mb-1">
          <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
            FTC Field Viewer
          </h1>
        </div>
        <p className="text-sm text-gray-400 ml-4">Web Version • Interactive Field Planning</p>
      </div>

      {/* Main Content Area with improved overflow handling */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
        {/* Field Info */}
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-4 rounded-lg border border-gray-600 shadow-lg">
          <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center">
            <div className="w-1 h-4 bg-blue-400 rounded mr-2"></div>
            Field Information
          </h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-400">Field Size:</span>
              <span className="text-xs font-mono text-blue-300">{fieldSizeInches}″ × {fieldSizeInches}″</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-400">Zoom Level:</span>
              <span className="text-xs font-mono text-green-300">{(zoom * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-400">Elements:</span>
              <span className="text-xs font-mono text-purple-300">{points.length + vectors.length}</span>
            </div>
          </div>
        </div>

        {/* View Controls */}
        <div className="bg-gray-700 p-3 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">View Settings</h3>
          
          <div className="space-y-3">
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={showLabels}
                  onChange={(e) => setShowLabels(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">Show Labels</span>
              </label>
            </div>
            
            <div>
              <label className="text-sm text-gray-300 block mb-1">
                Grid Opacity: {(gridOpacity * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={gridOpacity}
                onChange={(e) => setGridOpacity(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* Points Section */}
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-4 rounded-lg border border-gray-600 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-200 flex items-center">
              <div className="w-1 h-4 bg-purple-400 rounded mr-2"></div>
              Points 
              <span className="ml-1 px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded-full">
                {points.length}
              </span>
            </h3>
            <button
              onClick={() => setShowPointDialog(true)}
              className="bg-blue-600 hover:bg-blue-500 text-white text-xs px-3 py-1.5 rounded-md transition-all duration-200 transform hover:scale-105 hover:shadow-lg hover:shadow-blue-500/25 flex items-center space-x-1"
            >
              <span>+</span><span>Add Point</span>
            </button>
          </div>
          
          <div className="space-y-2 max-h-36 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
            {points.length === 0 ? (
              <div className="text-xs text-gray-500 italic text-center py-4">
                No points added yet
              </div>
            ) : (
              points.map((point) => (
                <div 
                  key={point.id} 
                  className={`flex items-center justify-between text-xs p-2 rounded-md transition-all duration-200 hover:bg-gray-600/50 ${
                    selectedPointId === point.id ? 'bg-purple-500/20 border border-purple-400/30' : 'border border-transparent'
                  }`}
                >
                  <div className="flex items-center space-x-2 flex-1 min-w-0">
                    <div 
                      className="w-3 h-3 rounded-full border border-gray-400 shadow-sm"
                      style={{ backgroundColor: point.color }}
                    />
                    <span className="text-gray-300 truncate font-mono text-xs">{point.name}</span>
                  </div>
                  <button
                    onClick={() => removePoint(point.id)}
                    className="text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded p-1 transition-all duration-200 ml-2"
                    title="Remove point"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Vectors Section */}
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-4 rounded-lg border border-gray-600 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-200 flex items-center">
              <div className="w-1 h-4 bg-green-400 rounded mr-2"></div>
              Vectors 
              <span className="ml-1 px-2 py-0.5 bg-green-500/20 text-green-300 text-xs rounded-full">
                {vectors.length}
              </span>
            </h3>
            <button
              onClick={() => setShowVectorDialog(true)}
              className="bg-green-600 hover:bg-green-500 text-white text-xs px-3 py-1.5 rounded-md transition-all duration-200 transform hover:scale-105 hover:shadow-lg hover:shadow-green-500/25 flex items-center space-x-1"
            >
              <span>→</span><span>Add Vector</span>
            </button>
          </div>
          
          <div className="space-y-2 max-h-36 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
            {vectors.length === 0 ? (
              <div className="text-xs text-gray-500 italic text-center py-4">
                No vectors added yet
              </div>
            ) : (
              vectors.map((vector) => (
                <div 
                  key={vector.id} 
                  className={`flex items-center justify-between text-xs p-2 rounded-md transition-all duration-200 hover:bg-gray-600/50 ${
                    selectedVectorId === vector.id ? 'bg-green-500/20 border border-green-400/30' : 'border border-transparent'
                  }`}
                >
                  <div className="flex items-center space-x-2 flex-1 min-w-0">
                    <div 
                      className="w-3 h-3 rounded border border-gray-400 shadow-sm flex items-center justify-center"
                      style={{ backgroundColor: vector.color }}
                    >
                      <span className="text-white text-[8px]">→</span>
                    </div>
                    <span className="text-gray-300 truncate font-mono text-xs">{vector.name}</span>
                  </div>
                  <button
                    onClick={() => removeVector(vector.id)}
                    className="text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded p-1 transition-all duration-200 ml-2"
                    title="Remove vector"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="bg-gradient-to-br from-gray-700 to-gray-800 p-4 rounded-lg border border-gray-600 shadow-lg">
          <h3 className="text-sm font-semibold text-gray-200 mb-4 flex items-center">
            <div className="w-1 h-4 bg-orange-400 rounded mr-2"></div>
            Actions
          </h3>
          <div className="space-y-3">
            <button
              onClick={handleExport}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white text-sm py-2.5 rounded-lg transition-all duration-200 transform hover:scale-[1.02] hover:shadow-lg hover:shadow-blue-500/25 flex items-center justify-center space-x-2"
            >
              <span>📁</span><span>Export Data</span>
            </button>
            
            <label className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-white text-sm py-2.5 rounded-lg cursor-pointer transition-all duration-200 transform hover:scale-[1.02] hover:shadow-lg hover:shadow-green-500/25 flex items-center justify-center space-x-2">
              <span>📂</span><span>Import Data</span>
              <input
                type="file"
                accept=".json"
                onChange={handleImport}
                className="hidden"
              />
            </label>
            
            <button
              onClick={clearAll}
              className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white text-sm py-2.5 rounded-lg transition-all duration-200 transform hover:scale-[1.02] hover:shadow-lg hover:shadow-red-500/25 flex items-center justify-center space-x-2"
            >
              <span>🗑️</span><span>Clear All</span>
            </button>
          </div>
        </div>
      </div>

      {/* Point Dialog */}
      {showPointDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-80">
            <h3 className="text-lg font-semibold mb-4">Add New Point</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={newPoint.name}
                  onChange={(e) => setNewPoint({ ...newPoint, name: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 select-text"
                  placeholder="Point name"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">X (inches)</label>
                  <input
                    type="number"
                    value={newPoint.x}
                    onChange={(e) => setNewPoint({ ...newPoint, x: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 select-text"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Y (inches)</label>
                  <input
                    type="number"
                    value={newPoint.y}
                    onChange={(e) => setNewPoint({ ...newPoint, y: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 select-text"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Color</label>
                <input
                  type="color"
                  value={newPoint.color}
                  onChange={(e) => setNewPoint({ ...newPoint, color: e.target.value })}
                  className="w-full h-10 bg-gray-700 border border-gray-600 rounded"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowPointDialog(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleAddPoint}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded"
              >
                Add Point
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Vector Dialog */}
      {showVectorDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-80">
            <h3 className="text-lg font-semibold mb-4">Add New Vector</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={newVector.name}
                  onChange={(e) => setNewVector({ ...newVector, name: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 select-text"
                  placeholder="Vector name"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">X (inches)</label>
                  <input
                    type="number"
                    value={newVector.x}
                    onChange={(e) => setNewVector({ ...newVector, x: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 select-text"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Y (inches)</label>
                  <input
                    type="number"
                    value={newVector.y}
                    onChange={(e) => setNewVector({ ...newVector, y: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 select-text"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Magnitude</label>
                  <input
                    type="number"
                    value={newVector.magnitude}
                    onChange={(e) => setNewVector({ ...newVector, magnitude: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 select-text"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Direction (°)</label>
                  <input
                    type="number"
                    value={newVector.direction}
                    onChange={(e) => setNewVector({ ...newVector, direction: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 select-text"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Color</label>
                <input
                  type="color"
                  value={newVector.color}
                  onChange={(e) => setNewVector({ ...newVector, color: e.target.value })}
                  className="w-full h-10 bg-gray-700 border border-gray-600 rounded"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowVectorDialog(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleAddVector}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded"
              >
                Add Vector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};