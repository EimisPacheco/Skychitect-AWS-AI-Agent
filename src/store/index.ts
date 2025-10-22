import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { 
  Architecture, 
  DiagramNode, 
  DiagramEdge, 
  HistoryEntry, 
  UserPreferences,
  ViewportState,
  DragState,
  AppError
} from '../types';

// Architecture Store
interface ArchitectureStore {
  // State
  current: Architecture | null;
  list: Architecture[];
  history: HistoryEntry[];
  historyIndex: number;
  loading: boolean;
  error: string | null;
  unsavedChanges: boolean;
  
  // Actions
  setCurrentArchitecture: (architecture: Architecture | null) => void;
  updateArchitecture: (updates: Partial<Architecture>) => void;
  addArchitecture: (architecture: Architecture) => void;
  removeArchitecture: (id: string) => void;
  duplicateArchitecture: (id: string) => void;
  
  // Diagram actions
  addNode: (node: DiagramNode) => void;
  updateNode: (id: string, updates: Partial<DiagramNode>) => void;
  removeNode: (id: string) => void;
  addEdge: (edge: DiagramEdge) => void;
  removeEdge: (id: string) => void;
  
  // History actions
  pushToHistory: (action: string, data: any, description: string) => void;
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
  clearHistory: () => void;
  
  // Utility actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  markSaved: () => void;
  markUnsaved: () => void;
}

export const useArchitectureStore = create<ArchitectureStore>()(
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        // Initial state
        current: null,
        list: [],
        history: [],
        historyIndex: -1,
        loading: false,
        error: null,
        unsavedChanges: false,

        // Architecture actions
        setCurrentArchitecture: (architecture) =>
          set((state) => {
            state.current = architecture;
            state.unsavedChanges = false;
          }),

        updateArchitecture: (updates) =>
          set((state) => {
            if (state.current) {
              Object.assign(state.current, updates);
              state.current.metadata.lastModified = new Date().toISOString();
              state.unsavedChanges = true;
            }
          }),

        addArchitecture: (architecture) =>
          set((state) => {
            state.list.push(architecture);
          }),

        removeArchitecture: (id) =>
          set((state) => {
            state.list = state.list.filter(arch => arch.id !== id);
            if (state.current?.id === id) {
              state.current = null;
            }
          }),

        duplicateArchitecture: (id) =>
          set((state) => {
            const original = state.list.find(arch => arch.id === id);
            if (original) {
              const duplicate: Architecture = {
                ...original,
                id: `${original.id}-copy-${Date.now()}`,
                name: `${original.name} (Copy)`,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
              };
              state.list.push(duplicate);
            }
          }),

        // Diagram actions
        addNode: (node) =>
          set((state) => {
            if (state.current) {
              state.current.diagram.nodes.push(node);
              state.unsavedChanges = true;
              get().pushToHistory('add_node', node, `Added node: ${node.label}`);
            }
          }),

        updateNode: (id, updates) =>
          set((state) => {
            if (state.current) {
              const nodeIndex = state.current.diagram.nodes.findIndex(n => n.id === id);
              if (nodeIndex >= 0) {
                Object.assign(state.current.diagram.nodes[nodeIndex], updates);
                state.unsavedChanges = true;
                get().pushToHistory('update_node', { id, updates }, `Updated node: ${id}`);
              }
            }
          }),

        removeNode: (id) =>
          set((state) => {
            if (state.current) {
              const nodeIndex = state.current.diagram.nodes.findIndex(n => n.id === id);
              if (nodeIndex >= 0) {
                const removedNode = state.current.diagram.nodes.splice(nodeIndex, 1)[0];
                // Remove related edges
                state.current.diagram.edges = state.current.diagram.edges.filter(
                  edge => edge.from !== id && edge.to !== id
                );
                state.unsavedChanges = true;
                get().pushToHistory('remove_node', removedNode, `Removed node: ${removedNode.label}`);
              }
            }
          }),

        addEdge: (edge) =>
          set((state) => {
            if (state.current) {
              state.current.diagram.edges.push(edge);
              state.unsavedChanges = true;
              get().pushToHistory('add_edge', edge, `Added connection: ${edge.from} → ${edge.to}`);
            }
          }),

        removeEdge: (id) =>
          set((state) => {
            if (state.current) {
              const edgeIndex = state.current.diagram.edges.findIndex(e => e.id === id);
              if (edgeIndex >= 0) {
                const removedEdge = state.current.diagram.edges.splice(edgeIndex, 1)[0];
                state.unsavedChanges = true;
                get().pushToHistory('remove_edge', removedEdge, `Removed connection`);
              }
            }
          }),

        // History actions
        pushToHistory: (action, data, description) =>
          set((state) => {
            const entry: HistoryEntry = {
              id: `history-${Date.now()}`,
              timestamp: new Date().toISOString(),
              action,
              data,
              description
            };
            
            // Remove any history entries after current index (for when we undo then do new action)
            state.history = state.history.slice(0, state.historyIndex + 1);
            state.history.push(entry);
            state.historyIndex = state.history.length - 1;
            
            // Limit history size
            if (state.history.length > 50) {
              state.history.shift();
              state.historyIndex--;
            }
          }),

        undo: () => {
          const state = get();
          if (state.canUndo()) {
            set((draft) => {
              draft.historyIndex--;
              // Apply reverse of the action at current index
              // This would need specific implementations for each action type
            });
          }
        },

        redo: () => {
          const state = get();
          if (state.canRedo()) {
            set((draft) => {
              draft.historyIndex++;
              // Apply the action at current index
              // This would need specific implementations for each action type
            });
          }
        },

        canUndo: () => get().historyIndex >= 0,
        canRedo: () => get().historyIndex < get().history.length - 1,

        clearHistory: () =>
          set((state) => {
            state.history = [];
            state.historyIndex = -1;
          }),

        // Utility actions
        setLoading: (loading) =>
          set((state) => {
            state.loading = loading;
          }),

        setError: (error) =>
          set((state) => {
            state.error = error;
          }),

        markSaved: () =>
          set((state) => {
            state.unsavedChanges = false;
          }),

        markUnsaved: () =>
          set((state) => {
            state.unsavedChanges = true;
          })
      }))
    ),
    { name: 'architecture-store' }
  )
);

