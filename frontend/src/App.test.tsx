import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
    it('renders login page by default', () => {
        render(<App />);
        expect(screen.getByText(/SyncVault AI/i)).toBeInTheDocument();
        expect(screen.getByText(/Login to your store/i)).toBeInTheDocument();
    });
});
