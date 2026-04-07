import styles from './StatCard.module.css';


export default function StatCard({ label, value, sub }: {
    label: string;
    value: string | number;
    sub?: string;
}) {
    return (
        <div className={styles.card}>
            <span className={styles.label}>{label}</span>
            <span className={styles.value}>{value}</span>
            {sub && <span className={styles.sub}>{sub}</span>}
        </div>
    );
}
