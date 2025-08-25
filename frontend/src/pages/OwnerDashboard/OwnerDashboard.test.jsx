import React from 'react';

import { render, screen } from '@testing-library/react';
import OwnerDashboard from './OwnerDashboard';

test('рендерит компонент', () => {
    render(<OwnerDashboard />);
    expect(screen.getByText(/В разработке/i)).toBeInTheDocument();
});