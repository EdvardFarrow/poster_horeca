import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

import EmployeeDashboard from '../EmployeeDashboard/EmployeeDashboard'

test('рендерит компонент', () => {
    render(<EmployeeDashboard />)
    expect(screen.getByText(/Employee Dashboard/i)).toBeInTheDocument()
})