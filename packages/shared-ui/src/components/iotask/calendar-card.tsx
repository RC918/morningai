import * as React from "react";

import { cn } from "../../utils";

interface CalendarEvent {
  id: string;
  title: string;
  time: string;
  color?: "primary" | "success" | "warning" | "error" | "accent";
}

interface CalendarCardProps {
  title?: string;
  date: Date;
  events?: CalendarEvent[];
  onDateChange?: (date: Date) => void;
  className?: string;
}

const eventColorStyles = {
  primary: "border-l-[var(--primary-500)] bg-[var(--primary-50)]",
  success: "border-l-[var(--success-500)] bg-[var(--success-50)]",
  warning: "border-l-[var(--warning-500)] bg-[var(--warning-50)]",
  error: "border-l-[var(--error-500)] bg-[var(--error-50)]",
  accent: "border-l-[var(--color-accent-500)] bg-[var(--color-accent-50)]",
};

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

function CalendarCard({
  title = "Calendar",
  date,
  events = [],
  onDateChange,
  className,
}: CalendarCardProps) {
  const [currentMonth, setCurrentMonth] = React.useState(date);
  const [selectedDate, setSelectedDate] = React.useState(date);

  const firstDayOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
  const lastDayOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);
  const startingDayOfWeek = firstDayOfMonth.getDay();
  const daysInMonth = lastDayOfMonth.getDate();

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };

  const handleDateClick = (day: number) => {
    const newDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    setSelectedDate(newDate);
    onDateChange?.(newDate);
  };

  const isToday = (day: number) => {
    const today = new Date();
    return (
      day === today.getDate() &&
      currentMonth.getMonth() === today.getMonth() &&
      currentMonth.getFullYear() === today.getFullYear()
    );
  };

  const isSelected = (day: number) => {
    return (
      day === selectedDate.getDate() &&
      currentMonth.getMonth() === selectedDate.getMonth() &&
      currentMonth.getFullYear() === selectedDate.getFullYear()
    );
  };

  const days: (number | null)[] = [];
  for (let i = 0; i < startingDayOfWeek; i++) {
    days.push(null);
  }
  for (let i = 1; i <= daysInMonth; i++) {
    days.push(i);
  }

  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card",
        className
      )}
    >
      <div className="border-b border-[var(--border)] px-5 py-4">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          {title}
        </h2>
      </div>
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <button
            type="button"
            onClick={prevMonth}
            className="p-1 rounded hover:bg-[var(--neutral-100)] text-[var(--text-secondary)]"
            aria-label="Previous month"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <span className="text-sm font-medium text-[var(--text-primary)]">
            {MONTHS[currentMonth.getMonth()]} {currentMonth.getFullYear()}
          </span>
          <button
            type="button"
            onClick={nextMonth}
            className="p-1 rounded hover:bg-[var(--neutral-100)] text-[var(--text-secondary)]"
            aria-label="Next month"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <div className="grid grid-cols-7 gap-1 mb-2">
          {DAYS.map((day) => (
            <div
              key={day}
              className="text-center text-xs font-medium text-[var(--text-secondary)] py-1"
            >
              {day}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-1">
          {days.map((day, index) =>
            day === null ? (
              <div key={index} className="h-8 w-8" aria-hidden="true" />
            ) : (
              <button
                key={index}
                type="button"
                onClick={() => handleDateClick(day)}
                aria-label={`${MONTHS[currentMonth.getMonth()]} ${day}, ${currentMonth.getFullYear()}${isToday(day) ? " (today)" : ""}${isSelected(day) ? " (selected)" : ""}`}
                aria-pressed={isSelected(day)}
                className={cn(
                  "h-8 w-8 rounded-full text-xs transition-colors hover:bg-[var(--neutral-100)]",
                  isToday(day) && !isSelected(day) && "bg-[var(--primary-50)] text-[var(--primary-600)]",
                  isSelected(day) && "bg-[var(--primary-500)] text-white",
                  !isToday(day) && !isSelected(day) && "text-[var(--text-primary)]"
                )}
              >
                {day}
              </button>
            )
          )}
        </div>

        {events.length > 0 && (
          <div className="mt-4 space-y-2">
            <h3 className="text-xs font-medium text-[var(--text-secondary)] uppercase">
              Events
            </h3>
            {events.map((event) => (
              <div
                key={event.id}
                className={cn(
                  "rounded-md border-l-2 px-3 py-2",
                  eventColorStyles[event.color || "primary"]
                )}
              >
                <p className="text-sm font-medium text-[var(--text-primary)]">
                  {event.title}
                </p>
                <p className="text-xs text-[var(--text-secondary)]">{event.time}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export { CalendarCard };
export type { CalendarCardProps, CalendarEvent };
