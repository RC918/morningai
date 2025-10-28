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
        "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",
        interactive && "card-hover cursor-pointer",
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
      className={cn("leading-none font-semibold", className)}
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
      className={cn("text-muted-foreground text-sm", className)}
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
