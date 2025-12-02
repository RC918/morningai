import * as React from "react"

import { cn } from "../../utils"

interface CardProps extends React.ComponentPropsWithoutRef<'div'> {
  className?: string;
  interactive?: boolean;
}

function Card({
  className,
  interactive = false,
  ...props
}: CardProps) {
  return (
    <div
      data-slot="card"
      className={cn(
        "bg-white text-neutral-900 flex flex-col gap-4 rounded-xl border border-neutral-200 py-5 shadow-sm font-['Public_Sans',sans-serif] dark:bg-neutral-800 dark:text-neutral-100 dark:border-neutral-700",
        interactive && "card-hover cursor-pointer hover:shadow-md hover:border-primary-200 transition-all",
        className
      )}
      {...props} />
  );
}

interface CardHeaderProps extends React.ComponentPropsWithoutRef<'div'> {
  className?: string;
}

function CardHeader({
  className,
  ...props
}: CardHeaderProps) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-1.5 px-6 has-data-[slot=card-action]:grid-cols-[1fr_auto] [.border-b]:pb-6",
        className
      )}
      {...props} />
  );
}

interface CardTitleProps extends React.ComponentPropsWithoutRef<'div'> {
  className?: string;
}

function CardTitle({
  className,
  ...props
}: CardTitleProps) {
  return (
    <div
      data-slot="card-title"
      className={cn("leading-none font-semibold text-neutral-900 dark:text-neutral-100", className)}
      {...props} />
  );
}

interface CardDescriptionProps extends React.ComponentPropsWithoutRef<'div'> {
  className?: string;
}

function CardDescription({
  className,
  ...props
}: CardDescriptionProps) {
  return (
    <div
      data-slot="card-description"
      className={cn("text-neutral-500 text-sm dark:text-neutral-400", className)}
      {...props} />
  );
}

interface CardActionProps extends React.ComponentPropsWithoutRef<'div'> {
  className?: string;
}

function CardAction({
  className,
  ...props
}: CardActionProps) {
  return (
    <div
      data-slot="card-action"
      className={cn(
        "col-start-2 row-span-2 row-start-1 self-start justify-self-end",
        className
      )}
      {...props} />
  );
}

interface CardContentProps extends React.ComponentPropsWithoutRef<'div'> {
  className?: string;
}

function CardContent({
  className,
  ...props
}: CardContentProps) {
  return (<div data-slot="card-content" className={cn("px-6", className)} {...props} />);
}

interface CardFooterProps extends React.ComponentPropsWithoutRef<'div'> {
  className?: string;
}

function CardFooter({
  className,
  ...props
}: CardFooterProps) {
  return (
    <div
      data-slot="card-footer"
      className={cn("flex items-center px-6 [.border-t]:pt-6", className)}
      {...props} />
  );
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
}

export type {
  CardProps,
  CardHeaderProps,
  CardFooterProps,
  CardTitleProps,
  CardActionProps,
  CardDescriptionProps,
  CardContentProps,
}
