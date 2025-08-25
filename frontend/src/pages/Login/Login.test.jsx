import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Login from './Login'

const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
}))

jest.mock('../../api/auth', () => ({
    login: jest.fn(),
    getUserInfo: jest.fn()    
}))

import { login as mockLogin, getUserInfo as mockGetUserInfo } from '../../api/auth'



describe('Login Page', () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    test('рендерит форму входа', () => {
        render(<Login />, { wrapper: MemoryRouter })
        expect(screen.getByText(/Вход/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Логин/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Пароль/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Войти/i })).toBeInTheDocument()
        expect(screen.getByText(/Зарегистрироваться/i)).toBeInTheDocument()
    })

    test('отображает ошибку при неверных данных', async () => {
        mockLogin.mockRejectedValueOnce(new Error('fail'))
        render(<Login />, { wrapper: MemoryRouter })

        fireEvent.change(screen.getByLabelText(/Логин/i), { target: { value: 'testuser' } })
        fireEvent.change(screen.getByLabelText(/Пароль/i), { target: { value: '1234' } })

        fireEvent.click(screen.getByRole('button', { name: /Войти/i }))

        await waitFor(() => {
            expect(screen.getByText(/Неверный логин или пароль/i)).toBeInTheDocument()
        })
    })

    test('успешный логин вызывает редирект по роли', async () => {
        mockLogin.mockResolvedValueOnce()
        mockGetUserInfo.mockResolvedValueOnce({ role: 'employee' })

        

        render(<Login />, { wrapper: MemoryRouter })

        fireEvent.change(screen.getByLabelText(/Логин/i), { target: { value: 'testuser' } })
        fireEvent.change(screen.getByLabelText(/Пароль/i), { target: { value: '1234' } })

        fireEvent.click(screen.getByRole('button', { name: /Войти/i }))

        await waitFor(() => {
            expect(mockNavigate).toHaveBeenCalledWith('/employee')
        })
    })
})
