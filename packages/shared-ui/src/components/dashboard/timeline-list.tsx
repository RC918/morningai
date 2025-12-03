import * as React from "react";

import { cn } from "../../utils";

interface TimelineItem {
  id: string;
  title: string;
  desc: string;
  time: string;
}

interface TimelineListProps {
  items: TimelineItem[];
  className?: string;
}

function TimelineList({ items, className }: TimelineListProps) {
  return (
    <ul className={cn("space-y-4 text-sm", className)}>
      {items.map((item) => (
        <li key={item.id} className="flex justify-between">
          <div>
            <div className="font-medium text-neutral-900 dark:text-neutral-100">
              {item.title}
            </div>
            <div className="text-xs text-neutral-500 dark:text-neutral-400">
              {item.desc}
            </div>
          </div>
          <span className="text-xs text-neutral-500 dark:text-neutral-400">
            {item.time}
          </span>
        </li>
      ))}
    </ul>
  );
}

export { TimelineList };
export type { TimelineListProps, TimelineItem };
