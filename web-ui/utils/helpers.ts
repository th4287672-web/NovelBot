export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  if (typeof structuredClone === 'function') {
      try {
          return structuredClone(obj);
      } catch (e) {
      }
  }
  return JSON.parse(JSON.stringify(obj));
}