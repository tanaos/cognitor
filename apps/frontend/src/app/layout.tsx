import type { Metadata } from 'next';

import './globals.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import Sidebar from './components/Sidebar';


export const metadata: Metadata = {
    title: 'Tanaos SLM Observability Platform',
    description: 'Observability, evaluation and optimization platform for Small Language Models.',
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang='en'>
            <head>
                <link
                    href='https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap'
                    rel='stylesheet'
                />
            </head>
            <body>
                <Sidebar />
                <main className='main-content'>
                    {children}
                </main>
            </body>
        </html>
    );
}
