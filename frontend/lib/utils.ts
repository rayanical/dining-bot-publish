/**
 * UI Utility Functions.
 *
 * Helper functions for handling class names and Tailwind CSS merging.
 *
 * @module lib/utils
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge and de-duplicate Tailwind/clsx class names.
 *
 * Combines standard `clsx` logic (conditionals, arrays, objects) with 
 * `tailwind-merge` to resolve conflicting Tailwind utility classes properly.
 *
 * @param {...ClassValue[]} inputs - One or more class name values.
 * @returns {string} A single space-delimited string with merged Tailwind classes.
 */
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}