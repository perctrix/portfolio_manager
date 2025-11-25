import React from 'react';

export function SkeletonCard() {
    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 animate-pulse">
            <div className="h-4 w-24 bg-gray-200 rounded mb-3"></div>
            <div className="h-8 w-32 bg-gray-200 rounded"></div>
        </div>
    );
}
