import type { MetadataRoute } from 'next';


export default function manifest(): MetadataRoute.Manifest {
    return {
        name: 'Cognitor — Log Viewer',
        short_name: 'Cognitor',
        description: 'SLM Observability Platform',
        start_url: '/',
        display: 'standalone',
        background_color: '#ffffff',
        theme_color: '#FF3668',
        icons: [
            {
                src: '/logo.png',
                sizes: 'any',
                type: 'image/png',
            },
        ],
    };
}
