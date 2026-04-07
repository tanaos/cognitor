'use client';

import ClipLoader from 'react-spinners/ClipLoader';


export default function Spinner({ size = 40 }: { size?: number }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '4rem 0' }}>
            <ClipLoader color='black' size={size} />
        </div>
    );
}
