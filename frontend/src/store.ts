import { configureStore, createSlice } from '@reduxjs/toolkit';

// Placeholder slice to prevent empty reducer error
const placeholderSlice = createSlice({
  name: 'placeholder',
  initialState: { initialized: true },
  reducers: {
    setInitialized: (state, action) => {
      state.initialized = action.payload;
    },
  },
});

// This is a placeholder store setup
// Individual slices will be added in future phases
export const store = configureStore({
  reducer: {
    placeholder: placeholderSlice.reducer,
    // portfolio: portfolioSlice.reducer,
    // marketData: marketDataSlice.reducer,
    // analytics: analyticsSlice.reducer,
    // optimization: optimizationSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
