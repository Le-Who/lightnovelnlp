import { describe, it, expect } from 'vitest';
import { cn } from '@/lib/utils';

describe('cn utility', () => {
    it('merges class names correctly', () => {
        expect(cn('class1', 'class2')).toBe('class1 class2');
    });

    it('handles conditional classes', () => {
        expect(cn('class1', true && 'class2', false && 'class3')).toBe('class1 class2');
    });

    it('handles arrays of classes', () => {
        expect(cn(['class1', 'class2'])).toBe('class1 class2');
    });

    it('merges Tailwind classes correctly', () => {
        expect(cn('px-2 py-1', 'p-4')).toBe('p-4');
        expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
    });

    it('handles complex combinations', () => {
        expect(cn('base-class', { 'active': true, 'disabled': false }, ['extra-class'])).toBe('base-class active extra-class');
    });

    it('handles empty inputs', () => {
        expect(cn()).toBe('');
        expect(cn(null)).toBe('');
        expect(cn(undefined)).toBe('');
    });
});