// UI Store
interface UIStore {
  // State
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  fullscreenMode: boolean;
  activeTab: string;
  selectedNodes: string[];
  dragState: DragState;
  viewport: ViewportState;
  showGrid: boolean;
  snapToGrid: boolean;
  
  // Actions
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setFullscreenMode: (fullscreen: boolean) => void;
  setActiveTab: (tab: string) => void;
  setSelectedNodes: (nodeIds: string[]) => void;
  addSelectedNode: (nodeId: string) => void;
  removeSelectedNode: (nodeId: string) => void;
  clearSelection: () => void;
  setDragState: (dragState: Partial<DragState>) => void;
  setViewport: (viewport: Partial<ViewportState>) => void;
  resetViewport: () => void;
  toggleGrid: () => void;
  toggleSnapToGrid: () => void;
}

export const useUIStore = create<UIStore>()(
  devtools(
    immer((set, get) => ({
      // Initial state
      theme: 'dark',
      sidebarOpen: true,
      fullscreenMode: false,
      activeTab: 'resources',
      selectedNodes: [],
      dragState: {
        isDragging: false,
        nodeId: null,
        offset: { x: 0, y: 0 },
        startPosition: { x: 0, y: 0 }
      },
      viewport: {
        zoom: 1,
        pan: { x: 0, y: 0 },
        bounds: { x: 0, y: 0, width: 800, height: 600 }
      },
      showGrid: true,
      snapToGrid: false,

      // Actions
      setTheme: (theme) =>
        set((state) => {
          state.theme = theme;
        }),

      toggleSidebar: () =>
        set((state) => {
          state.sidebarOpen = !state.sidebarOpen;
        }),

      setSidebarOpen: (open) =>
        set((state) => {
          state.sidebarOpen = open;
        }),

      setFullscreenMode: (fullscreen) =>
        set((state) => {
          state.fullscreenMode = fullscreen;
        }),

      setActiveTab: (tab) =>
        set((state) => {
          state.activeTab = tab;
        }),

      setSelectedNodes: (nodeIds) =>
        set((state) => {
          state.selectedNodes = nodeIds;
        }),

      addSelectedNode: (nodeId) =>
        set((state) => {
          if (!state.selectedNodes.includes(nodeId)) {
            state.selectedNodes.push(nodeId);
          }
        }),

      removeSelectedNode: (nodeId) =>
        set((state) => {
          state.selectedNodes = state.selectedNodes.filter(id => id !== nodeId);
        }),

      clearSelection: () =>
        set((state) => {
          state.selectedNodes = [];
        }),

      setDragState: (dragState) =>
        set((state) => {
          Object.assign(state.dragState, dragState);
        }),

      setViewport: (viewport) =>
        set((state) => {
          Object.assign(state.viewport, viewport);
        }),

      resetViewport: () =>
        set((state) => {
          state.viewport = {
            zoom: 1,
            pan: { x: 0, y: 0 },
            bounds: { x: 0, y: 0, width: 800, height: 600 }
          };
        }),

      toggleGrid: () =>
        set((state) => {
          state.showGrid = !state.showGrid;
        }),

      toggleSnapToGrid: () =>
        set((state) => {
          state.snapToGrid = !state.snapToGrid;
        })
    })),
    { name: 'ui-store' }
  )
);

