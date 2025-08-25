import React from 'react';
import { render, screen } from '@testing-library/react';
import EmployeeDashboard from './EmployeeDashboard'; 

test('рендерит компонент', () => {
    render(<EmployeeDashboard />);
    expect(screen.getByText(/Employee Dashboard/i)).toBeInTheDocument();
});