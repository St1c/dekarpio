export function toBoolean(value: any) {
    const normalizedValue = String(value).toLowerCase();
    return normalizedValue === 'true';
}
