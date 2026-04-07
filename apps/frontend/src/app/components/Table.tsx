import styles from './Table.module.css';


export default function Table({ columns, rows }: {
    columns: string[];
    rows: (string | number | React.ReactNode)[][];
}) {
    return (
        <div className={styles.wrapper}>
            <table className={styles.table}>
                <thead>
                    <tr className={styles.headRow}>
                        {columns.map((col) => (
                            <th key={col} className={styles.headCell}>
                                {col}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, i) => (
                        <tr key={i} className={styles.row}>
                            {row.map((cell, j) => (
                                <td key={j} className={styles.cell}>
                                    {cell}
                                </td>
                            ))}
                        </tr>
                    ))}
                    {rows.length === 0 && (
                        <tr>
                            <td colSpan={columns.length} className={styles.empty}>
                                No entries found.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
