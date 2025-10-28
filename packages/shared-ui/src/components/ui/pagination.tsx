import * as React from "react"
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  MoreHorizontalIcon,
} from "lucide-react"
import { useTranslation } from 'react-i18next'

import { cn } from "../../utils"
import { buttonVariants } from "./button";

interface PaginationProps extends React.ComponentPropsWithoutRef<"nav"> {
  className?: string;
}

function Pagination({
  className,
  ...props
}: PaginationProps) {
  return (
    <nav
      role="navigation"
      aria-label="pagination"
      data-slot="pagination"
      className={cn("mx-auto flex w-full justify-center", className)}
      {...props} />
  );
}

interface PaginationContentProps extends React.ComponentPropsWithoutRef<"ul"> {
  className?: string;
}

function PaginationContent({
  className,
  ...props
}: PaginationContentProps) {
  return (
    <ul
      data-slot="pagination-content"
      className={cn("flex flex-row items-center gap-1", className)}
      {...props} />
  );
}

interface PaginationItemProps extends React.ComponentPropsWithoutRef<"li"> {}

function PaginationItem({
  ...props
}: PaginationItemProps) {
  return <li data-slot="pagination-item" {...props} />;
}

interface PaginationLinkProps extends React.ComponentPropsWithoutRef<"a"> {
  className?: string;
  isActive?: boolean;
  size?: "default" | "sm" | "lg" | "icon";
}

function PaginationLink({
  className,
  isActive,
  size = "icon",
  ...props
}: PaginationLinkProps) {
  const { t } = useTranslation()
  return (
    <a
      aria-current={isActive ? "page" : undefined}
      data-slot="pagination-link"
      data-active={isActive}
      className={cn(buttonVariants({
        variant: isActive ? "outline" : "ghost",
        size,
      }), className)}
      aria-label={isActive ? t('feedback.currentPage') : t('feedback.goToPage')}
      {...props} />
  );
}

interface PaginationPreviousProps extends React.ComponentPropsWithoutRef<typeof PaginationLink> {
  className?: string;
}

function PaginationPrevious({
  className,
  ...props
}: PaginationPreviousProps) {
  return (
    <PaginationLink
      aria-label="Go to previous page"
      size="default"
      className={cn("gap-1 px-2.5 sm:pl-2.5", className)}
      {...props}>
      <ChevronLeftIcon />
      <span className="hidden sm:block">Previous</span>
    </PaginationLink>
  );
}

interface PaginationNextProps extends React.ComponentPropsWithoutRef<typeof PaginationLink> {
  className?: string;
}

function PaginationNext({
  className,
  ...props
}: PaginationNextProps) {
  return (
    <PaginationLink
      aria-label="Go to next page"
      size="default"
      className={cn("gap-1 px-2.5 sm:pr-2.5", className)}
      {...props}>
      <span className="hidden sm:block">Next</span>
      <ChevronRightIcon />
    </PaginationLink>
  );
}

interface PaginationEllipsisProps extends React.ComponentPropsWithoutRef<"span"> {
  className?: string;
}

function PaginationEllipsis({
  className,
  ...props
}: PaginationEllipsisProps) {
  return (
    <span
      aria-hidden
      data-slot="pagination-ellipsis"
      className={cn("flex size-9 items-center justify-center", className)}
      {...props}>
      <MoreHorizontalIcon className="size-4" />
      <span className="sr-only">More pages</span>
    </span>
  );
}

export {
  Pagination,
  PaginationContent,
  PaginationLink,
  PaginationItem,
  PaginationPrevious,
  PaginationNext,
  PaginationEllipsis,
}

export type {
  PaginationProps,
  PaginationContentProps,
  PaginationLinkProps,
  PaginationItemProps,
  PaginationPreviousProps,
  PaginationNextProps,
  PaginationEllipsisProps,
}
