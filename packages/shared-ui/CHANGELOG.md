# Changelog

All notable changes to `@morningai/shared-ui` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **TooltipContent**: Added `arrowClassName` prop to allow customization of the tooltip arrow styling. This enables consumers to override the default primary-colored arrow (e.g., for neutral-styled tooltips with white backgrounds). The prop is optional and backwards-compatible - when not provided, the arrow defaults to `bg-primary fill-primary`.

  ```tsx
  // Example: White tooltip with matching white arrow
  <TooltipContent
    className="bg-white text-neutral-900"
    arrowClassName="bg-white fill-white"
  >
    Tooltip text
  </TooltipContent>

  // Example: Dark mode responsive arrow
  <TooltipContent
    className="bg-white dark:bg-neutral-800"
    arrowClassName="bg-white fill-white dark:bg-neutral-800 dark:fill-neutral-800"
  >
    Tooltip text
  </TooltipContent>
  ```

- Added unit tests for `TooltipContent` component covering the new `arrowClassName` prop behavior.
