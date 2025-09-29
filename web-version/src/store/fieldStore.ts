import { create } from 'zustand';
import { 
  Point, 
  Vector, 
  FieldConfig, 
  ViewState, 
  DEFAULT_FIELD_CONFIG
} from '../types/field';

interface FieldStore extends FieldConfig, ViewState {
  // Actions for points
  addPoint: (point: Point) => void;
  updatePoint: (id: string, updates: Partial<Point>) => void;
  removePoint: (id: string) => void;
  selectPoint: (id: string | null) => void;
  
  // Actions for vectors
  addVector: (vector: Vector) => void;
  updateVector: (id: string, updates: Partial<Vector>) => void;
  removeVector: (id: string) => void;
  selectVector: (id: string | null) => void;
  
  // Actions for view state
  setZoom: (zoom: number) => void;
  setPan: (panX: number, panY: number) => void;
  setCursorPos: (x: number, y: number) => void;
  setShiftPressed: (pressed: boolean) => void;
  
  // Actions for field config
  setGridOpacity: (opacity: number) => void;
  setShowLabels: (show: boolean) => void;
  
  // Utility actions
  exportConfig: () => FieldConfig;
  importConfig: (config: FieldConfig) => void;
  exportData: () => string;
  importData: (data: string) => void;
  clearAll: () => void;
  reset: () => void;
}

export const useFieldStore = create<FieldStore>((set, get) => ({
  // Initial state from defaults
  ...DEFAULT_FIELD_CONFIG,
  
  // Initial view state
  zoom: 1.0,
  panX: 0,
  panY: 0,
  selectedPointId: null,
  selectedVectorId: null,
  cursorFieldPos: { x: 0, y: 0 },
  isShiftPressed: false,
  
  // Point actions
  addPoint: (point) => set((state) => ({
    points: [...state.points, point]
  })),
  
  updatePoint: (id, updates) => set((state) => ({
    points: state.points.map(p => p.id === id ? { ...p, ...updates } : p)
  })),
  
  removePoint: (id) => set((state) => ({
    points: state.points.filter(p => p.id !== id),
    selectedPointId: state.selectedPointId === id ? null : state.selectedPointId
  })),
  
  selectPoint: (id) => set({ selectedPointId: id, selectedVectorId: null }),
  
  // Vector actions
  addVector: (vector) => set((state) => ({
    vectors: [...state.vectors, vector]
  })),
  
  updateVector: (id, updates) => set((state) => ({
    vectors: state.vectors.map(v => v.id === id ? { ...v, ...updates } : v)
  })),
  
  removeVector: (id) => set((state) => ({
    vectors: state.vectors.filter(v => v.id !== id),
    selectedVectorId: state.selectedVectorId === id ? null : state.selectedVectorId
  })),
  
  selectVector: (id) => set({ selectedVectorId: id, selectedPointId: null }),
  
  // View actions
  setZoom: (zoom) => set({ zoom: Math.max(0.1, Math.min(20, zoom)) }),
  
  setPan: (panX, panY) => set({ panX, panY }),
  
  setCursorPos: (x, y) => set({ cursorFieldPos: { x, y } }),
  
  setShiftPressed: (pressed) => set({ isShiftPressed: pressed }),
  
  // Config actions
  setGridOpacity: (opacity) => set({ gridOpacity: Math.max(0.05, Math.min(1.0, opacity)) }),
  
  setShowLabels: (show) => set({ showLabels: show }),
  
  // Utility actions
  exportConfig: () => {
    const state = get();
    return {
      fieldSizeInches: state.fieldSizeInches,
      backgroundImage: state.backgroundImage,
      points: state.points,
      vectors: state.vectors,
      gridOpacity: state.gridOpacity,
      showLabels: state.showLabels
    };
  },
  
  importConfig: (config) => set((state) => ({
    ...state,
    ...config,
    selectedPointId: null,
    selectedVectorId: null
  })),

  exportData: () => {
    const state = get();
    return JSON.stringify({
      points: state.points,
      vectors: state.vectors,
      fieldSizeInches: state.fieldSizeInches,
      gridOpacity: state.gridOpacity,
      showLabels: state.showLabels
    }, null, 2);
  },

  importData: (jsonData) => {
    try {
      const data = JSON.parse(jsonData);
      set((state) => ({
        ...state,
        points: data.points || [],
        vectors: data.vectors || [],
        fieldSizeInches: data.fieldSizeInches || state.fieldSizeInches,
        gridOpacity: data.gridOpacity !== undefined ? data.gridOpacity : state.gridOpacity,
        showLabels: data.showLabels !== undefined ? data.showLabels : state.showLabels,
        selectedPointId: null,
        selectedVectorId: null
      }));
    } catch (error) {
      throw new Error('Invalid JSON data');
    }
  },

  clearAll: () => set({
    points: [],
    vectors: [],
    selectedPointId: null,
    selectedVectorId: null
  }),
  
  reset: () => set(() => ({
    ...DEFAULT_FIELD_CONFIG,
    zoom: 1.0,
    panX: 0,
    panY: 0,
    selectedPointId: null,
    selectedVectorId: null,
    cursorFieldPos: { x: 0, y: 0 },
    isShiftPressed: false
  }))
}));