// Performance Store
interface PerformanceStore {
  metrics: {
    renderTime: number;
    fps: number;
    nodeCount: number;
    edgeCount: number;
  };
  optimizations: {
    useVirtualization: boolean;
    debounceInterval: number;
    maxRenderNodes: number;
  };
  
  updateMetrics: (metrics: Partial<PerformanceStore['metrics']>) => void;
  setOptimizations: (optimizations: Partial<PerformanceStore['optimizations']>) => void;
}

export const usePerformanceStore = create<PerformanceStore>()(
  devtools(
    immer((set) => ({
      metrics: {
        renderTime: 0,
        fps: 0,
        nodeCount: 0,
        edgeCount: 0
      },
      optimizations: {
        useVirtualization: true,
        debounceInterval: 16,
        maxRenderNodes: 100
      },

      updateMetrics: (metrics) =>
        set((state) => {
          Object.assign(state.metrics, metrics);
        }),

      setOptimizations: (optimizations) =>
        set((state) => {
          Object.assign(state.optimizations, optimizations);
        })
    })),
    { name: 'performance-store' }
  )
);

// Error Store
interface ErrorStore {
  errors: AppError[];
  
  addError: (error: AppError) => void;
  removeError: (id: string) => void;
  clearErrors: () => void;
}

export const useErrorStore = create<ErrorStore>()(
  devtools(
    immer((set) => ({
      errors: [],

      addError: (error) =>
        set((state) => {
          state.errors.push(error);
        }),

      removeError: (id) =>
        set((state) => {
          state.errors = state.errors.filter(error => error.code !== id);
        }),

      clearErrors: () =>
        set((state) => {
          state.errors = [];
        })
    })),
    { name: 'error-store' }
  )
);

// Preferences Store
interface PreferencesStore {
  preferences: UserPreferences;
  
  updatePreferences: (updates: Partial<UserPreferences>) => void;
  resetPreferences: () => void;
}

const defaultPreferences: UserPreferences = {
  optimizationPreference: 'balanced',
  defaultProvider: 'aws',
  currency: 'USD',
  notifications: {
    costAlerts: true,
    performanceAlerts: true,
    securityAlerts: true,
    maintenanceUpdates: false
  },
  ui: {
    theme: 'dark',
    compactMode: false,
    showGrid: true,
    snapToGrid: false,
    autoSave: true,
    animationsEnabled: true
  }
};

export const usePreferencesStore = create<PreferencesStore>()(
  devtools(
    immer((set) => ({
      preferences: defaultPreferences,

      updatePreferences: (updates) =>
        set((state) => {
          Object.assign(state.preferences, updates);
        }),

      resetPreferences: () =>
        set((state) => {
          state.preferences = { ...defaultPreferences };
        })
    })),
    { name: 'preferences-store' }
  )
);