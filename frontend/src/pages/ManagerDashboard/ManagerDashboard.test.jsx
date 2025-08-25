import React from 'react';
import { render, screen } from '@testing-library/react';
import ManagerDashboard from './ManagerDashboard'; 

test('рендерит компонент', () => {
    render(<ManagerDashboard />);
    expect(screen.getByText(/Manager Dashboard/i)).toBeInTheDocument();
});