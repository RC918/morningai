import * as React from "react";

import { cn, getInitials } from "../../utils";

interface AvatarStackItem {
  id: string;
  name: string;
  src?: string;
}

interface AvatarStackProps {
  avatars: AvatarStackItem[];
  max?: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeStyles = {
  sm: "h-6 w-6 text-[10px]",
  md: "h-8 w-8 text-xs",
  lg: "h-10 w-10 text-sm",
};

const overlapStyles = {
  sm: "-ml-2",
  md: "-ml-2.5",
  lg: "-ml-3",
};

function AvatarStack({
  avatars,
  max = 4,
  size = "md",
  className,
}: AvatarStackProps) {
  const visibleAvatars = avatars.slice(0, max);
  const remainingCount = avatars.length - max;

  return (
    <div className={cn("flex items-center", className)}>
      {visibleAvatars.map((avatar, index) => (
        <div
          key={avatar.id}
          className={cn(
            "relative rounded-full border-2 border-[var(--surface)] bg-[var(--neutral-100)]",
            sizeStyles[size],
            index > 0 && overlapStyles[size]
          )}
          title={avatar.name}
        >
          {avatar.src ? (
            <img
              src={avatar.src}
              alt={avatar.name}
              className="h-full w-full rounded-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center rounded-full bg-[var(--primary-100)] text-[var(--primary-700)] font-medium">
              {getInitials(avatar.name)}
            </div>
          )}
        </div>
      ))}
      {remainingCount > 0 && (
        <div
          className={cn(
            "relative flex items-center justify-center rounded-full border-2 border-[var(--surface)] bg-[var(--neutral-200)] text-[var(--text-secondary)] font-medium",
            sizeStyles[size],
            overlapStyles[size]
          )}
        >
          +{remainingCount}
        </div>
      )}
    </div>
  );
}

export { AvatarStack };
export type { AvatarStackProps, AvatarStackItem };
