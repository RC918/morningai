declare const tokens: {
  readonly color: {
    readonly primary: Record<string, string>;
    readonly accent: {
      readonly purple: Record<string, string>;
      readonly orange: Record<string, string>;
    };
    readonly semantic: {
      readonly success: Record<string, string>;
      readonly error: Record<string, string>;
      readonly warning: Record<string, string>;
      readonly info: Record<string, string>;
    };
    readonly neutral: Record<string, string>;
    readonly background: {
      readonly base: string;
      readonly surface: string;
      readonly overlay: string;
    };
  };
  readonly font: {
    readonly family: Record<string, string>;
    readonly size: Record<string, string>;
    readonly lineHeight: Record<string, string>;
    readonly weight: Record<string, string>;
  };
  readonly space: Record<string, string>;
  readonly radius: Record<string, string>;
  readonly shadow: Record<string, string>;
  readonly animation: {
    readonly duration: Record<string, string>;
    readonly easing: Record<string, string>;
  };
  readonly breakpoint: Record<string, string>;
};

export default tokens;
