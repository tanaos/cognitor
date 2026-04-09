/**
 * Formats a timestamp string into "YYYY-MM-DD HH:MM:SS".
 * Accepts ISO strings, space-separated datetime strings, or any value
 * parseable by Date. Returns '—' for null/undefined/invalid values.
 */
export function formatTimestamp(value: string | null | undefined): string {
    if (!value) return '—';
    const d = new Date(value);
    if (isNaN(d.getTime())) return value;
    const pad = (n: number) => String(n).padStart(2, '0');
    return (
        `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
        `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
    );
}
