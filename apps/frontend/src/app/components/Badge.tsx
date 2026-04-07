import styles from './Badge.module.css';


export default function Badge({ label, variant = 'default' }: {
    label: string;
    variant?: 'default' | 'danger' | 'warning' | 'success';
}) {
    return (
        <span className={`${styles.badge} ${styles[variant]}`}>
            {label}
        </span>
    );
}
