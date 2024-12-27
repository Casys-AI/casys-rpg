# Qwik Routing and Actions Documentation

## Route Structure

```
frontend/src/routes/
├── game/
│   ├── layout.tsx    # Game-specific layout
│   ├── index.tsx     # Game initialization route
│   └── read/         # Game reading interface
├── layout.tsx        # Global layout
└── index.tsx         # Main entry point
```

## Game Initialization Flow

### Problem Solved
We encountered an issue with Qwik's optimizer where the error "_vite_ssr_import_0__.actionQrl is not a function" was appearing. The solution was to use `routeLoader$` instead of trying to handle the action directly.

### Solution
Instead of using actions for initialization, we switched to using `routeLoader$` which is better suited for our use case and works correctly with Qwik's optimizer.

```tsx
// ❌ Don't use action$ or routeAction$
export const useInitGame = action$(async (_, { cookie }) => {
  // This will cause optimizer errors
});

// ✅ Use routeLoader$ instead
export const useGameState = routeLoader$(async ({ cookie }) => {
  // This works correctly with Qwik's optimizer
  // and handles the initialization flow properly
});
```

### Key Points
1. **Qwik Optimizer**
   - The optimizer is strict about how data loading is handled
   - `routeLoader$` is more appropriate for initialization logic
   - Prevents optimization errors at build time

2. **Route Loading**
   - Use `routeLoader$` for route initialization
   - Better handling of initial state
   - More reliable than action-based approaches

### Best Practices
1. Use `routeLoader$` for initialization and data loading
2. Keep initialization logic in route files
3. Let Qwik City handle the loading lifecycle

### Next Steps
1. Review other initialization patterns
2. Document this pattern for future development
3. Consider using loaders for similar cases
