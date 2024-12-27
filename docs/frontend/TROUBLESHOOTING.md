# Frontend Troubleshooting Guide

Ce guide répertorie les erreurs courantes rencontrées lors du développement frontend et leurs solutions.

## Erreurs Qwik Courantes

### 1. Erreur de Sérialisation des Fonctions

**Erreur** :
```
Captured variable in the closure can not be serialized because it's a function named "X". 
You might need to convert it to a QRL using $(fn)
```

**Cause** :
- Qwik nécessite que toutes les fonctions utilisées dans les composants soient sérialisables
- Les fonctions normales ne peuvent pas être sérialisées automatiquement

**Solution** :
1. Importer `$` depuis Qwik :
```typescript
import { $ } from '@builder.io/qwik';
```

2. Wrapper la fonction avec `$()` :
```typescript
// ❌ Ne pas faire
const maFonction = () => { /* ... */ };

// ✅ Faire
const maFonction = $(async () => { /* ... */ });
```

### 2. Erreur de Handler WebSocket

**Erreur** :
```
TypeError: handlers.onError$ is not a function
```

**Cause** :
- Les handlers WebSocket dans Qwik doivent être des QRL
- L'utilisation de `.value` sur un signal contenant une fonction ne fonctionne pas correctement avec les WebSockets

**Solution** :
1. Définir les handlers comme des QRL :
```typescript
// ❌ Ne pas faire
const handleError = useSignal((error) => { /* ... */ });

// ✅ Faire
const handleError = $(async (error) => { /* ... */ });
```

2. Passer les handlers directement :
```typescript
// ❌ Ne pas faire
websocketService.connect({
  onError: handleError.value
});

// ✅ Faire
websocketService.connect({
  onError$: handleError
});
```

### 3. Erreur d'Accès aux Propriétés Undefined

**Erreur** :
```
Cannot read properties of undefined (reading 'X')
```

**Cause** :
- Tentative d'accès à une propriété d'un objet qui n'est pas encore initialisé
- Problème courant avec les services et les états asynchrones

**Solution** :
1. Ajouter des vérifications de type :
```typescript
// ❌ Ne pas faire
if (data.type === 'state') { /* ... */ }

// ✅ Faire
if (data && typeof data === 'object' && 'type' in data) {
  const message = data as WebSocketMessage;
  if (message.type === 'state') { /* ... */ }
}
```

2. Vérifier l'état des services avant utilisation :
```typescript
// ❌ Ne pas faire
websocketService.send(message);

// ✅ Faire
const ensureWebSocketConnection = $(async () => {
  if (!websocketService.isConnected()) {
    await websocketService.connect(/* ... */);
  }
});

// Puis utiliser
await ensureWebSocketConnection();
websocketService.send(message);
```

## Bonnes Pratiques

1. **Toujours utiliser `$`** pour les fonctions dans les composants Qwik
2. **Vérifier l'état des services** avant de les utiliser
3. **Typer correctement les données** avec TypeScript
4. **Gérer les cas d'erreur** de manière explicite
5. **Utiliser des fonctions utilitaires** pour les opérations communes

## Debugging

Pour un meilleur debugging :

1. Ajouter des logs détaillés :
```typescript
console.log(' [useGame] WebSocket message:', data);
```

2. Utiliser try/catch avec des messages d'erreur explicites :
```typescript
try {
  // ...
} catch (error) {
  console.error(' [useGame] WebSocket error:', error);
  throw error;
}
```

3. Vérifier la console du navigateur pour les erreurs de sérialisation Qwik
