import type { ReactNode } from 'react';

import styles from './FilterBar.module.css';


export default function FilterBar({
    children,
    justify,
}: {
    children: ReactNode;
    justify?: string;
}) {
    return (
        <div className={`${styles.bar}`} style={justify ? { justifyContent: justify } : undefined}>
            {children}
        </div>
    );
}
