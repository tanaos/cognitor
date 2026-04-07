'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';

import styles from './Sidebar.module.css';


const nav = [
    { href: '/', label: 'Dashboard', icon: 'bi bi-speedometer2' },
    { href: '/inference-logs', label: 'Inference Logs', icon: 'bi bi-list-columns' },
    { href: '/inference-errors', label: 'Inference Errors', icon: 'bi bi-exclamation-triangle' },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className={styles.sidebar}>
            <div className={styles.brand}>
                <Link href='/' className={styles.brandLink}>
                    <Image src='/logo.png' alt='Tanaos logo' width={28} height={28} />
                    <span className={styles.brandName}>Cognitor by Tanaos</span>
                </Link>
            </div>
            <nav className={styles.nav}>
                {nav.map(({ href, label, icon }) => {
                    const active = pathname === href;
                    return (
                        <Link
                            key={href}
                            href={href}
                            className={`${styles.navLink} ${active ? styles.navLinkActive : ''}`}
                        >
                            <i className={icon} />
                            {label}
                        </Link>
                    );
                })}
            </nav>
        </aside>
    );
}
