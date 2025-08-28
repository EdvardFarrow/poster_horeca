import { useState, useEffect } from "react";
import Calendar from "react-calendar";
import 'react-calendar/dist/Calendar.css';
import axios from "axios";

export default function EmployeeCalendar({ onSelectDate }) {
    const [myShifts, setMyShifts] = useState([]);
    const [today, setToday] = useState(new Date());

    useEffect(() => {
        axios.get("/api/salary/records/current/").then(res => {
        const shifts = res.data.shifts.map(s => ({
            date: new Date(s.date),
            role: s.role,
            status: s.status
        }));
        setMyShifts(shifts);
        });
    }, []);

    const tileClassName = ({ date, view }) => {
        if (view === 'month') {
        const shift = myShifts.find(d =>
            d.date.getFullYear() === date.getFullYear() &&
            d.date.getMonth() === date.getMonth() &&
            d.date.getDate() === date.getDate()
        );
        if (!shift) return '';

        if (shift.date >= today) return 'bg-green-200 rounded';
        if (shift.date < today) return 'bg-gray-200 text-gray-500 rounded';
        return '';
        }
        return '';
    };

    const tileContent = ({ date, view }) => {
        if (view === 'month') {
        const shift = myShifts.find(d =>
            d.date.getFullYear() === date.getFullYear() &&
            d.date.getMonth() === date.getMonth() &&
            d.date.getDate() === date.getDate()
        );
        if (shift) return <div className="text-xs">{shift.role}</div>;
        }
        return null;
    };

    return (
        <div className="max-w-md mx-auto">
        <Calendar
            onClickDay={(value) => {
            const clickedDate = value.toISOString().split('T')[0];
            const isFutureShift = myShifts.some(d =>
                d.date.toISOString().split('T')[0] === clickedDate &&
                d.date >= today
            );
            if (isFutureShift) onSelectDate(clickedDate);
            }}
            tileClassName={tileClassName}
            tileContent={tileContent}
        />
        <p className="text-sm mt-2 text-gray-600">
            Зелёным — будущие смены, серым — прошедшие. Роль указана внутри даты.
        </p>
        </div>
    );
}
