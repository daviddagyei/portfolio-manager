import { configureStore } from '@reduxjs/toolkit';

// This is a placeholder store setup
// Individual slices will be added in future phases
export const store = configureStore({
  reducer: {
    // portfolio: portfolioSlice.reducer,
    // marketData: marketDataSlice.reducer,
    // analytics: analyticsSlice.reducer,
    // optimization: optimizationSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
