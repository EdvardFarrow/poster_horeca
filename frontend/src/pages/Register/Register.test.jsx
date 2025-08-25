import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Register from './Register'

jest.mock('../../api/auth', () => ({
    register: jest.fn()
}))

import { register as mockRegister } from '../../api/auth'

const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate
}))

describe('Register Page', () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    test('рендерит форму регистрации', () => {
        render(<Register />, { wrapper: MemoryRouter })

        expect(screen.getByText(/Регистрация/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Логин/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Пароль/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Имя и Фамилия/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Зарегистрироваться/i })).toBeInTheDocument()
    })

    test('валидация fullname срабатывает', async () => {
        render(<Register />, { wrapper: MemoryRouter })

        const fullnameInput = screen.getByLabelText(/Имя и Фамилия/i)
        const submitBtn = screen.getByRole('button', { name: /Зарегистрироваться/i })

        fireEvent.change(fullnameInput, { target: { value: 'ivan' } })
        fireEvent.click(submitBtn)

        await waitFor(() => {
            expect(screen.getByText(/должны начинаться с заглавной буквы/i)).toBeInTheDocument()
        })
    })

    test('успешная регистрация вызывает navigate', async () => {
        mockRegister.mockResolvedValueOnce()


        render(<Register />, { wrapper: MemoryRouter })

        fireEvent.change(screen.getByLabelText(/Логин/i), { target: { value: 'testuser' } })
        fireEvent.change(screen.getByLabelText(/Пароль/i), { target: { value: '1234' } })
        fireEvent.change(screen.getByLabelText(/Имя и Фамилия/i), { target: { value: 'Ivan Ivanov' } })

        fireEvent.click(screen.getByRole('button', { name: /Зарегистрироваться/i }))

        await waitFor(() => {
            expect(mockRegister).toHaveBeenCalledWith({
                username: 'testuser',
                password: '1234',
                fullname: 'Ivan Ivanov',
                role: 'employee'
            })
            expect(mockNavigate).toHaveBeenCalledWith('/login')
        })
    })

    test('отображает ошибку при неуспешной регистрации', async () => {
        mockRegister.mockRejectedValueOnce({ response: { data: { detail: 'Пользователь уже существует' } } })

        render(<Register />, { wrapper: MemoryRouter })

        fireEvent.change(screen.getByLabelText(/Логин/i), { target: { value: 'existinguser' } })
        fireEvent.change(screen.getByLabelText(/Пароль/i), { target: { value: '1234' } })
        fireEvent.change(screen.getByLabelText(/Имя и Фамилия/i), { target: { value: 'Ivan Ivanov' } })

        fireEvent.click(screen.getByRole('button', { name: /Зарегистрироваться/i }))

        await waitFor(() => {
            expect(screen.getByText(/Пользователь уже существует/i)).toBeInTheDocument()
        })
    })
})
