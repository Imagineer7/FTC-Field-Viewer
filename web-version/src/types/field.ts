// Core data structures for FTC Field Viewer

export interface Point {
  id: string;
  name: string;
  x: number; // Field coordinates in inches
  y: number; // Field coordinates in inches
  color: string; // Hex color
}

export interface Vector {
  id: string;
  name: string;
  x: number; // Start position in inches
  y: number; // Start position in inches
  magnitude: number; // Length in inches
  direction: number; // Angle in degrees (0° = positive X axis)
  color: string; // Hex color
}

export interface FieldConfig {
  fieldSizeInches: number;
  backgroundImage?: string;
  points: Point[];
  vectors: Vector[];
  gridOpacity: number;
  showLabels: boolean;
}

export interface ViewState {
  zoom: number;
  panX: number;
  panY: number;
  selectedPointId: string | null;
  selectedVectorId: string | null;
  cursorFieldPos: { x: number; y: number };
  isShiftPressed: boolean;
}

export interface GridSettings {
  baseSpacing: number; // Base grid spacing in inches (23.5 for FTC tiles)
  opacity: number;
  color: string;
}

// Default field configuration based on current Python implementation
export const DEFAULT_FIELD_CONFIG: FieldConfig = {
  fieldSizeInches: 141.0,
  points: [
    {
      id: 'red-goal',
      name: 'Red Goal (ID 24)',
      x: -58.3727,
      y: 55.6425,
      color: '#ff4d4d'
    },
    {
      id: 'blue-goal', 
      name: 'Blue Goal (ID 20)',
      x: -58.3727,
      y: -55.6425,
      color: '#4da6ff'
    }
  ],
  vectors: [],
  gridOpacity: 0.5,
  showLabels: true
};

export const DEFAULT_GRID_SETTINGS: GridSettings = {
  baseSpacing: 23.5, // FTC tile size
  opacity: 0.5,
  color: '#00bcff'
};

// Utility functions for coordinate conversion
export const fieldToCanvas = (
  fieldX: number, 
  fieldY: number, 
  canvasWidth: number, 
  canvasHeight: number, 
  fieldSize: number,
  zoom: number,
  panX: number,
  panY: number
): { x: number; y: number } => {
  // Convert field coordinates (inches, center origin) to canvas coordinates (pixels, top-left origin)
  const scale = Math.min(canvasWidth, canvasHeight) / fieldSize * zoom;
  const centerX = canvasWidth / 2 + panX;
  const centerY = canvasHeight / 2 + panY;
  
  return {
    x: centerX + fieldX * scale,
    y: centerY - fieldY * scale // Flip Y axis
  };
};

export const canvasToField = (
  canvasX: number,
  canvasY: number,
  canvasWidth: number,
  canvasHeight: number,
  fieldSize: number,
  zoom: number,
  panX: number,
  panY: number
): { x: number; y: number } => {
  // Convert canvas coordinates to field coordinates
  const scale = Math.min(canvasWidth, canvasHeight) / fieldSize * zoom;
  const centerX = canvasWidth / 2 + panX;
  const centerY = canvasHeight / 2 + panY;
  
  return {
    x: (canvasX - centerX) / scale,
    y: -(canvasY - centerY) / scale // Flip Y axis
  };
};

export const snapToGrid = (x: number, y: number, gridSpacing: number): { x: number; y: number } => {
  return {
    x: Math.round(x / gridSpacing) * gridSpacing,
    y: Math.round(y / gridSpacing) * gridSpacing
  };
};

// Generate unique IDs
export const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9);
};